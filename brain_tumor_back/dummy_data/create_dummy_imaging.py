"""
더미 영상 검사 데이터 생성 스크립트

사용법:
    python manage.py shell
    >>> from apps.imaging.create_dummy_imaging import create_dummy_imaging_studies
    >>> create_dummy_imaging_studies(30, 20)
"""

import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.imaging.models import ImagingStudy, ImagingReport
from apps.patients.models import Patient
from apps.encounters.models import Encounter

User = get_user_model()


def create_dummy_imaging_studies(num_studies=30, num_reports=20):
    """
    더미 영상 검사 및 판독문 데이터 생성

    Args:
        num_studies (int): 생성할 영상 검사 수
        num_reports (int): 생성할 판독문 수 (검사 수보다 작아야 함)
    """
    print(f"Creating {num_studies} imaging studies with {num_reports} reports...")

    # 기존 데이터 확인
    existing_studies = ImagingStudy.objects.count()
    existing_reports = ImagingReport.objects.count()
    print(f"Existing studies: {existing_studies}, reports: {existing_reports}")

    # 필요한 데이터 가져오기
    patients = list(Patient.objects.all())
    encounters = list(Encounter.objects.all())
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    radiologists = list(User.objects.filter(role__code__in=['RIS', 'DOCTOR']))

    if not patients:
        print("No patients found. Please create patients first.")
        return

    if not encounters:
        print("No encounters found. Please create encounters first.")
        return

    if not doctors:
        print("No doctors found. Please create users with DOCTOR role.")
        return

    if not radiologists:
        print("No radiologists found. Using doctors as radiologists.")
        radiologists = doctors

    # 검사 종류와 부위
    modalities = ['CT', 'MRI', 'PET', 'X-RAY']
    body_parts = ['Brain', 'Head', 'Skull', 'Neck', 'Cervical Spine']
    statuses = ['ordered', 'scheduled', 'in-progress', 'completed', 'reported', 'cancelled']

    # 영상 검사 생성
    studies = []
    for i in range(num_studies):
        # encounter를 먼저 선택하고 그에 맞는 patient 가져오기
        encounter = random.choice(encounters)
        patient = encounter.patient

        # 날짜 생성 (최근 3개월 내)
        days_ago = random.randint(0, 90)
        ordered_at = timezone.now() - timedelta(days=days_ago)

        status = random.choice(statuses)
        scheduled_at = None
        performed_at = None

        if status in ['scheduled', 'in-progress', 'completed', 'reported']:
            scheduled_at = ordered_at + timedelta(days=random.randint(1, 3))

        if status in ['in-progress', 'completed', 'reported']:
            performed_at = scheduled_at + timedelta(hours=random.randint(1, 24))

        study = ImagingStudy.objects.create(
            patient=patient,
            encounter=encounter,
            modality=random.choice(modalities),
            body_part=random.choice(body_parts),
            status=status,
            ordered_by=random.choice(doctors),
            ordered_at=ordered_at,
            scheduled_at=scheduled_at,
            performed_at=performed_at,
            radiologist=random.choice(radiologists) if status in ['completed', 'reported'] else None,
            study_uid=f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1000, 9999)}",
            clinical_info=f"Clinical indication: {random.choice(['headache', 'dizziness', 'seizure', 'follow-up', 'screening'])}",
            special_instruction=random.choice(["", "Contrast enhanced", "Without contrast", "Urgent"])
        )
        studies.append(study)

        if i % 10 == 0:
            print(f"Created {i+1}/{num_studies} studies...")

    print(f"[OK] Created {len(studies)} imaging studies")

    # 판독문 생성 (완료된 검사에 대해서만)
    completed_studies = [s for s in studies if s.status in ['completed', 'reported']]

    if len(completed_studies) < num_reports:
        print(f"Warning: Only {len(completed_studies)} completed studies available for reports")
        num_reports = len(completed_studies)

    # 판독문 샘플 데이터
    findings_templates = [
        "No acute intracranial abnormality detected.",
        "Mild cerebral atrophy noted for age.",
        "Small area of signal abnormality in the left frontal lobe.",
        "Mass lesion identified in the right temporal lobe, measuring approximately {size} cm.",
        "Multiple small foci of increased signal intensity in the white matter.",
        "Contrast-enhancing lesion in the {location}, suggestive of {type}.",
    ]

    impression_templates = [
        "Normal brain imaging study.",
        "Age-related changes, no acute findings.",
        "Nonspecific white matter changes, likely chronic small vessel disease.",
        "Brain tumor suspected. Further evaluation recommended.",
        "Findings consistent with {diagnosis}. Clinical correlation advised.",
    ]

    lobes = ['frontal', 'temporal', 'parietal', 'occipital']
    hemispheres = ['left', 'right']
    tumor_types = ['glioma', 'meningioma', 'metastasis', 'astrocytoma']

    reports = []
    selected_studies = random.sample(completed_studies, num_reports)

    for i, study in enumerate(selected_studies):
        tumor_detected = random.random() < 0.3  # 30% 확률로 종양 발견

        if tumor_detected:
            lobe = random.choice(lobes)
            hemisphere = random.choice(hemispheres)
            tumor_type = random.choice(tumor_types)
            size = round(random.uniform(1.5, 4.5), 1)

            findings = random.choice(findings_templates).format(
                size=size,
                location=f"{hemisphere} {lobe} lobe",
                type=tumor_type
            )
            impression = f"Brain tumor detected in {hemisphere} {lobe} lobe. {random.choice(impression_templates).format(diagnosis=tumor_type)}"

            tumor_location = {
                "lobe": lobe,
                "hemisphere": hemisphere
            }
            tumor_size = {
                "diameter_cm": size,
                "volume_cm3": round((4/3) * 3.14159 * ((size/2)**3), 2)
            }
        else:
            findings = random.choice([t for t in findings_templates if '{' not in t])
            impression = random.choice([t for t in impression_templates if '{' not in t])
            tumor_location = None
            tumor_size = None

        # 판독문 상태 (70% 서명됨, 30% 초안)
        report_status = 'signed' if random.random() < 0.7 else 'draft'
        signed_at = timezone.now() if report_status == 'signed' else None

        report = ImagingReport.objects.create(
            imaging_study=study,
            radiologist=study.radiologist,
            findings=findings,
            impression=impression,
            tumor_detected=tumor_detected,
            tumor_location=tumor_location,
            tumor_size=tumor_size,
            status=report_status,
            signed_at=signed_at
        )
        reports.append(report)

        # 판독 완료된 검사는 상태 업데이트
        if report_status == 'signed':
            study.status = 'reported'
            study.save()

        if i % 5 == 0:
            print(f"Created {i+1}/{num_reports} reports...")

    print(f"[OK] Created {len(reports)} imaging reports")

    # 통계 출력
    print("\n=== Summary ===")
    print(f"Total studies: {ImagingStudy.objects.count()}")
    print(f"  - CT: {ImagingStudy.objects.filter(modality='CT').count()}")
    print(f"  - MRI: {ImagingStudy.objects.filter(modality='MRI').count()}")
    print(f"  - PET: {ImagingStudy.objects.filter(modality='PET').count()}")
    print(f"  - X-Ray: {ImagingStudy.objects.filter(modality='X-RAY').count()}")
    print(f"\nTotal reports: {ImagingReport.objects.count()}")
    print(f"  - Tumor detected: {ImagingReport.objects.filter(tumor_detected=True).count()}")
    print(f"  - Normal: {ImagingReport.objects.filter(tumor_detected=False).count()}")
    print(f"\nStatus breakdown:")
    for status in statuses:
        count = ImagingStudy.objects.filter(status=status).count()
        print(f"  - {status}: {count}")

    print("\n[DONE] Dummy data creation completed!")


if __name__ == "__main__":
    print("This script should be run from Django shell:")
    print("python manage.py shell")
    print(">>> from apps.imaging.create_dummy_imaging import create_dummy_imaging_studies")
    print(">>> create_dummy_imaging_studies(30, 20)")
