#!/usr/bin/env python
"""
Orthanc DICOM 업로드 및 OCS 동기화 스크립트

이 스크립트는:
1. 환자데이터 폴더의 MRI를 Orthanc에 업로드
2. OCS RIS 레코드의 worker_result를 Orthanc 정보로 업데이트
3. Orthanc/DICOM 데이터가 있는 OCS → CONFIRMED, 없으면 → ACCEPTED

※ CT/PET OCS는 setup_dummy_data_*.py에서 생성하지 않음 (MRI만 생성)

사용법:
    python setup_dummy_data/sync_orthanc_ocs.py
    python setup_dummy_data/sync_orthanc_ocs.py --dry-run  # 테스트 모드
    python setup_dummy_data/sync_orthanc_ocs.py --skip-upload  # 업로드 스킵 (OCS만 업데이트)
"""

import os
import sys
import json
import argparse
import uuid
from pathlib import Path
from datetime import datetime
import requests

# 프로젝트 루트 디렉토리로 이동 (상위 폴더)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Django 설정
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from django.db import transaction
from apps.ocs.models import OCS
from apps.patients.models import Patient


# ============================================================
# 설정
# ============================================================

ORTHANC_URL = "http://localhost:8042"
PATIENT_DATA_PATH = Path("c:/0000/환자데이터")

# 환자 폴더 목록 (순서대로)
PATIENT_FOLDERS = [
    "TCGA-CS-4944",
    "TCGA-CS-6666",
    "TCGA-DU-5855",
    "TCGA-DU-5874",
    "TCGA-DU-7014",
    "TCGA-DU-7015",
    "TCGA-DU-7018",
    "TCGA-DU-7300",
    "TCGA-DU-A5TW",
    "TCGA-DU-A5TY",
    "TCGA-FG-7634",
    "TCGA-HT-7473",
    "TCGA-HT-7602",
    "TCGA-HT-7686",
    "TCGA-HT-7694",
]

# MRI 시리즈 타입 매핑
SERIES_TYPE_MAP = {
    "t1": "T1",
    "t2": "T2",
    "t1ce": "T1C",
    "flair": "FLAIR",
    "seg": "SEG",
}


# ============================================================
# Orthanc API 헬퍼
# ============================================================

def orthanc_get(path):
    """Orthanc GET 요청"""
    r = requests.get(f"{ORTHANC_URL}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def orthanc_post_dicom(dicom_bytes):
    """DICOM 파일 업로드"""
    r = requests.post(
        f"{ORTHANC_URL}/instances",
        data=dicom_bytes,
        headers={"Content-Type": "application/dicom"},
        timeout=60
    )
    r.raise_for_status()
    return r.json()


def orthanc_delete(path):
    """Orthanc DELETE 요청"""
    r = requests.delete(f"{ORTHANC_URL}{path}", timeout=30)
    r.raise_for_status()
    return r.json() if r.text else {}


# ============================================================
# DICOM 업로드
# ============================================================

def upload_patient_mri(patient_folder_name, patient_number, ocs_id, dry_run=False):
    """
    환자 MRI 폴더를 Orthanc에 업로드

    Args:
        patient_folder_name: TCGA-CS-4944
        patient_number: P202600001
        ocs_id: ocs_0001
        dry_run: True면 실제 업로드 안 함

    Returns:
        orthanc_info dict 또는 None
    """
    import pydicom
    from pydicom.uid import generate_uid

    mri_path = PATIENT_DATA_PATH / patient_folder_name / "mri"

    if not mri_path.exists():
        print(f"  [ERROR] MRI 폴더 없음: {mri_path}")
        return None

    # 시리즈 폴더 확인
    series_folders = [f for f in mri_path.iterdir() if f.is_dir()]
    if not series_folders:
        print(f"  [ERROR] 시리즈 폴더 없음: {mri_path}")
        return None

    # StudyInstanceUID 생성 (DICOM UI VR 규격: 숫자와 점만)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # ocs_id에서 숫자만 추출
    ocs_num = ''.join(filter(str.isdigit, ocs_id))
    patient_num = ''.join(filter(str.isdigit, patient_number))
    study_uid = f"1.2.410.200001.{ocs_num}.{patient_num}.{timestamp}"
    study_id = uuid.uuid4().hex[:16]  # SH VR 최대 16자

    now = datetime.now()
    study_date = now.strftime("%Y%m%d")
    study_time = now.strftime("%H%M%S")

    print(f"  StudyUID: {study_uid}")
    print(f"  시리즈: {[f.name for f in series_folders]}")

    if dry_run:
        print(f"  [DRY-RUN] 업로드 스킵")
        return {
            "patient_id": patient_number,
            "orthanc_study_id": "dry-run-study-id",
            "study_id": study_id,
            "study_uid": study_uid,
            "uploaded_at": timezone.now().isoformat() + "Z",
            "series": [
                {
                    "orthanc_id": f"dry-run-{folder.name}",
                    "series_uid": f"1.2.3.{i}",
                    "series_type": SERIES_TYPE_MAP.get(folder.name, "OTHER"),
                    "description": folder.name,
                    "instances_count": len(list(folder.glob("*.dcm")))
                }
                for i, folder in enumerate(series_folders, 1)
            ]
        }

    # 실제 업로드
    uploaded_series = {}  # series_name -> orthanc_series_id
    series_uid_map = {}   # series_name -> series_uid
    series_num = 1

    for series_folder in sorted(series_folders):
        series_name = series_folder.name
        series_uid = generate_uid()
        series_uid_map[series_name] = series_uid

        dcm_files = sorted(series_folder.glob("*.dcm"))
        print(f"    {series_name}: {len(dcm_files)} files", end="")

        for dcm_file in dcm_files:
            try:
                ds = pydicom.dcmread(str(dcm_file), force=True)

                # DICOM 태그 수정
                ds.PatientID = patient_number
                ds.PatientName = patient_number
                ds.StudyInstanceUID = study_uid
                ds.StudyID = study_id
                ds.StudyDescription = f"Brain MRI - {ocs_id}"
                ds.StudyDate = study_date
                ds.StudyTime = study_time
                ds.SeriesInstanceUID = series_uid
                ds.SeriesNumber = series_num
                ds.SeriesDescription = series_name

                # 메모리에 저장
                import io
                bio = io.BytesIO()
                ds.save_as(bio)
                bio.seek(0)

                # 업로드
                result = orthanc_post_dicom(bio.getvalue())

                if result.get("ParentSeries"):
                    uploaded_series[series_name] = result["ParentSeries"]

            except Exception as e:
                print(f"\n    [ERROR] {dcm_file.name}: {e}")

        series_num += 1
        print(" [OK]")

    # Orthanc Study ID 조회
    orthanc_study_id = None
    if uploaded_series:
        first_series_id = list(uploaded_series.values())[0]
        try:
            series_info = orthanc_get(f"/series/{first_series_id}")
            orthanc_study_id = series_info.get("ParentStudy")
        except Exception as e:
            print(f"  [WARNING] Study ID 조회 실패: {e}")

    # 결과 구성
    series_list = []
    for series_name, orthanc_series_id in uploaded_series.items():
        try:
            series_info = orthanc_get(f"/series/{orthanc_series_id}")
            instances_count = len(series_info.get("Instances", []))
        except:
            instances_count = 0

        series_list.append({
            "orthanc_id": orthanc_series_id,
            "series_uid": series_uid_map.get(series_name, ""),
            "series_type": SERIES_TYPE_MAP.get(series_name, "OTHER"),
            "description": series_name,
            "instances_count": instances_count
        })

    return {
        "patient_id": patient_number,
        "orthanc_study_id": orthanc_study_id,
        "study_id": study_id,
        "study_uid": study_uid,
        "uploaded_at": timezone.now().isoformat() + "Z",
        "series": series_list
    }


# ============================================================
# OCS 업데이트
# ============================================================

def update_ocs_worker_result(ocs, orthanc_info, is_confirmed=True, dry_run=False):
    """
    OCS worker_result 업데이트

    Args:
        ocs: OCS 모델 인스턴스
        orthanc_info: Orthanc 업로드 결과
        is_confirmed: CONFIRMED 상태로 설정할지 여부
        dry_run: True면 실제 업데이트 안 함
    """
    timestamp = timezone.now().isoformat() + "Z"

    # 전체 instances 수 계산
    total_instances = sum(s.get("instances_count", 0) for s in orthanc_info.get("series", []))

    worker_result = {
        "_template": "RIS",
        "_version": "1.2",
        "_confirmed": is_confirmed,
        "_verifiedAt": timestamp if is_confirmed else None,
        "_verifiedBy": "시스템관리자" if is_confirmed else None,

        "orthanc": orthanc_info,

        "dicom": {
            "study_uid": orthanc_info.get("study_uid", ""),
            "series_count": len(orthanc_info.get("series", [])),
            "instance_count": total_instances
        },

        "findings": "뇌 MRI 검사 결과, 종양 소견이 관찰됩니다." if is_confirmed else "",
        "impression": "뇌종양 의심, 추가 검사 필요" if is_confirmed else "",
        "recommendation": "신경외과 협진 권고" if is_confirmed else "",

        "tumorDetected": True if is_confirmed else None,
        "imageResults": [],
        "files": [],
        "_custom": {}
    }

    if dry_run:
        print(f"    [DRY-RUN] worker_result 업데이트 스킵")
        return

    # 실제 업데이트
    ocs.worker_result = worker_result

    if is_confirmed:
        ocs.ocs_status = OCS.OcsStatus.CONFIRMED
        ocs.confirmed_at = timezone.now()
        ocs.ocs_result = True
    else:
        ocs.ocs_status = OCS.OcsStatus.ACCEPTED
        ocs.accepted_at = timezone.now()

    ocs.save()


# ============================================================
# 메인 로직
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Orthanc DICOM 업로드 및 OCS 동기화')
    parser.add_argument('--dry-run', action='store_true', help='테스트 모드 (실제 업로드/업데이트 안 함)')
    parser.add_argument('--skip-upload', action='store_true', help='Orthanc 업로드 스킵 (OCS만 업데이트)')
    parser.add_argument('--limit', type=int, default=0, help='처리할 환자 수 제한 (0=전체)')
    args = parser.parse_args()

    print("=" * 60)
    print("Orthanc DICOM 업로드 및 OCS 동기화")
    print("=" * 60)

    if args.dry_run:
        print("[MODE] DRY-RUN - 실제 변경 없음")

    # 1. 환자 목록 조회
    print("\n[1단계] 환자 목록 조회...")
    patients = list(Patient.objects.filter(is_deleted=False).order_by('patient_number')[:16])
    print(f"  DB 환자: {len(patients)}명")

    if len(patients) < 15:
        print(f"  [ERROR] 환자가 15명 미만입니다. 더미 데이터를 먼저 생성하세요.")
        return

    # 2. OCS RIS 목록 조회
    print("\n[2단계] OCS RIS 목록 조회...")
    ocs_ris_list = list(OCS.objects.filter(job_role='RIS', job_type='MRI', is_deleted=False).order_by('id'))
    print(f"  OCS RIS: {len(ocs_ris_list)}건")

    if len(ocs_ris_list) < 16:
        print(f"  [WARNING] OCS RIS가 16건 미만입니다. 가능한 만큼만 처리합니다.")

    # 3. 환자 폴더와 매핑
    print("\n[3단계] 환자-폴더 매핑...")

    # 기존 업로드된 환자 확인 (ocs_0107 = P202600032)
    existing_patient = "P202600032"
    existing_folder = None  # 기존 폴더는 스킵

    mappings = []
    folder_idx = 0
    patient_idx = 0

    # 처리 제한
    limit = args.limit if args.limit > 0 else len(PATIENT_FOLDERS)

    while folder_idx < len(PATIENT_FOLDERS) and len(mappings) < limit:
        folder_name = PATIENT_FOLDERS[folder_idx]

        # 해당 순서의 환자
        if patient_idx < len(patients):
            patient = patients[patient_idx]

            # 해당 순서의 OCS
            ocs = ocs_ris_list[patient_idx] if patient_idx < len(ocs_ris_list) else None

            mappings.append({
                "folder": folder_name,
                "patient": patient,
                "patient_number": patient.patient_number,
                "ocs": ocs,
                "ocs_id": ocs.ocs_id if ocs else None,
            })

        folder_idx += 1
        patient_idx += 1

    print(f"  매핑 완료: {len(mappings)}건")

    for m in mappings[:5]:
        print(f"    {m['folder']} -> {m['patient_number']} -> {m['ocs_id']}")
    if len(mappings) > 5:
        print(f"    ... 외 {len(mappings) - 5}건")

    # 4. Orthanc 업로드
    print("\n[4단계] Orthanc 업로드...")

    upload_results = []

    for i, mapping in enumerate(mappings):
        folder = mapping["folder"]
        patient_number = mapping["patient_number"]
        ocs_id = mapping["ocs_id"] or f"ocs_new_{i+1:04d}"

        print(f"\n[{i+1}/{len(mappings)}] {folder} -> {patient_number}")

        if args.skip_upload:
            print(f"  [SKIP] 업로드 스킵 (--skip-upload)")
            orthanc_info = None
        else:
            orthanc_info = upload_patient_mri(folder, patient_number, ocs_id, dry_run=args.dry_run)

        upload_results.append({
            "mapping": mapping,
            "orthanc_info": orthanc_info
        })

    # 5. OCS 업데이트
    print("\n[5단계] OCS 업데이트...")

    # Orthanc/DICOM 데이터가 있으면 CONFIRMED, 없으면 ACCEPTED
    confirmed_count = 0

    for i, result in enumerate(upload_results):
        mapping = result["mapping"]
        orthanc_info = result["orthanc_info"]
        ocs = mapping["ocs"]

        if not ocs:
            print(f"  [{i+1}] {mapping['patient_number']}: OCS 없음, 스킵")
            continue

        # orthanc_info가 있으면 CONFIRMED, 없으면 ACCEPTED
        is_confirmed = orthanc_info is not None
        status = "CONFIRMED" if is_confirmed else "ACCEPTED"

        if is_confirmed:
            confirmed_count += 1

        print(f"  [{i+1}] {ocs.ocs_id} -> {status}")

        if orthanc_info:
            update_ocs_worker_result(ocs, orthanc_info, is_confirmed=True, dry_run=args.dry_run)
        else:
            # Orthanc 업로드 없이 ACCEPTED 상태로 변경
            if not args.dry_run:
                ocs.ocs_status = OCS.OcsStatus.ACCEPTED
                ocs.accepted_at = timezone.now()
                ocs.save()

    # 6. 나머지 OCS RIS MRI를 ACCEPTED로 변경
    print("\n[6단계] 나머지 OCS RIS MRI 상태 변경...")

    processed_ocs_ids = [m["ocs"].id for m in [r["mapping"] for r in upload_results] if m["ocs"]]

    # MRI만 대상으로 함 (CT, PET 제외)
    remaining_ocs = OCS.objects.filter(
        job_role='RIS',
        job_type='MRI',
        is_deleted=False
    ).exclude(
        id__in=processed_ocs_ids
    ).exclude(
        ocs_status__in=[OCS.OcsStatus.CONFIRMED, OCS.OcsStatus.CANCELLED]
    )

    remaining_count = remaining_ocs.count()
    print(f"  대상: {remaining_count}건 (MRI only)")

    if not args.dry_run and remaining_count > 0:
        updated = remaining_ocs.update(
            ocs_status=OCS.OcsStatus.ACCEPTED,
            accepted_at=timezone.now()
        )
        print(f"  업데이트 완료: {updated}건")
    elif args.dry_run:
        print(f"  [DRY-RUN] 업데이트 스킵")

    # 7. 요약
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)

    print(f"\n[요약]")
    print(f"  - 환자 폴더: {len(PATIENT_FOLDERS)}개")
    print(f"  - 업로드 처리: {len(upload_results)}건")
    print(f"  - CONFIRMED (DICOM 있음): {confirmed_count}건")
    print(f"  - 나머지 ACCEPTED (MRI): {remaining_count}건")

    # Orthanc 상태 확인
    try:
        studies = orthanc_get("/studies")
        print(f"  - Orthanc Studies: {len(studies)}개")
    except:
        pass

    # 최종 OCS RIS 상태
    print(f"\n[OCS RIS 최종 상태]")
    mri_total = OCS.objects.filter(job_role='RIS', job_type='MRI', is_deleted=False).count()
    mri_confirmed = OCS.objects.filter(job_role='RIS', job_type='MRI', ocs_status='CONFIRMED', is_deleted=False).count()
    mri_accepted = OCS.objects.filter(job_role='RIS', job_type='MRI', ocs_status='ACCEPTED', is_deleted=False).count()

    print(f"  - MRI 전체: {mri_total}건 (CONFIRMED: {mri_confirmed}, ACCEPTED: {mri_accepted})")


if __name__ == "__main__":
    main()
