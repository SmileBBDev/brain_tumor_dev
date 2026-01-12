#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (3) - 처방 데이터

이 스크립트는 처방 더미 데이터를 생성합니다:
- 처방전 (Prescription)
- 처방 항목 (PrescriptionItem)

사용법:
    python setup_dummy_data_3_prescriptions.py          # 기존 데이터 유지, 부족분만 추가
    python setup_dummy_data_3_prescriptions.py --reset  # 처방 데이터만 삭제 후 새로 생성
    python setup_dummy_data_3_prescriptions.py --force  # 목표 수량 이상이어도 강제 추가

선행 조건:
    python setup_database.py            (마이그레이션 및 기본 데이터)
    python setup_dummy_data_1_base.py   (기본 더미 데이터)
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import random
import argparse

# 프로젝트 루트 디렉토리로 이동 (상위 폴더)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Django 설정 (sys.path에 프로젝트 루트 추가)
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 초기화
import django
django.setup()

from django.utils import timezone
from django.db import transaction


def check_prerequisites():
    """선행 조건 확인"""
    print("\n[0단계] 선행 조건 확인...")

    from django.contrib.auth import get_user_model
    from apps.patients.models import Patient

    User = get_user_model()

    # 사용자 확인
    if not User.objects.exists():
        print("[ERROR] 사용자가 없습니다.")
        print("  먼저 실행하세요: python setup_database.py")
        return False

    # 환자 확인
    if not Patient.objects.filter(is_deleted=False).exists():
        print("[ERROR] 환자가 없습니다.")
        print("  먼저 실행하세요: python setup_dummy_data_1_base.py")
        return False

    print("[OK] 선행 조건 충족")
    return True


# 뇌종양 관련 약품 목록
MEDICATIONS = [
    # 항암제
    {"name": "Temozolomide 140mg", "code": "TEM140", "dosage": "140mg", "frequency": "QD", "route": "PO", "instructions": "공복에 복용, 구역질 시 제토제 병용"},
    {"name": "Temozolomide 250mg", "code": "TEM250", "dosage": "250mg", "frequency": "QD", "route": "PO", "instructions": "공복에 복용, 혈구 수치 모니터링 필요"},
    {"name": "Bevacizumab 400mg", "code": "BEV400", "dosage": "400mg", "frequency": "QW", "route": "IV", "instructions": "10mg/kg 기준, 30분 이상 점적"},
    {"name": "Lomustine 100mg", "code": "LOM100", "dosage": "100mg", "frequency": "QOD", "route": "PO", "instructions": "6주 주기, 혈액 검사 필수"},

    # 부종/뇌압 관리
    {"name": "Dexamethasone 4mg", "code": "DEX4", "dosage": "4mg", "frequency": "TID", "route": "PO", "instructions": "식후 복용, 점진적 감량 필요"},
    {"name": "Dexamethasone 8mg", "code": "DEX8", "dosage": "8mg", "frequency": "BID", "route": "IV", "instructions": "응급 시 사용, 점진적 경구 전환"},
    {"name": "Mannitol 20% 100ml", "code": "MAN100", "dosage": "100ml", "frequency": "QID", "route": "IV", "instructions": "뇌압 상승 시 15분 이상 점적"},

    # 항경련제
    {"name": "Levetiracetam 500mg", "code": "LEV500", "dosage": "500mg", "frequency": "BID", "route": "PO", "instructions": "식사와 무관, 갑작스런 중단 금지"},
    {"name": "Levetiracetam 1000mg", "code": "LEV1000", "dosage": "1000mg", "frequency": "BID", "route": "PO", "instructions": "고용량, 졸음 주의"},
    {"name": "Valproic acid 500mg", "code": "VPA500", "dosage": "500mg", "frequency": "TID", "route": "PO", "instructions": "간기능 검사 정기적 시행"},
    {"name": "Phenytoin 100mg", "code": "PHE100", "dosage": "100mg", "frequency": "TID", "route": "PO", "instructions": "혈중 농도 모니터링 필요"},

    # 진통제
    {"name": "Acetaminophen 500mg", "code": "ACE500", "dosage": "500mg", "frequency": "QID", "route": "PO", "instructions": "1일 4g 초과 금지"},
    {"name": "Tramadol 50mg", "code": "TRA50", "dosage": "50mg", "frequency": "TID", "route": "PO", "instructions": "졸음 유발 가능, 운전 주의"},
    {"name": "Oxycodone 10mg", "code": "OXY10", "dosage": "10mg", "frequency": "BID", "route": "PO", "instructions": "마약성 진통제, 변비 예방 필요"},

    # 구역/구토 관리
    {"name": "Ondansetron 8mg", "code": "OND8", "dosage": "8mg", "frequency": "BID", "route": "PO", "instructions": "항암 치료 30분 전 투여"},
    {"name": "Metoclopramide 10mg", "code": "MET10", "dosage": "10mg", "frequency": "TID", "route": "PO", "instructions": "식전 30분 복용"},

    # 위장 보호
    {"name": "Esomeprazole 40mg", "code": "ESO40", "dosage": "40mg", "frequency": "QD", "route": "PO", "instructions": "아침 식전 복용"},
    {"name": "Famotidine 20mg", "code": "FAM20", "dosage": "20mg", "frequency": "BID", "route": "PO", "instructions": "스테로이드 병용 시 필수"},

    # 기타 보조
    {"name": "Megestrol acetate 160mg", "code": "MEG160", "dosage": "160mg", "frequency": "QD", "route": "PO", "instructions": "식욕 부진 시 사용"},
    {"name": "Methylphenidate 10mg", "code": "MPH10", "dosage": "10mg", "frequency": "BID", "route": "PO", "instructions": "피로감 개선, 오후 투여 피함"},
]

# 진단명 목록
DIAGNOSES = [
    "뇌교종 (Glioma)",
    "교모세포종 (Glioblastoma, GBM)",
    "핍지교종 (Oligodendroglioma)",
    "수막종 (Meningioma)",
    "뇌전이암 (Brain Metastasis)",
    "뇌하수체선종 (Pituitary Adenoma)",
    "청신경초종 (Vestibular Schwannoma)",
    "두개인두종 (Craniopharyngioma)",
    "림프종 (Primary CNS Lymphoma)",
    "상의세포종 (Ependymoma)",
]


def create_dummy_prescriptions(num_prescriptions=20, num_items_per_rx=3, force=False):
    """더미 처방 데이터 생성"""
    print(f"\n[1단계] 처방 데이터 생성 (목표: 처방 {num_prescriptions}건, 항목 약 {num_prescriptions * num_items_per_rx}건)...")

    from apps.prescriptions.models import Prescription, PrescriptionItem
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = Prescription.objects.count()
    if existing_count >= num_prescriptions and not force:
        print(f"[SKIP] 이미 {existing_count}건의 처방이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    encounters = list(Encounter.objects.all())

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    statuses = [choice[0] for choice in Prescription.Status.choices]
    status_weights = [0.1, 0.5, 0.3, 0.1]  # DRAFT, ISSUED, DISPENSED, CANCELLED

    notes_list = [
        "다음 진료 시 반응 평가 예정",
        "부작용 발생 시 즉시 내원",
        "정기 혈액 검사 필요",
        "복용법 상세 설명 완료",
        "외래 2주 후 재방문 예정",
        "",
    ]

    prescription_count = 0
    item_count = 0

    for i in range(num_prescriptions):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters and random.random() < 0.7 else None
        status = random.choices(statuses, weights=status_weights)[0]
        diagnosis = random.choice(DIAGNOSES)

        days_ago = random.randint(0, 180)
        created_at_delta = timedelta(days=days_ago)

        # 타임스탬프 설정
        issued_at = None
        dispensed_at = None
        cancelled_at = None
        cancel_reason = None

        if status in ['ISSUED', 'DISPENSED']:
            issued_at = timezone.now() - created_at_delta + timedelta(hours=random.randint(1, 4))
        if status == 'DISPENSED':
            dispensed_at = issued_at + timedelta(hours=random.randint(1, 24)) if issued_at else None
        if status == 'CANCELLED':
            cancelled_at = timezone.now() - created_at_delta + timedelta(hours=random.randint(1, 8))
            cancel_reason = random.choice([
                "환자 요청으로 취소",
                "처방 내용 변경",
                "약물 상호작용 우려",
                "진단 변경",
            ])

        try:
            with transaction.atomic():
                prescription = Prescription.objects.create(
                    patient=patient,
                    doctor=doctor,
                    encounter=encounter,
                    status=status,
                    diagnosis=diagnosis,
                    notes=random.choice(notes_list),
                    issued_at=issued_at,
                    dispensed_at=dispensed_at,
                    cancelled_at=cancelled_at,
                    cancel_reason=cancel_reason,
                )

                # 처방 항목 생성 (1~5개)
                num_items = random.randint(1, 5)
                selected_meds = random.sample(MEDICATIONS, min(num_items, len(MEDICATIONS)))

                for order, med in enumerate(selected_meds):
                    duration = random.choice([7, 14, 28, 30, 60, 90])

                    # 빈도에 따른 수량 계산
                    freq_multiplier = {'QD': 1, 'BID': 2, 'TID': 3, 'QID': 4, 'PRN': 1, 'QOD': 0.5, 'QW': 0.14}
                    daily_count = freq_multiplier.get(med['frequency'], 1)
                    quantity = int(duration * daily_count) + random.randint(0, 5)

                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medication_name=med['name'],
                        medication_code=med['code'],
                        dosage=med['dosage'],
                        frequency=med['frequency'],
                        route=med['route'],
                        duration_days=duration,
                        quantity=quantity,
                        instructions=med['instructions'],
                        order=order,
                    )
                    item_count += 1

                prescription_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 처방 생성: {prescription_count}건")
    print(f"[OK] 처방 항목 생성: {item_count}건")
    print(f"  현재 전체 처방: {Prescription.objects.count()}건")
    print(f"  현재 전체 처방 항목: {PrescriptionItem.objects.count()}건")
    return True


def reset_prescription_data():
    """처방 데이터만 삭제"""
    print("\n[RESET] 처방 데이터 삭제 중...")

    from apps.prescriptions.models import Prescription, PrescriptionItem

    # 삭제 순서: 의존성 역순
    item_count = PrescriptionItem.objects.count()
    PrescriptionItem.objects.all().delete()
    print(f"  PrescriptionItem: {item_count}건 삭제")

    rx_count = Prescription.objects.count()
    Prescription.objects.all().delete()
    print(f"  Prescription: {rx_count}건 삭제")

    print("[OK] 처방 데이터 삭제 완료")


def print_summary():
    """처방 더미 데이터 요약"""
    print("\n" + "="*60)
    print("처방 더미 데이터 생성 완료!")
    print("="*60)

    from apps.prescriptions.models import Prescription, PrescriptionItem

    print(f"\n[통계 - 처방 데이터]")
    print(f"  - 처방전: {Prescription.objects.count()}건")
    print(f"  - 처방 항목: {PrescriptionItem.objects.count()}건")

    # 상태별 통계
    print(f"\n[상태별 분포]")
    for status_choice in Prescription.Status.choices:
        count = Prescription.objects.filter(status=status_choice[0]).count()
        print(f"  - {status_choice[1]}: {count}건")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 처방 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='처방 데이터만 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    parser.add_argument('-y', '--yes', action='store_true', help='확인 없이 자동 실행 (비대화형 모드)')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 처방 더미 데이터 생성 (3)")
    print("="*60)

    # 선행 조건 확인
    if not check_prerequisites():
        sys.exit(1)

    # --reset 옵션: 처방 데이터만 삭제
    if args.reset:
        if args.yes:
            reset_prescription_data()
        else:
            confirm = input("\n처방 데이터를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                reset_prescription_data()
            else:
                print("삭제 취소됨")
                sys.exit(0)

    force = args.reset or args.force  # reset 시에는 force=True

    # 처방 데이터 생성 (20건, 항목 약 60건)
    create_dummy_prescriptions(20, 3, force=force)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
