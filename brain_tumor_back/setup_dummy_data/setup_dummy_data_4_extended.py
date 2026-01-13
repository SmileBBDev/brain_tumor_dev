#!/usr/bin/env python
"""
Brain Tumor CDSS - 확장 더미 데이터 스크립트

이 스크립트는 추가 더미 데이터를 생성합니다:
- 환자 20명 추가 (총 50명)
- 오늘 예약 진료 8건 추가
- 과거 진료 기록 추가
- 과거 처방전 추가

사용법:
    python setup_dummy_data_4_extended.py
    python setup_dummy_data_4_extended.py --reset  # 기존 확장 데이터 삭제 후 새로 생성
"""

import os
import sys
from pathlib import Path
from datetime import timedelta, time as dt_time
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
from django.db import IntegrityError, transaction


# 추가 환자 20명 데이터
EXTENDED_PATIENTS = [
    {"name": "김태현", "birth_date": timezone.now().date() - timedelta(days=365*48), "gender": "M", "phone": "010-1001-1001", "ssn": "7601011001001", "blood_type": "A+", "allergies": [], "chronic_diseases": ["고혈압"], "address": "서울특별시 강서구 강서로 100"},
    {"name": "이수민", "birth_date": timezone.now().date() - timedelta(days=365*32), "gender": "F", "phone": "010-1001-1002", "ssn": "9203151001002", "blood_type": "B+", "allergies": ["페니실린"], "chronic_diseases": [], "address": "서울특별시 동작구 동작대로 200"},
    {"name": "박준호", "birth_date": timezone.now().date() - timedelta(days=365*56), "gender": "M", "phone": "010-1001-1003", "ssn": "6809201001003", "blood_type": "O+", "allergies": [], "chronic_diseases": ["당뇨", "고혈압"], "address": "경기도 안양시 만안구 안양로 300"},
    {"name": "최유진", "birth_date": timezone.now().date() - timedelta(days=365*28), "gender": "F", "phone": "010-1001-1004", "ssn": "9608101001004", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 종로구 종로 400"},
    {"name": "정민석", "birth_date": timezone.now().date() - timedelta(days=365*63), "gender": "M", "phone": "010-1001-1005", "ssn": "6105251001005", "blood_type": "A-", "allergies": ["조영제"], "chronic_diseases": ["고지혈증"], "address": "경기도 부천시 원미구 길주로 500"},
    {"name": "강서연", "birth_date": timezone.now().date() - timedelta(days=365*37), "gender": "F", "phone": "010-1001-1006", "ssn": "8706051001006", "blood_type": "B-", "allergies": [], "chronic_diseases": [], "address": "인천광역시 부평구 부평대로 600"},
    {"name": "윤재원", "birth_date": timezone.now().date() - timedelta(days=365*45), "gender": "M", "phone": "010-1001-1007", "ssn": "7909151001007", "blood_type": "O-", "allergies": ["아스피린"], "chronic_diseases": ["고혈압"], "address": "경기도 파주시 교하로 700"},
    {"name": "임하영", "birth_date": timezone.now().date() - timedelta(days=365*51), "gender": "F", "phone": "010-1001-1008", "ssn": "7312201001008", "blood_type": "AB-", "allergies": [], "chronic_diseases": ["당뇨"], "address": "서울특별시 성북구 성북로 800"},
    {"name": "한민주", "birth_date": timezone.now().date() - timedelta(days=365*23), "gender": "F", "phone": "010-1001-1009", "ssn": "0102151001009", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 도봉구 도봉로 900"},
    {"name": "오승현", "birth_date": timezone.now().date() - timedelta(days=365*39), "gender": "M", "phone": "010-1001-1010", "ssn": "8508101001010", "blood_type": "B+", "allergies": ["설파제"], "chronic_diseases": [], "address": "경기도 시흥시 시흥대로 1000"},
    {"name": "서지훈", "birth_date": timezone.now().date() - timedelta(days=365*54), "gender": "M", "phone": "010-1001-1011", "ssn": "7003121001011", "blood_type": "A+", "allergies": [], "chronic_diseases": ["고혈압", "당뇨"], "address": "부산광역시 사하구 낙동대로 1100"},
    {"name": "배아린", "birth_date": timezone.now().date() - timedelta(days=365*30), "gender": "F", "phone": "010-1001-1012", "ssn": "9407151001012", "blood_type": "O+", "allergies": [], "chronic_diseases": [], "address": "대구광역시 북구 침산로 1200"},
    {"name": "조현빈", "birth_date": timezone.now().date() - timedelta(days=365*46), "gender": "M", "phone": "010-1001-1013", "ssn": "7810201001013", "blood_type": "B+", "allergies": ["페니실린", "조영제"], "chronic_diseases": ["고지혈증"], "address": "광주광역시 동구 금남로 1300"},
    {"name": "신나연", "birth_date": timezone.now().date() - timedelta(days=365*26), "gender": "F", "phone": "010-1001-1014", "ssn": "9804151001014", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "대전광역시 중구 대종로 1400"},
    {"name": "권혁준", "birth_date": timezone.now().date() - timedelta(days=365*59), "gender": "M", "phone": "010-1001-1015", "ssn": "6507201001015", "blood_type": "A-", "allergies": [], "chronic_diseases": ["고혈압", "고지혈증"], "address": "울산광역시 동구 봉수로 1500"},
    {"name": "황예나", "birth_date": timezone.now().date() - timedelta(days=365*34), "gender": "F", "phone": "010-1001-1016", "ssn": "9001151001016", "blood_type": "O-", "allergies": ["아스피린"], "chronic_diseases": [], "address": "경기도 의정부시 평화로 1600"},
    {"name": "안시우", "birth_date": timezone.now().date() - timedelta(days=365*42), "gender": "M", "phone": "010-1001-1017", "ssn": "8206201001017", "blood_type": "B-", "allergies": [], "chronic_diseases": ["당뇨"], "address": "경기도 광명시 광명로 1700"},
    {"name": "문채원", "birth_date": timezone.now().date() - timedelta(days=365*22), "gender": "F", "phone": "010-1001-1018", "ssn": "0210151001018", "blood_type": "AB-", "allergies": [], "chronic_diseases": [], "address": "서울특별시 금천구 가산디지털로 1800"},
    {"name": "송민호", "birth_date": timezone.now().date() - timedelta(days=365*47), "gender": "M", "phone": "010-1001-1019", "ssn": "7705201001019", "blood_type": "A+", "allergies": ["설파제"], "chronic_diseases": ["고혈압"], "address": "서울특별시 구로구 디지털로 1900"},
    {"name": "류소연", "birth_date": timezone.now().date() - timedelta(days=365*36), "gender": "F", "phone": "010-1001-1020", "ssn": "8809151001020", "blood_type": "O+", "allergies": [], "chronic_diseases": [], "address": "경기도 김포시 김포대로 2000"},
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
]

# 주요 호소 증상
CHIEF_COMPLAINTS = [
    '두통이 심해요', '어지러움증이 계속됩니다', '손발 저림 증상',
    '기억력 감퇴', '수면 장애', '편두통', '목 통증',
    '시야 흐림', '균형 감각 이상', '근육 경련', '발작 증세',
    '정기 진료', '추적 검사', '상담', '재진', '수술 후 경과 관찰'
]

# SOAP 노트 샘플
SUBJECTIVE_SAMPLES = [
    '3일 전부터 지속되는 두통, 아침에 더 심함',
    '일주일간 어지러움 증상, 구역감 동반',
    '양손 저림 증상, 특히 야간에 심해짐',
    '최근 건망증이 심해졌다고 호소',
    '잠들기 어렵고 자주 깸, 피로감 호소',
    '우측 관자놀이 쪽 박동성 두통',
    '경추 부위 통증, 고개 돌릴 때 악화',
    '수술 후 회복 잘 되고 있음',
    '항암 치료 후 경과 양호',
]

OBJECTIVE_SAMPLES = [
    'BP 130/85, HR 72, BT 36.5',
    '신경학적 검사 정상, 경부 강직 없음',
    '동공 반사 정상, 안구 운동 정상',
    'Romberg test 양성, 보행 시 불안정',
    'MMT 정상, DTR 정상, 병적 반사 없음',
    'GCS 15, 의식 명료, 지남력 정상',
    '뇌 MRI: T2 고신호 병변 확인',
    '수술 부위 깨끗함, 감염 소견 없음',
]

ASSESSMENT_SAMPLES = [
    '긴장성 두통 의심, R/O 편두통',
    '말초성 현훈 vs 중추성 현훈 감별 필요',
    '수근관 증후군 의심',
    '경도 인지장애 가능성, 치매 스크리닝 필요',
    '불면증, 수면 무호흡 가능성',
    '뇌종양 의심, 추가 검사 필요',
    '경추 디스크 탈출증 의심',
    '수술 후 회복 양호',
    '항암 치료 효과 확인 중',
]

PLAN_SAMPLES = [
    '뇌 MRI 촬영, 진통제 처방, 2주 후 재진',
    '청력검사, 전정기능검사 예정, 어지럼증 약물 처방',
    '신경전도검사 의뢰, 보존적 치료',
    '인지기능검사, 혈액검사 (갑상선, B12)',
    '수면다원검사 의뢰, 수면위생 교육',
    'MRI 추적검사, 신경외과 협진',
    '물리치료 의뢰, NSAIDs 처방',
    '정기 추적 검사 예정',
    '항암 치료 지속, 혈액검사 모니터링',
]

# 약품 목록 (처방용)
MEDICATIONS = [
    {"name": "Temozolomide 140mg", "code": "TEM140", "dosage": "140mg", "frequency": "QD", "route": "PO", "instructions": "공복에 복용"},
    {"name": "Dexamethasone 4mg", "code": "DEX4", "dosage": "4mg", "frequency": "TID", "route": "PO", "instructions": "식후 복용"},
    {"name": "Levetiracetam 500mg", "code": "LEV500", "dosage": "500mg", "frequency": "BID", "route": "PO", "instructions": "식사와 무관"},
    {"name": "Acetaminophen 500mg", "code": "ACE500", "dosage": "500mg", "frequency": "QID", "route": "PO", "instructions": "1일 4g 초과 금지"},
    {"name": "Ondansetron 8mg", "code": "OND8", "dosage": "8mg", "frequency": "BID", "route": "PO", "instructions": "구역 시 복용"},
    {"name": "Esomeprazole 40mg", "code": "ESO40", "dosage": "40mg", "frequency": "QD", "route": "PO", "instructions": "아침 식전 복용"},
    {"name": "Tramadol 50mg", "code": "TRA50", "dosage": "50mg", "frequency": "TID", "route": "PO", "instructions": "통증 시 복용"},
    {"name": "Valproic acid 500mg", "code": "VPA500", "dosage": "500mg", "frequency": "TID", "route": "PO", "instructions": "간기능 검사 필요"},
]


def create_extended_patients():
    """추가 환자 20명 생성"""
    print("\n[1단계] 추가 환자 생성 (20명)...")

    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 등록자 (첫 번째 관리자 또는 시스템 매니저)
    registered_by = User.objects.filter(role__code__in=['SYSTEMMANAGER', 'ADMIN']).first()
    if not registered_by:
        registered_by = User.objects.first()

    if not registered_by:
        print("[ERROR] 등록자 사용자가 없습니다.")
        return False

    created_count = 0
    skipped_count = 0

    for patient_data in EXTENDED_PATIENTS:
        try:
            # SSN 중복 확인
            if Patient.objects.filter(ssn=patient_data['ssn']).exists():
                skipped_count += 1
                continue

            Patient.objects.create(
                registered_by=registered_by,
                status='active',
                **patient_data
            )
            created_count += 1
        except IntegrityError:
            skipped_count += 1
        except Exception as e:
            print(f"  오류 ({patient_data['name']}): {e}")

    print(f"[OK] 환자 생성: {created_count}명, 스킵: {skipped_count}명")
    print(f"  현재 전체 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    return True


def create_today_scheduled_encounters(target_count=8):
    """오늘 예약 진료 생성"""
    print(f"\n[2단계] 오늘 예약 진료 생성 (목표: {target_count}건)...")

    from apps.encounters.models import Encounter
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 오늘 예약 진료 수 확인
    today = timezone.now().date()
    existing_count = Encounter.objects.filter(
        admission_date__date=today,
        status='scheduled'
    ).count()

    if existing_count >= target_count:
        print(f"[SKIP] 이미 {existing_count}건의 오늘 예약 진료가 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 활성 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    departments = ['neurology', 'neurosurgery']
    scheduled_times = [
        dt_time(9, 0), dt_time(9, 30), dt_time(10, 0), dt_time(10, 30),
        dt_time(11, 0), dt_time(14, 0), dt_time(14, 30), dt_time(15, 0),
        dt_time(15, 30), dt_time(16, 0), dt_time(16, 30)
    ]

    today_complaints = [
        '정기 진료', '추적 검사', 'MRI 결과 상담', '재진',
        '수술 후 경과 관찰', '항암 치료 상담', '두통 검진', '증상 확인'
    ]

    # 이미 오늘 예약이 있는 환자 제외
    already_scheduled_patients = set(
        Encounter.objects.filter(
            admission_date__date=today,
            status='scheduled'
        ).values_list('patient_id', flat=True)
    )
    available_patients = [p for p in patients if p.id not in already_scheduled_patients]

    if not available_patients:
        print("[WARNING] 사용 가능한 환자가 없습니다. 기존 환자 재사용.")
        available_patients = patients

    created_count = 0
    needed = target_count - existing_count

    for i in range(needed):
        patient = random.choice(available_patients)
        doctor = random.choice(doctors)

        try:
            encounter = Encounter.objects.create(
                patient=patient,
                attending_doctor=doctor,
                admission_date=timezone.now(),
                scheduled_time=scheduled_times[i % len(scheduled_times)],
                status='scheduled',
                encounter_type='outpatient',
                department=random.choice(departments),
                chief_complaint=random.choice(today_complaints),
            )
            created_count += 1

            # 사용된 환자 목록에서 제거 (중복 방지)
            if patient in available_patients and len(available_patients) > 1:
                available_patients.remove(patient)

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 오늘 예약 진료: {created_count}건 생성")
    print(f"  현재 오늘 예약 진료: {Encounter.objects.filter(admission_date__date=today, status='scheduled').count()}건")
    return True


def create_past_encounters(target_per_patient=5):
    """과거 진료 기록 생성 (환자별 5건)"""
    print(f"\n[3단계] 과거 진료 기록 생성 (환자당 {target_per_patient}건)...")

    from apps.encounters.models import Encounter
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    encounter_types = ['outpatient', 'inpatient', 'emergency']
    departments = ['neurology', 'neurosurgery']

    created_count = 0

    for patient in patients:
        # 이미 있는 진료 수 확인
        existing_count = Encounter.objects.filter(patient=patient).count()
        if existing_count >= target_per_patient:
            continue

        needed = target_per_patient - existing_count

        for i in range(needed):
            days_ago = random.randint(7, 365)  # 과거 1주~1년
            admission_date = timezone.now() - timedelta(days=days_ago)

            encounter_type = random.choice(encounter_types)
            status = random.choice(['completed', 'completed', 'completed', 'cancelled'])  # 대부분 완료

            discharge_date = None
            if status == 'completed':
                if encounter_type == 'outpatient':
                    discharge_days = 0
                elif encounter_type == 'inpatient':
                    discharge_days = random.randint(3, 14)
                else:
                    discharge_days = random.randint(1, 3)
                discharge_date = admission_date + timedelta(days=discharge_days)

            soap_data = {}
            if status == 'completed':
                soap_data = {
                    'subjective': random.choice(SUBJECTIVE_SAMPLES),
                    'objective': random.choice(OBJECTIVE_SAMPLES),
                    'assessment': random.choice(ASSESSMENT_SAMPLES),
                    'plan': random.choice(PLAN_SAMPLES),
                }

            try:
                Encounter.objects.create(
                    patient=patient,
                    encounter_type=encounter_type,
                    status=status,
                    attending_doctor=random.choice(doctors),
                    department=random.choice(departments),
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    chief_complaint=random.choice(CHIEF_COMPLAINTS),
                    primary_diagnosis=random.choice(DIAGNOSES),
                    secondary_diagnoses=random.sample(['고혈압', '당뇨', '고지혈증'], random.randint(0, 2)),
                    **soap_data,
                )
                created_count += 1
            except Exception as e:
                print(f"  오류: {e}")

    print(f"[OK] 과거 진료 기록: {created_count}건 생성")
    print(f"  현재 전체 진료: {Encounter.objects.count()}건")
    return True


def create_past_prescriptions(target_per_patient=3):
    """과거 처방전 생성 (환자별 3건)"""
    print(f"\n[4단계] 과거 처방전 생성 (환자당 {target_per_patient}건)...")

    from apps.prescriptions.models import Prescription, PrescriptionItem
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    statuses = ['ISSUED', 'DISPENSED', 'DISPENSED', 'DISPENSED']  # 대부분 조제 완료

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

    for patient in patients:
        # 이미 있는 처방 수 확인
        existing_count = Prescription.objects.filter(patient=patient).count()
        if existing_count >= target_per_patient:
            continue

        needed = target_per_patient - existing_count

        # 환자의 진료 기록 가져오기
        patient_encounters = list(Encounter.objects.filter(patient=patient, status='completed'))

        for i in range(needed):
            doctor = random.choice(doctors)
            encounter = random.choice(patient_encounters) if patient_encounters else None
            status = random.choice(statuses)
            diagnosis = random.choice(DIAGNOSES)

            days_ago = random.randint(7, 180)
            created_at_base = timezone.now() - timedelta(days=days_ago)

            issued_at = created_at_base + timedelta(hours=random.randint(1, 4))
            dispensed_at = None
            if status == 'DISPENSED':
                dispensed_at = issued_at + timedelta(hours=random.randint(1, 24))

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
                    )

                    # 처방 항목 생성 (1~4개)
                    num_items = random.randint(1, 4)
                    selected_meds = random.sample(MEDICATIONS, min(num_items, len(MEDICATIONS)))

                    for order, med in enumerate(selected_meds):
                        duration = random.choice([7, 14, 28, 30])

                        freq_multiplier = {'QD': 1, 'BID': 2, 'TID': 3, 'QID': 4}
                        daily_count = freq_multiplier.get(med['frequency'], 1)
                        quantity = int(duration * daily_count)

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

    print(f"[OK] 과거 처방전: {prescription_count}건 생성")
    print(f"[OK] 처방 항목: {item_count}건 생성")
    print(f"  현재 전체 처방: {Prescription.objects.count()}건")
    return True


def print_summary():
    """데이터 요약 출력"""
    print("\n" + "="*60)
    print("확장 더미 데이터 생성 완료!")
    print("="*60)

    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from apps.prescriptions.models import Prescription, PrescriptionItem

    today = timezone.now().date()

    print(f"\n[통계]")
    print(f"  - 전체 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 전체 진료: {Encounter.objects.count()}건")
    print(f"  - 오늘 예약 진료: {Encounter.objects.filter(admission_date__date=today, status='scheduled').count()}건")
    print(f"  - 전체 처방: {Prescription.objects.count()}건")
    print(f"  - 전체 처방 항목: {PrescriptionItem.objects.count()}건")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 확장 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='확장 데이터 삭제 후 새로 생성')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 확장 더미 데이터 생성")
    print("="*60)

    # 1. 추가 환자 생성
    create_extended_patients()

    # 2. 오늘 예약 진료 생성
    create_today_scheduled_encounters(target_count=8)

    # 3. 과거 진료 기록 생성
    create_past_encounters(target_per_patient=5)

    # 4. 과거 처방전 생성
    create_past_prescriptions(target_per_patient=3)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
