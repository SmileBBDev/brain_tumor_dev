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


def create_ocs_ris_requests(target_count=5):
    """OCS RIS (영상 검사) 요청 생성"""
    print(f"\n[5단계] OCS RIS 요청 생성 (목표: {target_count}건)...")

    from apps.ocs.models import OCS
    from apps.imaging.models import ImagingStudy
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    encounters = list(Encounter.objects.all())
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    radiologists = list(User.objects.filter(role__code__in=['RIS', 'DOCTOR']))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not radiologists:
        radiologists = doctors

    # RIS 요청 상세 데이터 (30개) - 모두 ORDERED 상태
    ris_requests = [
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "지속적인 두통과 시야 흐림 증상", "request_detail": "Brain MRI with contrast - 뇌종양 의심, 조영증강 MRI 요청", "special_instruction": "조영제 사용, 환자 조영제 알레르기 없음 확인"},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "급성 의식 저하", "request_detail": "Brain CT - 뇌출혈 감별 필요", "special_instruction": "응급 촬영 요청"},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "만성 두통 6개월", "request_detail": "Brain MRI - 두통 원인 평가", "special_instruction": ""},
        {"modality": "PET", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 진단 후 병기 결정", "request_detail": "Brain PET-CT - 전신 전이 여부 확인", "special_instruction": "금식 6시간 이상"},
        {"modality": "CT", "body_part": "Head", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "부비동염 의심", "request_detail": "Paranasal sinus CT", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Cervical Spine", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "경부 통증 및 상지 저림", "request_detail": "C-spine MRI - 디스크 평가", "special_instruction": ""},
        {"modality": "CT", "body_part": "Head", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "교통사고 후 두부 외상 평가", "request_detail": "Head CT without contrast - 급성 두개내 출혈 여부 확인", "special_instruction": "조영제 없이 촬영"},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "급성 뇌경색 의심", "request_detail": "Brain MRI with DWI - 급성 허혈성 변화 평가", "special_instruction": "DWI 포함 필수"},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 수술 후 1주", "request_detail": "Brain CT - 수술 후 출혈 여부 확인", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "간질 발작 환자", "request_detail": "Brain MRI epilepsy protocol", "special_instruction": "해마 고해상도 촬영"},
        {"modality": "PET", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "치매 감별 진단", "request_detail": "Brain FDG-PET", "special_instruction": "금식 6시간"},
        {"modality": "X-RAY", "body_part": "Skull", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "두부 외상", "request_detail": "Skull X-ray AP/Lateral", "special_instruction": ""},
        {"modality": "PET", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "교모세포종 수술 후 추적 검사", "request_detail": "Brain PET-CT - 종양 재발 여부 평가", "special_instruction": "금식 6시간 이상 확인 필요"},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌하수체 종양 의심", "request_detail": "Sellar MRI with dynamic enhancement", "special_instruction": "Dynamic enhancement 포함"},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌수두증 추적", "request_detail": "Brain CT - 뇌실 크기 평가", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "다발성 경화증 추적", "request_detail": "Brain MRI MS protocol", "special_instruction": "이전 검사와 비교 필요"},
        {"modality": "CT", "body_part": "Head", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌농양 의심", "request_detail": "Brain CT with contrast", "special_instruction": "조영증강 촬영"},
        {"modality": "MRI", "body_part": "Neck", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "경동맥 협착 의심", "request_detail": "Neck MRA", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Cervical Spine", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "경추 디스크 탈출증 의심", "request_detail": "Cervical Spine MRI - 신경근 압박 평가", "special_instruction": ""},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "지주막하 출혈 의심", "request_detail": "Brain CT - SAH 감별", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌전이암 추적", "request_detail": "Brain MRI with contrast - 전이 병변 평가", "special_instruction": "조영증강 필수"},
        {"modality": "PET", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "림프종 의심", "request_detail": "Brain PET-CT", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "청신경초종 추적", "request_detail": "IAC MRI", "special_instruction": "내이도 고해상도"},
        {"modality": "CT", "body_part": "Head", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "안면 외상", "request_detail": "Facial bone CT", "special_instruction": "3D 재구성 포함"},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "발작 후 뇌 평가", "request_detail": "Brain CT - 뇌전증 원인 평가", "special_instruction": "환자 진정 상태 확인"},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 항암 치료 후 평가", "request_detail": "Brain MRI - 치료 반응 평가", "special_instruction": ""},
        {"modality": "CT", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌실복강 단락술 후", "request_detail": "Brain CT - 단락관 위치 확인", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌종양 감마나이프 치료 후", "request_detail": "Brain MRI - 방사선 괴사 vs 재발 감별", "special_instruction": "Perfusion MRI 포함"},
        {"modality": "PET", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "저등급 교종 추적", "request_detail": "Brain PET-CT - 악성 변환 평가", "special_instruction": ""},
        {"modality": "MRI", "body_part": "Brain", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "수막종 수술 후 3개월", "request_detail": "Brain MRI with contrast - 잔여 종양 평가", "special_instruction": "이전 검사와 비교"},
    ]

    created_count = 0

    for i, req in enumerate(ris_requests[:target_count]):
        patient = patients[i % len(patients)]
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters else None
        ocs_status = req['ocs_status']

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(radiologists)

        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": req['clinical_info'],
            "request_detail": req['request_detail'],
            "special_instruction": req['special_instruction'],
        }

        # worker_result (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            tumor_detected = random.random() < 0.4
            lobes = ['frontal', 'temporal', 'parietal', 'occipital']
            hemispheres = ['left', 'right']

            worker_result = {
                "_template": "RIS",
                "_version": "1.1",
                "_confirmed": ocs_status == 'CONFIRMED',
                "findings": "Mass lesion identified in right temporal lobe." if tumor_detected else "No acute intracranial abnormality. Normal brain parenchyma.",
                "impression": "Brain tumor suspected, recommend biopsy." if tumor_detected else "Normal study, no significant findings.",
                "recommendation": "Neurosurgery consultation recommended." if tumor_detected else "Routine follow-up as clinically indicated.",
                "tumor": {
                    "detected": tumor_detected,
                    "location": {"lobe": random.choice(lobes), "hemisphere": random.choice(hemispheres)} if tumor_detected else {},
                    "size": {"max_diameter_cm": round(random.uniform(1.5, 4.5), 1), "volume_cc": round(random.uniform(5.0, 40.0), 1)} if tumor_detected else {}
                },
                "dicom": {
                    "study_uid": f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1000, 9999)}",
                    "series": [],
                    "accession_number": f"ACC{random.randint(10000, 99999)}",
                    "series_count": random.randint(3, 8),
                    "instance_count": random.randint(100, 400)
                },
                "work_notes": []
            }

        # 타임스탬프 계산
        days_ago = random.randint(0, 30)
        base_time = timezone.now() - timedelta(days=days_ago)
        timestamps = {'accepted_at': None, 'in_progress_at': None, 'result_ready_at': None, 'confirmed_at': None}

        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['accepted_at'] = base_time + timedelta(hours=random.randint(1, 3))
        if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['in_progress_at'] = base_time + timedelta(hours=random.randint(3, 8))
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            timestamps['result_ready_at'] = base_time + timedelta(hours=random.randint(8, 24))
        if ocs_status == 'CONFIRMED':
            timestamps['confirmed_at'] = base_time + timedelta(hours=random.randint(24, 48))

        try:
            with transaction.atomic():
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='RIS',
                    job_type=req['modality'],
                    ocs_status=ocs_status,
                    priority=req['priority'],
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                    accepted_at=timestamps['accepted_at'],
                    in_progress_at=timestamps['in_progress_at'],
                    result_ready_at=timestamps['result_ready_at'],
                    confirmed_at=timestamps['confirmed_at'],
                )

                # ImagingStudy 연결 생성
                scheduled_at = None
                performed_at = None
                if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    scheduled_at = base_time + timedelta(days=1)
                if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    performed_at = scheduled_at + timedelta(hours=random.randint(2, 8)) if scheduled_at else None

                ImagingStudy.objects.create(
                    ocs=ocs,
                    modality=req['modality'],
                    body_part=req['body_part'],
                    study_uid=worker_result.get('dicom', {}).get('study_uid') if worker_result else None,
                    series_count=worker_result.get('dicom', {}).get('series_count', 0) if worker_result else 0,
                    instance_count=worker_result.get('dicom', {}).get('instance_count', 0) if worker_result else 0,
                    scheduled_at=scheduled_at,
                    performed_at=performed_at,
                )

                created_count += 1
                print(f"  - RIS 요청 생성: {ocs.ocs_id} ({req['modality']} {req['body_part']}) - {ocs_status}")

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS RIS 요청 생성: {created_count}건")
    print(f"  현재 전체 OCS(RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    return True


def create_ocs_lis_requests(target_count=5):
    """OCS LIS (검사) 요청 생성"""
    print(f"\n[6단계] OCS LIS 요청 생성 (목표: {target_count}건)...")

    from apps.ocs.models import OCS
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    encounters = list(Encounter.objects.all())
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    lab_workers = list(User.objects.filter(role__code__in=['LIS', 'DOCTOR']))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not lab_workers:
        lab_workers = doctors

    # LIS 요청 상세 데이터 (30개) - 모두 ORDERED 상태
    lis_requests = [
        {"job_type": "CBC", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "발열 및 전신 쇠약감", "request_detail": "Complete Blood Count - 감염 및 빈혈 평가", "special_instruction": "공복 불필요",
         "test_results": [{"code": "WBC", "name": "백혈구", "value": "", "unit": "10^3/uL", "reference": "4.0-11.0", "is_abnormal": False}, {"code": "RBC", "name": "적혈구", "value": "", "unit": "10^6/uL", "reference": "4.0-6.0", "is_abnormal": False}, {"code": "HGB", "name": "혈색소", "value": "", "unit": "g/dL", "reference": "12.0-17.0", "is_abnormal": False}, {"code": "PLT", "name": "혈소판", "value": "", "unit": "10^3/uL", "reference": "150-400", "is_abnormal": False}]},
        {"job_type": "BMP", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "수술 전 검사", "request_detail": "Basic Metabolic Panel", "special_instruction": "공복 8시간",
         "test_results": [{"code": "GLU", "name": "혈당", "value": "", "unit": "mg/dL", "reference": "70-100", "is_abnormal": False}, {"code": "BUN", "name": "요소질소", "value": "", "unit": "mg/dL", "reference": "7-20", "is_abnormal": False}, {"code": "CRE", "name": "크레아티닌", "value": "", "unit": "mg/dL", "reference": "0.7-1.3", "is_abnormal": False}]},
        {"job_type": "Coagulation", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "수술 전 응고 검사", "request_detail": "PT/INR, aPTT", "special_instruction": "",
         "test_results": [{"code": "PT", "name": "프로트롬빈시간", "value": "", "unit": "sec", "reference": "11-13.5", "is_abnormal": False}, {"code": "INR", "name": "INR", "value": "", "unit": "", "reference": "0.9-1.1", "is_abnormal": False}, {"code": "APTT", "name": "활성화부분트롬보플라스틴시간", "value": "", "unit": "sec", "reference": "25-35", "is_abnormal": False}]},
        {"job_type": "LFT", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "항암제 간독성 모니터링", "request_detail": "Liver Function Test", "special_instruction": "",
         "test_results": [{"code": "AST", "name": "AST", "value": "", "unit": "U/L", "reference": "0-40", "is_abnormal": False}, {"code": "ALT", "name": "ALT", "value": "", "unit": "U/L", "reference": "0-41", "is_abnormal": False}, {"code": "ALP", "name": "알칼리포스파타제", "value": "", "unit": "U/L", "reference": "40-130", "is_abnormal": False}]},
        {"job_type": "Thyroid Panel", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌하수체 기능 평가", "request_detail": "TSH, Free T4, T3", "special_instruction": "",
         "test_results": [{"code": "TSH", "name": "갑상선자극호르몬", "value": "", "unit": "mIU/L", "reference": "0.4-4.0", "is_abnormal": False}, {"code": "FT4", "name": "유리T4", "value": "", "unit": "ng/dL", "reference": "0.8-1.8", "is_abnormal": False}]},
        {"job_type": "Urinalysis", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "요로감염 의심", "request_detail": "Complete Urinalysis", "special_instruction": "중간뇨 채취",
         "test_results": [{"code": "WBC_U", "name": "뇨백혈구", "value": "", "unit": "/HPF", "reference": "0-5", "is_abnormal": False}, {"code": "RBC_U", "name": "뇨적혈구", "value": "", "unit": "/HPF", "reference": "0-3", "is_abnormal": False}]},
        {"job_type": "GENETIC", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 수술 전 유전자 분석", "request_detail": "IDH1/IDH2 mutation analysis, MGMT methylation status", "special_instruction": "조직 검체 필요",
         "test_results": [{"code": "GENE", "name": "유전자 변이 분석", "value": "", "unit": "", "reference": "", "is_abnormal": False}],
         "gene_mutations": [{"gene_name": "IDH1", "mutation_type": "", "status": "Pending", "allele_frequency": None, "clinical_significance": ""}, {"gene_name": "TP53", "mutation_type": "", "status": "Pending", "allele_frequency": None, "clinical_significance": ""}, {"gene_name": "MGMT", "mutation_type": "", "status": "Pending", "allele_frequency": None, "clinical_significance": ""}]},
        {"job_type": "RNA_SEQ", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 분자 아형 분류", "request_detail": "RNA sequencing for molecular subtyping", "special_instruction": "냉동 조직 필요",
         "test_results": [{"code": "RNA", "name": "RNA 시퀀싱", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "CBC", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "항암 치료 전 혈액 검사", "request_detail": "CBC with differential", "special_instruction": "",
         "test_results": [{"code": "WBC", "name": "백혈구", "value": "", "unit": "10^3/uL", "reference": "4.0-11.0", "is_abnormal": False}, {"code": "HGB", "name": "혈색소", "value": "", "unit": "g/dL", "reference": "12.0-17.0", "is_abnormal": False}, {"code": "PLT", "name": "혈소판", "value": "", "unit": "10^3/uL", "reference": "150-400", "is_abnormal": False}]},
        {"job_type": "CSF", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌수막염 감별", "request_detail": "CSF analysis - cell count, protein, glucose", "special_instruction": "요추천자 후 즉시 검사",
         "test_results": [{"code": "CSF_WBC", "name": "CSF 백혈구", "value": "", "unit": "/uL", "reference": "0-5", "is_abnormal": False}, {"code": "CSF_PRO", "name": "CSF 단백", "value": "", "unit": "mg/dL", "reference": "15-45", "is_abnormal": False}]},
        {"job_type": "RFT", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "신기능 평가", "request_detail": "Renal Function Test", "special_instruction": "",
         "test_results": [{"code": "BUN", "name": "요소질소", "value": "", "unit": "mg/dL", "reference": "7-20", "is_abnormal": False}, {"code": "CRE", "name": "크레아티닌", "value": "", "unit": "mg/dL", "reference": "0.7-1.3", "is_abnormal": False}]},
        {"job_type": "Lipid Panel", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "심혈관 위험도 평가", "request_detail": "Total cholesterol, LDL, HDL, TG", "special_instruction": "공복 12시간",
         "test_results": [{"code": "TC", "name": "총콜레스테롤", "value": "", "unit": "mg/dL", "reference": "0-200", "is_abnormal": False}, {"code": "LDL", "name": "LDL", "value": "", "unit": "mg/dL", "reference": "0-130", "is_abnormal": False}]},
        {"job_type": "Tumor Markers", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 치료 반응 평가", "request_detail": "Tumor marker panel (CEA, AFP, CA19-9)", "special_instruction": "공복 8시간 필요",
         "test_results": [{"code": "CEA", "name": "암배아항원", "value": "", "unit": "ng/mL", "reference": "0-5.0", "is_abnormal": False}, {"code": "AFP", "name": "알파태아단백", "value": "", "unit": "ng/mL", "reference": "0-10.0", "is_abnormal": False}]},
        {"job_type": "GENE_PANEL", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌종양 comprehensive panel", "request_detail": "Next-gen sequencing brain tumor panel", "special_instruction": "FFPE 조직",
         "test_results": [{"code": "NGS", "name": "NGS 패널", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "BIOPSY", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌종양 조직검사", "request_detail": "Brain tumor biopsy pathology", "special_instruction": "냉동절편 포함",
         "test_results": [{"code": "PATH", "name": "조직병리", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "HbA1c", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "당뇨 조절 상태 평가", "request_detail": "Glycated hemoglobin", "special_instruction": "",
         "test_results": [{"code": "HBA1C", "name": "당화혈색소", "value": "", "unit": "%", "reference": "4.0-5.6", "is_abnormal": False}]},
        {"job_type": "ESR_CRP", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "염증 지표 평가", "request_detail": "ESR, CRP", "special_instruction": "",
         "test_results": [{"code": "ESR", "name": "적혈구침강속도", "value": "", "unit": "mm/hr", "reference": "0-20", "is_abnormal": False}, {"code": "CRP", "name": "C반응단백", "value": "", "unit": "mg/dL", "reference": "0-0.5", "is_abnormal": False}]},
        {"job_type": "Electrolytes", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "전해질 불균형 교정", "request_detail": "Na, K, Cl, CO2", "special_instruction": "",
         "test_results": [{"code": "NA", "name": "나트륨", "value": "", "unit": "mEq/L", "reference": "136-145", "is_abnormal": False}, {"code": "K", "name": "칼륨", "value": "", "unit": "mEq/L", "reference": "3.5-5.0", "is_abnormal": False}]},
        {"job_type": "PROTEIN", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "뇌손상 마커 평가", "request_detail": "Brain injury protein markers (GFAP, S100B, NSE)", "special_instruction": "",
         "test_results": [{"code": "PROT", "name": "단백질 마커 분석", "value": "", "unit": "", "reference": "", "is_abnormal": False}],
         "protein_markers": [{"marker_name": "GFAP", "value": None, "unit": "ng/mL", "reference_range": "0-2.0", "is_abnormal": False, "interpretation": ""}, {"marker_name": "S100B", "value": None, "unit": "ug/L", "reference_range": "0-0.15", "is_abnormal": False, "interpretation": ""}, {"marker_name": "NSE", "value": None, "unit": "ng/mL", "reference_range": "0-16.3", "is_abnormal": False, "interpretation": ""}]},
        {"job_type": "BIOMARKER", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "신경퇴행성 질환 마커", "request_detail": "Neurodegenerative biomarkers", "special_instruction": "",
         "test_results": [{"code": "BIO", "name": "바이오마커 패널", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "CBC", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "항암 치료 후 혈액 검사", "request_detail": "CBC with differential - post chemo", "special_instruction": "",
         "test_results": [{"code": "WBC", "name": "백혈구", "value": "", "unit": "10^3/uL", "reference": "4.0-11.0", "is_abnormal": False}, {"code": "ANC", "name": "절대호중구수", "value": "", "unit": "/uL", "reference": "1500-8000", "is_abnormal": False}, {"code": "PLT", "name": "혈소판", "value": "", "unit": "10^3/uL", "reference": "150-400", "is_abnormal": False}]},
        {"job_type": "GENETIC", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "유전성 암 증후군 스크리닝", "request_detail": "Hereditary cancer gene panel", "special_instruction": "",
         "test_results": [{"code": "GENE", "name": "유전자 검사", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "Drug Level", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "항경련제 농도 모니터링", "request_detail": "Levetiracetam level", "special_instruction": "투약 전 trough level",
         "test_results": [{"code": "LEV", "name": "레베티라세탐", "value": "", "unit": "ug/mL", "reference": "12-46", "is_abnormal": False}]},
        {"job_type": "Hormone", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌하수체 호르몬 평가", "request_detail": "Pituitary hormone panel", "special_instruction": "오전 8시 채혈",
         "test_results": [{"code": "ACTH", "name": "부신피질자극호르몬", "value": "", "unit": "pg/mL", "reference": "10-60", "is_abnormal": False}, {"code": "CORT", "name": "코르티솔", "value": "", "unit": "ug/dL", "reference": "5-25", "is_abnormal": False}, {"code": "GH", "name": "성장호르몬", "value": "", "unit": "ng/mL", "reference": "0-3", "is_abnormal": False}]},
        {"job_type": "CMP", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "항암치료 전 전해질 및 간기능 평가", "request_detail": "Comprehensive Metabolic Panel", "special_instruction": "공복 8시간 필요",
         "test_results": [{"code": "GLU", "name": "혈당", "value": "", "unit": "mg/dL", "reference": "70-100", "is_abnormal": False}, {"code": "BUN", "name": "요소질소", "value": "", "unit": "mg/dL", "reference": "7-20", "is_abnormal": False}, {"code": "CRE", "name": "크레아티닌", "value": "", "unit": "mg/dL", "reference": "0.7-1.3", "is_abnormal": False}, {"code": "NA", "name": "나트륨", "value": "", "unit": "mEq/L", "reference": "136-145", "is_abnormal": False}, {"code": "K", "name": "칼륨", "value": "", "unit": "mEq/L", "reference": "3.5-5.0", "is_abnormal": False}]},
        {"job_type": "GENETIC", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "교모세포종 분자 진단", "request_detail": "GBM molecular profiling", "special_instruction": "",
         "test_results": [{"code": "GENE", "name": "분자 프로파일링", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "PROTEIN_PANEL", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "뇌척수액 단백질 분석", "request_detail": "CSF protein electrophoresis", "special_instruction": "",
         "test_results": [{"code": "CSF_PROT", "name": "CSF 단백 전기영동", "value": "", "unit": "", "reference": "", "is_abnormal": False}]},
        {"job_type": "Tumor Markers", "ocs_status": "ORDERED", "priority": "normal", "clinical_info": "생식세포종양 마커", "request_detail": "AFP, beta-hCG", "special_instruction": "",
         "test_results": [{"code": "AFP", "name": "알파태아단백", "value": "", "unit": "ng/mL", "reference": "0-10.0", "is_abnormal": False}, {"code": "BHCG", "name": "베타융모성생식선자극호르몬", "value": "", "unit": "mIU/mL", "reference": "0-5", "is_abnormal": False}]},
        {"job_type": "Ammonia", "ocs_status": "ORDERED", "priority": "urgent", "clinical_info": "간성뇌증 평가", "request_detail": "Serum ammonia level", "special_instruction": "즉시 검사 필요",
         "test_results": [{"code": "NH3", "name": "암모니아", "value": "", "unit": "umol/L", "reference": "10-35", "is_abnormal": False}]},
    ]

    created_count = 0

    for i, req in enumerate(lis_requests[:target_count]):
        patient = patients[i % len(patients)]
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters else None
        ocs_status = req['ocs_status']

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(lab_workers)

        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": req['clinical_info'],
            "request_detail": req['request_detail'],
            "special_instruction": req['special_instruction'],
        }

        # worker_result (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            is_abnormal = any(t.get('is_abnormal', False) for t in req['test_results'])

            worker_result = {
                "_template": "LIS",
                "_version": "1.0",
                "_confirmed": ocs_status == 'CONFIRMED',
                "test_results": req['test_results'],
                "summary": "이상 소견 있음" if is_abnormal else "모든 검사 정상 범위",
                "interpretation": "추가 검사 또는 임상적 상관관계 필요" if is_abnormal else "특이 소견 없음",
                "_custom": {}
            }

            # 유전자 검사인 경우
            if 'gene_mutations' in req:
                worker_result['test_type'] = 'GENETIC'
                worker_result['gene_mutations'] = req['gene_mutations']
                worker_result['summary'] = "IDH1 변이 양성, MGMT 메틸화 양성"
                worker_result['interpretation'] = "예후 양호, Temozolomide 반응 예상"

            # 단백질 검사인 경우
            if 'protein_markers' in req:
                worker_result['test_type'] = 'PROTEIN'
                worker_result['protein_markers'] = req['protein_markers']
                worker_result['summary'] = "GFAP, S100B 상승 - 뇌손상 소견"
                worker_result['interpretation'] = "뇌종양 또는 뇌손상 관련 마커 상승, 추적 관찰 필요"

        # 타임스탬프 계산
        days_ago = random.randint(0, 30)
        base_time = timezone.now() - timedelta(days=days_ago)
        timestamps = {'accepted_at': None, 'in_progress_at': None, 'result_ready_at': None, 'confirmed_at': None}

        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['accepted_at'] = base_time + timedelta(hours=random.randint(1, 2))
        if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['in_progress_at'] = base_time + timedelta(hours=random.randint(2, 6))
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            timestamps['result_ready_at'] = base_time + timedelta(hours=random.randint(6, 24))
        if ocs_status == 'CONFIRMED':
            timestamps['confirmed_at'] = base_time + timedelta(hours=random.randint(24, 48))

        try:
            with transaction.atomic():
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='LIS',
                    job_type=req['job_type'],
                    ocs_status=ocs_status,
                    priority=req['priority'],
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                    accepted_at=timestamps['accepted_at'],
                    in_progress_at=timestamps['in_progress_at'],
                    result_ready_at=timestamps['result_ready_at'],
                    confirmed_at=timestamps['confirmed_at'],
                )

                created_count += 1
                print(f"  - LIS 요청 생성: {ocs.ocs_id} ({req['job_type']}) - {ocs_status}")

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS LIS 요청 생성: {created_count}건")
    print(f"  현재 전체 OCS(LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    return True


def print_summary():
    """데이터 요약 출력"""
    print("\n" + "="*60)
    print("확장 더미 데이터 생성 완료!")
    print("="*60)

    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from apps.prescriptions.models import Prescription, PrescriptionItem
    from apps.ocs.models import OCS

    today = timezone.now().date()

    print(f"\n[통계]")
    print(f"  - 전체 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 전체 진료: {Encounter.objects.count()}건")
    print(f"  - 오늘 예약 진료: {Encounter.objects.filter(admission_date__date=today, status='scheduled').count()}건")
    print(f"  - 전체 처방: {Prescription.objects.count()}건")
    print(f"  - 전체 처방 항목: {PrescriptionItem.objects.count()}건")
    print(f"  - OCS (RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  - OCS (LIS): {OCS.objects.filter(job_role='LIS').count()}건")


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

    # 5. OCS RIS 요청 생성 (30개)
    create_ocs_ris_requests(target_count=30)

    # 6. OCS LIS 요청 생성 (30개)
    create_ocs_lis_requests(target_count=30)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
