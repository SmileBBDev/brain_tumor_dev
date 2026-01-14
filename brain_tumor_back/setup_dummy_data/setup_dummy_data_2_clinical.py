#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (2/3) - 임상 데이터

이 스크립트는 임상 관련 더미 데이터를 생성합니다:
- 환자 50명
- 진료(Encounter) 20건
- OCS (RIS) 30건 + ImagingStudy
- OCS (LIS) 20건
- AI 모델 3개
- 환자 주의사항
- 치료 계획 15건 + 세션
- 경과 추적 25건
- AI 추론 요청 10건
- 처방전 20건 + 처방 항목 ~60건

사용법:
    python setup_dummy_data_2_clinical.py          # 기존 데이터 유지, 부족분만 추가
    python setup_dummy_data_2_clinical.py --reset  # 임상 데이터만 삭제 후 새로 생성
    python setup_dummy_data_2_clinical.py --force  # 목표 수량 이상이어도 강제 추가

선행 조건:
    python setup_dummy_data_1_base.py     # 기본 더미 데이터 (역할/사용자/메뉴)
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


# ============================================================
# 선행 조건 확인
# ============================================================

def check_prerequisites():
    """선행 조건 확인"""
    print("\n[0단계] 선행 조건 확인...")

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role

    User = get_user_model()

    # 역할 확인
    if not Role.objects.exists():
        print("[ERROR] 역할(Role)이 없습니다.")
        print("  먼저 실행하세요: python setup_dummy_data_1_base.py")
        return False

    # 사용자 확인
    if not User.objects.exists():
        print("[ERROR] 사용자가 없습니다.")
        print("  먼저 실행하세요: python setup_dummy_data_1_base.py")
        return False

    # DOCTOR 역할 사용자 확인
    if not User.objects.filter(role__code='DOCTOR').exists():
        print("[WARNING] DOCTOR 역할 사용자가 없습니다. 첫 번째 사용자를 사용합니다.")

    print("[OK] 선행 조건 충족")
    return True


# ============================================================
# 환자 데이터 (from 1_base.py - 7,8,9,10단계)
# ============================================================

def create_dummy_patients(target_count=50, force=False):
    """더미 환자 데이터 생성"""
    print(f"\n[1단계] 환자 데이터 생성 (목표: {target_count}명)...")

    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = Patient.objects.filter(is_deleted=False).count()
    if existing_count >= target_count and not force:
        print(f"[SKIP] 이미 {existing_count}명의 환자가 존재합니다.")
        return True

    # 등록자 (슈퍼유저 또는 첫 번째 사용자)
    registered_by = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not registered_by:
        print("[ERROR] 사용자가 없습니다.")
        return False

    # 더미 환자 데이터 (50명)
    dummy_patients = [
        {"name": "김철수", "birth_date": timezone.now().date() - timedelta(days=365*45), "gender": "M", "phone": "010-1234-5678", "ssn": "7801011234567", "blood_type": "A+", "allergies": ["페니실린"], "chronic_diseases": ["고혈압"], "address": "서울특별시 강남구 테헤란로 123"},
        {"name": "이영희", "birth_date": timezone.now().date() - timedelta(days=365*38), "gender": "F", "phone": "010-2345-6789", "ssn": "8603151234568", "blood_type": "B+", "allergies": [], "chronic_diseases": ["당뇨"], "address": "서울특별시 서초구 서초대로 456"},
        {"name": "박민수", "birth_date": timezone.now().date() - timedelta(days=365*52), "gender": "M", "phone": "010-3456-7890", "ssn": "7205201234569", "blood_type": "O+", "allergies": ["조영제"], "chronic_diseases": ["고혈압", "당뇨"], "address": "경기도 성남시 분당구 판교로 789"},
        {"name": "최지은", "birth_date": timezone.now().date() - timedelta(days=365*29), "gender": "F", "phone": "010-4567-8901", "ssn": "9506101234560", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 송파구 올림픽로 321"},
        {"name": "정현우", "birth_date": timezone.now().date() - timedelta(days=365*61), "gender": "M", "phone": "010-5678-9012", "ssn": "6309251234561", "blood_type": "A-", "allergies": ["아스피린"], "chronic_diseases": ["고혈압", "고지혈증"], "address": "서울특별시 마포구 월드컵로 654"},
        {"name": "강미라", "birth_date": timezone.now().date() - timedelta(days=365*34), "gender": "F", "phone": "010-6789-0123", "ssn": "9002051234562", "blood_type": "B-", "allergies": [], "chronic_diseases": [], "address": "인천광역시 연수구 센트럴로 987"},
        {"name": "윤서준", "birth_date": timezone.now().date() - timedelta(days=365*47), "gender": "M", "phone": "010-7890-1234", "ssn": "7707151234563", "blood_type": "O-", "allergies": ["설파제"], "chronic_diseases": [], "address": "경기도 고양시 일산동구 중앙로 147"},
        {"name": "임수진", "birth_date": timezone.now().date() - timedelta(days=365*55), "gender": "F", "phone": "010-8901-2345", "ssn": "6912201234564", "blood_type": "AB-", "allergies": ["페니실린", "조영제"], "chronic_diseases": ["당뇨", "고혈압"], "address": "서울특별시 강동구 천호대로 258"},
        {"name": "한지우", "birth_date": timezone.now().date() - timedelta(days=365*26), "gender": "O", "phone": "010-9012-3456", "ssn": "9808301234565", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 관악구 관악로 369"},
        {"name": "오민지", "birth_date": timezone.now().date() - timedelta(days=365*42), "gender": "F", "phone": "010-0123-4567", "ssn": "8204101234566", "blood_type": "B+", "allergies": [], "chronic_diseases": ["고지혈증"], "address": "경기도 수원시 영통구 광교로 741"},
        {"name": "서동훈", "birth_date": timezone.now().date() - timedelta(days=365*58), "gender": "M", "phone": "010-1111-2222", "ssn": "6605121234567", "blood_type": "A+", "allergies": [], "chronic_diseases": ["고혈압"], "address": "부산광역시 해운대구 해운대로 100"},
        {"name": "배수연", "birth_date": timezone.now().date() - timedelta(days=365*31), "gender": "F", "phone": "010-2222-3333", "ssn": "9303152234567", "blood_type": "O+", "allergies": ["페니실린"], "chronic_diseases": [], "address": "대구광역시 수성구 수성로 200"},
        {"name": "조성민", "birth_date": timezone.now().date() - timedelta(days=365*49), "gender": "M", "phone": "010-3333-4444", "ssn": "7508203234567", "blood_type": "B+", "allergies": [], "chronic_diseases": ["당뇨", "고지혈증"], "address": "광주광역시 서구 상무대로 300"},
        {"name": "신예린", "birth_date": timezone.now().date() - timedelta(days=365*27), "gender": "F", "phone": "010-4444-5555", "ssn": "9707154234567", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "대전광역시 유성구 대학로 400"},
        {"name": "권도현", "birth_date": timezone.now().date() - timedelta(days=365*65), "gender": "M", "phone": "010-5555-6666", "ssn": "5909205234567", "blood_type": "A-", "allergies": ["조영제", "아스피린"], "chronic_diseases": ["고혈압", "당뇨", "고지혈증"], "address": "울산광역시 남구 삼산로 500"},
        {"name": "황지현", "birth_date": timezone.now().date() - timedelta(days=365*36), "gender": "F", "phone": "010-6666-7777", "ssn": "8804156234567", "blood_type": "O-", "allergies": [], "chronic_diseases": [], "address": "경기도 용인시 수지구 포은대로 600"},
        {"name": "안재호", "birth_date": timezone.now().date() - timedelta(days=365*53), "gender": "M", "phone": "010-7777-8888", "ssn": "7102207234567", "blood_type": "B-", "allergies": ["설파제"], "chronic_diseases": ["고혈압"], "address": "경기도 화성시 동탄대로 700"},
        {"name": "문서아", "birth_date": timezone.now().date() - timedelta(days=365*24), "gender": "F", "phone": "010-8888-9999", "ssn": "0001158234567", "blood_type": "AB-", "allergies": [], "chronic_diseases": [], "address": "서울특별시 노원구 동일로 800"},
        {"name": "송준혁", "birth_date": timezone.now().date() - timedelta(days=365*44), "gender": "M", "phone": "010-9999-0000", "ssn": "8007209234567", "blood_type": "A+", "allergies": [], "chronic_diseases": ["당뇨"], "address": "서울특별시 영등포구 여의대로 900"},
        {"name": "류하은", "birth_date": timezone.now().date() - timedelta(days=365*33), "gender": "F", "phone": "010-1234-0000", "ssn": "9106150234568", "blood_type": "O+", "allergies": ["페니실린"], "chronic_diseases": [], "address": "경기도 성남시 중원구 성남대로 1000"},
        {"name": "장태웅", "birth_date": timezone.now().date() - timedelta(days=365*57), "gender": "M", "phone": "010-2345-0000", "ssn": "6703201234568", "blood_type": "B+", "allergies": [], "chronic_diseases": ["고혈압", "고지혈증"], "address": "인천광역시 남동구 구월로 1100"},
        {"name": "노은지", "birth_date": timezone.now().date() - timedelta(days=365*29), "gender": "F", "phone": "010-3456-0000", "ssn": "9509152234568", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "부산광역시 부산진구 중앙대로 1200"},
        {"name": "하승우", "birth_date": timezone.now().date() - timedelta(days=365*41), "gender": "M", "phone": "010-4567-0000", "ssn": "8310203234568", "blood_type": "O-", "allergies": ["조영제"], "chronic_diseases": ["당뇨"], "address": "대구광역시 달서구 달구벌대로 1300"},
        {"name": "전소희", "birth_date": timezone.now().date() - timedelta(days=365*38), "gender": "F", "phone": "010-5678-0000", "ssn": "8605154234568", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "광주광역시 북구 용봉로 1400"},
        {"name": "곽민재", "birth_date": timezone.now().date() - timedelta(days=365*62), "gender": "M", "phone": "010-6789-0000", "ssn": "6204205234568", "blood_type": "B-", "allergies": ["아스피린"], "chronic_diseases": ["고혈압", "당뇨"], "address": "대전광역시 서구 둔산로 1500"},
        {"name": "우다인", "birth_date": timezone.now().date() - timedelta(days=365*25), "gender": "F", "phone": "010-7890-0000", "ssn": "9908156234568", "blood_type": "A-", "allergies": [], "chronic_diseases": [], "address": "울산광역시 중구 성남로 1600"},
        {"name": "남기훈", "birth_date": timezone.now().date() - timedelta(days=365*50), "gender": "M", "phone": "010-8901-0000", "ssn": "7406207234568", "blood_type": "O+", "allergies": [], "chronic_diseases": ["고지혈증"], "address": "세종특별자치시 한누리대로 1700"},
        {"name": "심유나", "birth_date": timezone.now().date() - timedelta(days=365*35), "gender": "F", "phone": "010-9012-0000", "ssn": "8902158234568", "blood_type": "B+", "allergies": ["설파제"], "chronic_diseases": [], "address": "제주특별자치도 제주시 연동로 1800"},
        {"name": "엄태식", "birth_date": timezone.now().date() - timedelta(days=365*68), "gender": "M", "phone": "010-0123-0000", "ssn": "5607209234568", "blood_type": "AB-", "allergies": ["페니실린", "아스피린"], "chronic_diseases": ["고혈압", "당뇨", "고지혈증"], "address": "강원도 춘천시 중앙로 1900"},
        {"name": "차준영", "birth_date": timezone.now().date() - timedelta(days=365*40), "gender": "M", "phone": "010-1122-3344", "ssn": "8405201234569", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "경상북도 포항시 북구 중앙로 2000"},
        # 확장 환자 20명
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

    created_count = 0
    skipped_count = 0

    for patient_data in dummy_patients:
        try:
            # SSN 중복 확인
            if Patient.objects.filter(ssn=patient_data['ssn']).exists():
                skipped_count += 1
                continue

            # 랜덤 중증도 할당
            severity_choices = ['normal', 'normal', 'normal', 'mild', 'mild', 'moderate', 'severe', 'critical']
            severity = random.choice(severity_choices)

            patient = Patient.objects.create(
                registered_by=registered_by,
                status='active',
                severity=severity,
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


def create_dummy_encounters(target_count=20, force=False):
    """더미 진료 데이터 생성"""
    print(f"\n[2단계] 진료 데이터 생성 (목표: {target_count}건)...")

    from apps.encounters.models import Encounter
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = Encounter.objects.count()
    if existing_count >= target_count and not force:
        print(f"[SKIP] 이미 {existing_count}건의 진료가 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 활성 환자가 없습니다.")
        return False

    if not doctors:
        print("[WARNING] DOCTOR 역할 사용자가 없습니다. 첫 번째 사용자를 사용합니다.")
        doctors = list(User.objects.all()[:1])

    encounter_types = ['outpatient', 'inpatient', 'emergency']
    statuses = ['scheduled', 'in_progress', 'completed', 'cancelled']
    departments = ['neurology', 'neurosurgery']

    chief_complaints = [
        '두통이 심해요', '어지러움증이 계속됩니다', '손발 저림 증상',
        '기억력 감퇴', '수면 장애', '편두통', '목 통증',
        '시야 흐림', '균형 감각 이상', '근육 경련', '발작 증세'
    ]

    primary_diagnoses = [
        '뇌종양 의심', '편두통', '뇌졸중', '파킨슨병',
        '치매', '간질', '다발성 경화증', '신경통'
    ]

    # SOAP 노트 샘플 데이터
    subjective_samples = [
        '3일 전부터 지속되는 두통, 아침에 더 심함',
        '일주일간 어지러움 증상, 구역감 동반',
        '양손 저림 증상, 특히 야간에 심해짐',
        '최근 건망증이 심해졌다고 호소',
        '잠들기 어렵고 자주 깸, 피로감 호소',
        '우측 관자놀이 쪽 박동성 두통',
        '경추 부위 통증, 고개 돌릴 때 악화',
    ]

    objective_samples = [
        'BP 130/85, HR 72, BT 36.5',
        '신경학적 검사 정상, 경부 강직 없음',
        '동공 반사 정상, 안구 운동 정상',
        'Romberg test 양성, 보행 시 불안정',
        'MMT 정상, DTR 정상, 병적 반사 없음',
        'GCS 15, 의식 명료, 지남력 정상',
        '뇌 MRI: T2 고신호 병변 확인',
    ]

    assessment_samples = [
        '긴장성 두통 의심, R/O 편두통',
        '말초성 현훈 vs 중추성 현훈 감별 필요',
        '수근관 증후군 의심',
        '경도 인지장애 가능성, 치매 스크리닝 필요',
        '불면증, 수면 무호흡 가능성',
        '뇌종양 의심, 추가 검사 필요',
        '경추 디스크 탈출증 의심',
    ]

    plan_samples = [
        '뇌 MRI 촬영, 진통제 처방, 2주 후 재진',
        '청력검사, 전정기능검사 예정, 어지럼증 약물 처방',
        '신경전도검사 의뢰, 보존적 치료',
        '인지기능검사, 혈액검사 (갑상선, B12)',
        '수면다원검사 의뢰, 수면위생 교육',
        'MRI 추적검사, 신경외과 협진',
        '물리치료 의뢰, NSAIDs 처방',
    ]

    created_count = 0

    for i in range(target_count):
        days_ago = random.randint(0, 60)
        admission_date = timezone.now() - timedelta(days=days_ago)
        encounter_type = random.choice(encounter_types)

        if days_ago > 30:
            status = random.choice(['completed', 'cancelled'])
        elif days_ago > 7:
            status = random.choice(['in_progress', 'completed'])
        else:
            status = random.choice(statuses)

        discharge_date = None
        if status == 'completed':
            if encounter_type == 'outpatient':
                discharge_days = random.choice([0, 1])
            elif encounter_type == 'inpatient':
                discharge_days = random.randint(1, 14)
            else:
                discharge_days = random.randint(0, 7)
            discharge_date = admission_date + timedelta(days=discharge_days)
        elif status == 'cancelled' and random.choice([True, False]):
            discharge_date = admission_date

        # 완료된 진료는 SOAP 노트 작성
        soap_data = {}
        if status in ['completed', 'in_progress']:
            soap_data = {
                'subjective': random.choice(subjective_samples),
                'objective': random.choice(objective_samples),
                'assessment': random.choice(assessment_samples),
                'plan': random.choice(plan_samples),
            }

        try:
            encounter = Encounter.objects.create(
                patient=random.choice(patients),
                encounter_type=encounter_type,
                status=status,
                attending_doctor=random.choice(doctors),
                department=random.choice(departments),
                admission_date=admission_date,
                discharge_date=discharge_date,
                chief_complaint=random.choice(chief_complaints),
                primary_diagnosis=random.choice(primary_diagnoses),
                secondary_diagnoses=random.sample(['고혈압', '당뇨', '고지혈증'], random.randint(0, 2)),
                **soap_data,
            )
            created_count += 1
        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 진료 생성: {created_count}건")

    # 오늘 예약 진료 3건 생성 (금일 예약 환자 목록 테스트용)
    print("\n[2-1단계] 오늘 예약 진료 생성...")
    today_scheduled_count = Encounter.objects.filter(
        admission_date__date=timezone.now().date(),
        status='scheduled'
    ).count()

    # 예약 시간 목록
    scheduled_times = [dt_time(9, 0), dt_time(10, 30), dt_time(14, 0), dt_time(15, 30), dt_time(16, 0)]

    if today_scheduled_count < 3:
        for i in range(3 - today_scheduled_count):
            try:
                Encounter.objects.create(
                    patient=random.choice(patients),
                    attending_doctor=random.choice(doctors),
                    admission_date=timezone.now(),
                    scheduled_time=scheduled_times[i % len(scheduled_times)],
                    status='scheduled',
                    encounter_type='outpatient',
                    department=random.choice(departments),
                    chief_complaint=random.choice(['정기 진료', '추적 검사', '상담', '재진'])
                )
            except Exception as e:
                print(f"  오류: {e}")
        print(f"[OK] 오늘 예약 진료: {3 - today_scheduled_count}건 추가 생성")
    else:
        print(f"[SKIP] 오늘 예약 진료 이미 {today_scheduled_count}건 존재")

    print(f"  현재 전체 진료: {Encounter.objects.count()}건")
    return True


def create_dummy_imaging_with_ocs(num_orders=30, force=False):
    """더미 영상 검사 데이터 생성 (OCS 통합 버전)"""
    print(f"\n[3단계] 영상 검사 데이터 생성 - OCS 통합 (목표: {num_orders}건)...")

    from apps.ocs.models import OCS
    from apps.imaging.models import ImagingStudy
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_ocs = OCS.objects.filter(job_role='RIS').count()
    if existing_ocs >= num_orders and not force:
        print(f"[SKIP] 이미 {existing_ocs}건의 RIS 오더가 존재합니다.")
        return True

    # 필요한 데이터 - 환자와 담당 의사 관계가 있는 진료 기록만 사용
    encounters = list(Encounter.objects.filter(
        attending_doctor__isnull=False,
        patient__is_deleted=False
    ).select_related('patient', 'attending_doctor'))
    radiologists = list(User.objects.filter(role__code__in=['RIS', 'DOCTOR']))

    if not encounters:
        print("[ERROR] 담당 의사가 있는 진료 기록이 없습니다.")
        return False

    if not radiologists:
        radiologists = list(User.objects.filter(role__code='DOCTOR'))

    # 뇌종양 CDSS에 필요한 영상 검사만
    modalities = ['MRI', 'CT', 'PET']  # X-RAY 제거
    body_parts = ['Brain', 'Head']  # 뇌종양 관련 부위만
    ocs_statuses = ['ORDERED', 'ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']
    priorities = ['urgent', 'normal']
    clinical_indications = ['brain tumor evaluation', 'follow-up', 'post-op check', 'treatment response']

    created_count = 0

    for i in range(num_orders):
        # 진료 기록에서 환자와 담당 의사 관계 가져오기
        encounter = random.choice(encounters)
        patient = encounter.patient
        doctor = encounter.attending_doctor  # 환자의 담당 의사가 요청
        modality = random.choice(modalities)
        body_part = random.choice(body_parts)

        days_ago = random.randint(0, 90)
        ocs_status = random.choice(ocs_statuses)

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(radiologists)

        # doctor_request 데이터
        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": f"{random.choice(clinical_indications)} - {patient.name}",
            "request_detail": f"{modality} {body_part} 촬영 요청",
            "special_instruction": random.choice(["", "조영제 사용", "조영제 없이", "긴급"]),
        }

        # worker_result 데이터 (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            tumor_detected = random.random() < 0.3
            lobes = ['frontal', 'temporal', 'parietal', 'occipital']
            hemispheres = ['left', 'right']

            worker_result = {
                "_template": "RIS",
                "_version": "1.0",
                "_confirmed": ocs_status == 'CONFIRMED',
                "findings": "Mass lesion identified." if tumor_detected else "No acute intracranial abnormality.",
                "impression": "Brain tumor suspected." if tumor_detected else "Normal study.",
                "recommendation": "Further evaluation recommended." if tumor_detected else "",
                "tumor": {
                    "detected": tumor_detected,
                    "location": {"lobe": random.choice(lobes), "hemisphere": random.choice(hemispheres)} if tumor_detected else {},
                    "size": {"max_diameter_cm": round(random.uniform(1.0, 4.0), 1), "volume_cc": round(random.uniform(2.0, 30.0), 1)} if tumor_detected else {}
                },
                "dicom": {
                    "study_uid": f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1000, 9999)}",
                    "series_count": random.randint(1, 5),
                    "instance_count": random.randint(20, 200)
                },
                "work_notes": []
            }

        try:
            with transaction.atomic():
                # OCS 생성
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='RIS',
                    job_type=modality,
                    ocs_status=ocs_status,
                    priority=random.choice(priorities),
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                )

                # ImagingStudy 생성 (OCS에 연결)
                scheduled_at = None
                performed_at = None

                if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    scheduled_at = timezone.now() - timedelta(days=days_ago) + timedelta(days=random.randint(1, 3))

                if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    performed_at = scheduled_at + timedelta(hours=random.randint(1, 24)) if scheduled_at else None

                study = ImagingStudy.objects.create(
                    ocs=ocs,
                    modality=modality,
                    body_part=body_part,
                    study_uid=worker_result.get('dicom', {}).get('study_uid') if worker_result else None,
                    series_count=worker_result.get('dicom', {}).get('series_count', 0) if worker_result else 0,
                    instance_count=worker_result.get('dicom', {}).get('instance_count', 0) if worker_result else 0,
                    scheduled_at=scheduled_at,
                    performed_at=performed_at,
                )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS + ImagingStudy 생성: {created_count}건")
    print(f"  현재 전체 OCS(RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  현재 전체 ImagingStudy: {ImagingStudy.objects.count()}건")
    return True


def create_dummy_lis_orders(num_orders=30, force=False):
    """더미 LIS (검사) 오더 생성"""
    print(f"\n[4단계] 검사 오더 데이터 생성 - LIS (목표: {num_orders}건)...")

    from apps.ocs.models import OCS
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_ocs = OCS.objects.filter(job_role='LIS').count()
    if existing_ocs >= num_orders and not force:
        print(f"[SKIP] 이미 {existing_ocs}건의 LIS 오더가 존재합니다.")
        return True

    # 필요한 데이터 - 환자와 담당 의사 관계가 있는 진료 기록만 사용
    encounters = list(Encounter.objects.filter(
        attending_doctor__isnull=False,
        patient__is_deleted=False
    ).select_related('patient', 'attending_doctor'))
    lab_workers = list(User.objects.filter(role__code__in=['LIS', 'DOCTOR']))

    if not encounters:
        print("[ERROR] 담당 의사가 있는 진료 기록이 없습니다.")
        return False

    if not lab_workers:
        lab_workers = list(User.objects.filter(role__code='DOCTOR'))

    # 뇌종양 CDSS에 필요한 검사만 (8종류)
    test_types = [
        # 혈액검사 (4) - 항암치료/수술 전 필수
        'CBC',            # 일반혈액검사
        'CMP',            # 종합대사패널 (간/신기능 포함)
        'Coagulation',    # 응고검사
        'Tumor Markers',  # 종양표지자
        # 유전자검사 (3) - 뇌종양 분류/예후 판정
        'GENE_PANEL',     # IDH1, MGMT, TP53, EGFR
        'RNA_SEQ',        # RNA 발현 분석
        'DNA_SEQ',        # DNA 변이 분석
        # 단백질검사 (1) - 뇌손상/종양 마커
        'BIOMARKER',      # GFAP, S100B, NSE
    ]
    ocs_statuses = ['ORDERED', 'ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']
    priorities = ['urgent', 'normal']

    created_count = 0

    for i in range(num_orders):
        # 진료 기록에서 환자와 담당 의사 관계 가져오기
        encounter = random.choice(encounters)
        patient = encounter.patient
        doctor = encounter.attending_doctor  # 환자의 담당 의사가 요청
        test_type = random.choice(test_types)

        # 날짜 분포: 1주일 ~ 6개월 (180일)
        days_ago = random.randint(0, 180)

        # 상태 결정: 오래된 데이터일수록 CONFIRMED 확률 높음
        if days_ago > 90:  # 3개월 이상
            ocs_status = random.choice(['CONFIRMED', 'CONFIRMED', 'CONFIRMED', 'CANCELLED'])
        elif days_ago > 30:  # 1개월 이상
            ocs_status = random.choice(['RESULT_READY', 'CONFIRMED', 'CONFIRMED'])
        elif days_ago > 7:  # 1주일 이상
            ocs_status = random.choice(['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED'])
        else:  # 최근 1주일
            ocs_status = random.choice(ocs_statuses)

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(lab_workers)

        # doctor_request 데이터
        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": f"{patient.name} - 정기검사",
            "request_detail": f"{test_type} 검사 요청",
            "special_instruction": random.choice(["", "공복 필요", "아침 첫 소변", ""]),
        }

        # worker_result 데이터 (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            is_abnormal = random.random() < 0.2

            # 검사 결과 샘플
            test_results = []
            if test_type == 'CBC':
                test_results = [
                    {"code": "WBC", "name": "백혈구", "value": str(round(random.uniform(4.0, 11.0), 1)), "unit": "10^3/uL", "reference": "4.0-11.0", "is_abnormal": False},
                    {"code": "RBC", "name": "적혈구", "value": str(round(random.uniform(4.0, 6.0), 2)), "unit": "10^6/uL", "reference": "4.0-6.0", "is_abnormal": False},
                    {"code": "HGB", "name": "혈색소", "value": str(round(random.uniform(12.0, 17.0), 1)), "unit": "g/dL", "reference": "12.0-17.0", "is_abnormal": False},
                    {"code": "PLT", "name": "혈소판", "value": str(random.randint(150, 400)), "unit": "10^3/uL", "reference": "150-400", "is_abnormal": False},
                ]
            elif test_type == 'CMP':
                # 종합대사패널 (간/신기능 포함)
                test_results = [
                    {"code": "GLU", "name": "혈당", "value": str(random.randint(70, 110)), "unit": "mg/dL", "reference": "70-110", "is_abnormal": False},
                    {"code": "BUN", "name": "요소질소", "value": str(round(random.uniform(7, 20), 1)), "unit": "mg/dL", "reference": "7-20", "is_abnormal": False},
                    {"code": "CRE", "name": "크레아티닌", "value": str(round(random.uniform(0.6, 1.2), 2)), "unit": "mg/dL", "reference": "0.6-1.2", "is_abnormal": False},
                    {"code": "AST", "name": "AST", "value": str(random.randint(10, 40)), "unit": "U/L", "reference": "10-40", "is_abnormal": False},
                    {"code": "ALT", "name": "ALT", "value": str(random.randint(7, 56)), "unit": "U/L", "reference": "7-56", "is_abnormal": False},
                ]
            elif test_type == 'Coagulation':
                # 응고검사 (수술 전 필수)
                test_results = [
                    {"code": "PT", "name": "프로트롬빈시간", "value": str(round(random.uniform(11, 13.5), 1)), "unit": "sec", "reference": "11-13.5", "is_abnormal": False},
                    {"code": "INR", "name": "INR", "value": str(round(random.uniform(0.9, 1.1), 2)), "unit": "", "reference": "0.9-1.1", "is_abnormal": False},
                    {"code": "aPTT", "name": "활성화부분트롬보플라스틴시간", "value": str(round(random.uniform(25, 35), 1)), "unit": "sec", "reference": "25-35", "is_abnormal": False},
                ]
            elif test_type == 'Tumor Markers':
                cea_val = round(random.uniform(0.5, 5.0), 2) if not is_abnormal else round(random.uniform(5.1, 20.0), 2)
                afp_val = round(random.uniform(0.5, 10.0), 2) if not is_abnormal else round(random.uniform(10.1, 50.0), 2)
                test_results = [
                    {"code": "CEA", "name": "암배아항원", "value": str(cea_val), "unit": "ng/mL", "reference": "0-5.0", "is_abnormal": cea_val > 5.0},
                    {"code": "AFP", "name": "알파태아단백", "value": str(afp_val), "unit": "ng/mL", "reference": "0-10.0", "is_abnormal": afp_val > 10.0},
                ]
            elif test_type in ['GENE_PANEL', 'RNA_SEQ', 'DNA_SEQ']:
                # 유전자 검사 결과
                gene_mutations = [
                    {"gene_name": "IDH1", "mutation_type": "R132H" if is_abnormal else "Wild Type", "status": "Mutant" if is_abnormal else "Normal", "allele_frequency": round(random.uniform(0.1, 0.5), 2) if is_abnormal else None, "clinical_significance": "Favorable prognosis" if is_abnormal else "N/A"},
                    {"gene_name": "TP53", "mutation_type": random.choice(["Missense", "Nonsense", "Wild Type"]), "status": random.choice(["Mutant", "Normal"]), "allele_frequency": round(random.uniform(0.05, 0.3), 2), "clinical_significance": "Variable"},
                    {"gene_name": "MGMT", "mutation_type": "Methylated" if random.random() > 0.5 else "Unmethylated", "status": "Methylated" if random.random() > 0.5 else "Unmethylated", "allele_frequency": None, "clinical_significance": "TMZ response predictor"},
                    {"gene_name": "EGFR", "mutation_type": random.choice(["Amplified", "Normal"]), "status": random.choice(["Amplified", "Normal"]), "allele_frequency": None, "clinical_significance": "GBM marker"},
                ]
                test_results = [{"code": "GENE", "name": "유전자 변이 분석", "value": "분석 완료", "unit": "", "reference": "", "is_abnormal": is_abnormal}]
                worker_result = {
                    "_template": "LIS", "_version": "1.0", "_confirmed": ocs_status == 'CONFIRMED',
                    "test_type": "GENETIC", "test_results": test_results, "gene_mutations": gene_mutations,
                    "summary": "유전자 변이 검출됨" if is_abnormal else "유전자 변이 없음",
                    "interpretation": "IDH1 변이 양성 - 예후 양호" if is_abnormal else "특이 변이 없음", "_custom": {}
                }
            elif test_type == 'BIOMARKER':
                # 단백질 검사 결과
                protein_markers = [
                    {"marker_name": "GFAP", "value": round(random.uniform(0.1, 5.0), 2), "unit": "ng/mL", "reference_range": "0-2.0", "is_abnormal": random.random() > 0.7, "interpretation": "Astrocyte marker"},
                    {"marker_name": "S100B", "value": round(random.uniform(0.01, 0.5), 3), "unit": "ug/L", "reference_range": "0-0.15", "is_abnormal": random.random() > 0.6, "interpretation": "Brain injury marker"},
                    {"marker_name": "NSE", "value": round(random.uniform(5, 25), 1), "unit": "ng/mL", "reference_range": "0-16.3", "is_abnormal": random.random() > 0.7, "interpretation": "Neuroendocrine marker"},
                ]
                test_results = [{"code": "PROT", "name": "단백질 마커 분석", "value": "분석 완료", "unit": "", "reference": "", "is_abnormal": is_abnormal}]
                worker_result = {
                    "_template": "LIS", "_version": "1.0", "_confirmed": ocs_status == 'CONFIRMED',
                    "test_type": "PROTEIN", "test_results": test_results, "protein_markers": protein_markers,
                    "protein": "GFAP, S100B 상승" if is_abnormal else "정상 범위",
                    "summary": "단백질 마커 이상" if is_abnormal else "정상 범위",
                    "interpretation": "뇌종양 관련 마커 상승 소견" if is_abnormal else "특이 소견 없음", "_custom": {}
                }
            else:
                # 일반 검사
                test_results = [
                    {"code": "TEST1", "name": f"{test_type} 항목1", "value": str(round(random.uniform(50, 150), 1)), "unit": "mg/dL", "reference": "50-150", "is_abnormal": False},
                    {"code": "TEST2", "name": f"{test_type} 항목2", "value": str(round(random.uniform(10, 50), 1)), "unit": "U/L", "reference": "10-50", "is_abnormal": False},
                ]

            # GENE/BIOMARKER는 위에서 이미 worker_result 설정됨
            if test_type not in ['GENE_PANEL', 'RNA_SEQ', 'DNA_SEQ', 'BIOMARKER']:
                worker_result = {
                    "_template": "LIS",
                    "_version": "1.0",
                    "_confirmed": ocs_status == 'CONFIRMED',
                    "test_results": test_results,
                    "summary": "이상 소견 있음" if is_abnormal else "정상 범위",
                    "interpretation": "추가 검사 권장" if is_abnormal else "특이 소견 없음",
                    "_custom": {}
                }

        # 타임스탬프 계산
        base_time = timezone.now() - timedelta(days=days_ago)
        timestamps = {
            'accepted_at': None,
            'in_progress_at': None,
            'result_ready_at': None,
            'confirmed_at': None,
            'cancelled_at': None,
        }

        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['accepted_at'] = base_time + timedelta(hours=random.randint(1, 4))

        if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['in_progress_at'] = base_time + timedelta(hours=random.randint(4, 12))

        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            timestamps['result_ready_at'] = base_time + timedelta(hours=random.randint(12, 48))

        if ocs_status == 'CONFIRMED':
            timestamps['confirmed_at'] = base_time + timedelta(hours=random.randint(48, 72))

        if ocs_status == 'CANCELLED':
            timestamps['cancelled_at'] = base_time + timedelta(hours=random.randint(1, 24))

        try:
            with transaction.atomic():
                # OCS 생성
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='LIS',
                    job_type=test_type,
                    ocs_status=ocs_status,
                    priority=random.choice(priorities),
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                    accepted_at=timestamps['accepted_at'],
                    in_progress_at=timestamps['in_progress_at'],
                    result_ready_at=timestamps['result_ready_at'],
                    confirmed_at=timestamps['confirmed_at'],
                    cancelled_at=timestamps['cancelled_at'],
                )
                # created_at은 auto_now_add이므로 별도 업데이트
                OCS.objects.filter(pk=ocs.pk).update(created_at=base_time)
                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS(LIS) 생성: {created_count}건")
    print(f"  현재 전체 OCS(LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    return True


def create_ai_models():
    """AI 모델 시드 데이터 생성"""
    print(f"\n[5단계] AI 모델 데이터 생성...")

    from apps.ai_inference.models import AIModel

    # 기존 데이터 확인
    existing_count = AIModel.objects.count()
    if existing_count >= 3:
        print(f"[SKIP] 이미 {existing_count}개의 AI 모델이 존재합니다.")
        return True

    ai_models_data = [
        {
            "code": "M1",
            "name": "MRI 4-Channel Analysis",
            "description": "MRI 4채널(T1, T2, T1C, FLAIR) 기반 뇌종양 분석 모델",
            "ocs_sources": ["RIS"],
            "required_keys": {
                "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"]
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 300,
                "batch_size": 1,
                "gpu_required": True
            }
        },
        {
            "code": "MG",
            "name": "Genetic Analysis",
            "description": "RNA 시퀀싱 기반 유전자 분석 모델 (MGMT 메틸화, IDH 변이 등)",
            "ocs_sources": ["LIS"],
            "required_keys": {
                "LIS": ["RNA_seq"]
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 600,
                "batch_size": 1,
                "gpu_required": False
            }
        },
        {
            "code": "MM",
            "name": "Multimodal Analysis",
            "description": "MRI + 유전 + 단백질 통합 분석 모델 (종합 예후 예측)",
            "ocs_sources": ["RIS", "LIS"],
            "required_keys": {
                "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"],
                "LIS": ["RNA_seq", "protein"]
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 900,
                "batch_size": 1,
                "gpu_required": True
            }
        }
    ]

    created_count = 0
    for model_data in ai_models_data:
        model, created = AIModel.objects.get_or_create(
            code=model_data["code"],
            defaults=model_data
        )
        if created:
            created_count += 1
            print(f"  생성: {model.code} - {model.name}")
        else:
            print(f"  스킵: {model.code} (이미 존재)")

    print(f"[OK] AI 모델 생성: {created_count}개")
    print(f"  현재 전체 AI 모델: {AIModel.objects.count()}개")
    return True


def create_patient_alerts(force=False):
    """환자 주의사항 더미 데이터 생성"""
    print("\n[6단계] 환자 주의사항 데이터 생성...")

    from apps.patients.models import Patient, PatientAlert
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = PatientAlert.objects.count()
    if existing_count > 0 and not force:
        print(f"[SKIP] 이미 {existing_count}건의 주의사항이 존재합니다.")
        return True

    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    alert_samples = [
        {'alert_type': 'ALLERGY', 'severity': 'HIGH', 'title': '페니실린 알레르기', 'description': '페니실린 계열 항생제 투여 시 아나필락시스 반응 가능'},
        {'alert_type': 'ALLERGY', 'severity': 'HIGH', 'title': '조영제 알레르기', 'description': 'CT/MRI 조영제 투여 시 두드러기, 호흡곤란 발생 이력'},
        {'alert_type': 'ALLERGY', 'severity': 'MEDIUM', 'title': '아스피린 과민반응', 'description': 'NSAIDs 사용 시 주의 필요'},
        {'alert_type': 'CONTRAINDICATION', 'severity': 'HIGH', 'title': '와파린 복용 중', 'description': '항응고제 복용 중 - 출혈 위험'},
        {'alert_type': 'CONTRAINDICATION', 'severity': 'HIGH', 'title': 'MRI 금기', 'description': '심장 박동기 삽입 환자 - MRI 촬영 금지'},
        {'alert_type': 'PRECAUTION', 'severity': 'MEDIUM', 'title': '낙상 주의', 'description': '보행 장애로 인한 낙상 위험'},
        {'alert_type': 'PRECAUTION', 'severity': 'LOW', 'title': '당뇨 환자', 'description': '혈당 관리 필요 - 공복 검사 시 저혈당 주의'},
        {'alert_type': 'OTHER', 'severity': 'LOW', 'title': '보호자 연락 필요', 'description': '중요 결정 시 보호자 동의 필요'},
    ]

    created_count = 0

    # 각 환자에게 0~3개의 주의사항 추가
    for patient in patients:
        num_alerts = random.randint(0, 3)
        if num_alerts == 0:
            continue

        selected_alerts = random.sample(alert_samples, min(num_alerts, len(alert_samples)))
        for alert_data in selected_alerts:
            try:
                PatientAlert.objects.create(
                    patient=patient,
                    alert_type=alert_data['alert_type'],
                    severity=alert_data['severity'],
                    title=alert_data['title'],
                    description=alert_data['description'],
                    is_active=True,
                    created_by=random.choice(doctors),
                )
                created_count += 1
            except Exception as e:
                print(f"  오류: {e}")

    print(f"[OK] 환자 주의사항 생성: {created_count}건")
    print(f"  현재 전체 주의사항: {PatientAlert.objects.count()}건")
    return True


def link_patient_user_account():
    """
    PATIENT 역할 사용자를 환자(Patient) 테이블과 연결

    patient1~5 계정 → 환자 테이블의 김철수, 이영희, 박민수, 최지은, 정현우와 연결
    """
    print("\n[7단계] 환자 계정-환자 테이블 연결...")

    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # PATIENT 역할 사용자 ↔ 환자 이름 매핑 (5명)
    patient_mapping = [
        ('patient1', '김철수'),
        ('patient2', '이영희'),
        ('patient3', '박민수'),
        ('patient4', '최지은'),
        ('patient5', '정현우'),
    ]

    linked_count = 0
    skipped_count = 0

    for login_id, patient_name in patient_mapping:
        # 사용자 확인
        patient_user = User.objects.filter(login_id=login_id, role__code='PATIENT').first()
        if not patient_user:
            print(f"  [SKIP] {login_id} 사용자가 없거나 PATIENT 역할이 아닙니다.")
            skipped_count += 1
            continue

        # 이미 연결된 환자가 있는지 확인
        if Patient.objects.filter(user=patient_user).exists():
            linked_patient = Patient.objects.get(user=patient_user)
            print(f"  [OK] 이미 연결됨: {login_id} → {linked_patient.name}")
            skipped_count += 1
            continue

        # 환자 찾기
        patient = Patient.objects.filter(name=patient_name, is_deleted=False, user__isnull=True).first()
        if not patient:
            print(f"  [SKIP] {patient_name} 환자가 없거나 이미 연결됨")
            skipped_count += 1
            continue

        # 연결
        patient.user = patient_user
        patient.save()
        linked_count += 1
        print(f"  [OK] 연결: {login_id} → {patient.name} ({patient.patient_number})")

    print(f"[OK] 환자 계정 연결 완료 (연결: {linked_count}건, 스킵: {skipped_count}건)")
    print(f"     테스트 계정: patient1~5 / patient1001~patient5001")
    return True


# ============================================================
# 치료/경과/AI 요청 (from 2_add.py)
# ============================================================

def create_dummy_treatment_plans(num_plans=15, force=False):
    """더미 치료 계획 데이터 생성"""
    print(f"\n[8단계] 치료 계획 데이터 생성 (목표: {num_plans}건)...")

    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = TreatmentPlan.objects.count()
    if existing_count >= num_plans and not force:
        print(f"[SKIP] 이미 {existing_count}건의 치료 계획이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    # 실제 모델의 choices 사용
    treatment_types = [choice[0] for choice in TreatmentPlan.TreatmentType.choices]
    treatment_goals = [choice[0] for choice in TreatmentPlan.TreatmentGoal.choices]
    statuses = [choice[0] for choice in TreatmentPlan.Status.choices]

    plan_summaries = {
        'surgery': ['뇌종양 절제술 시행 예정', '내시경 수술 계획', '감압술 시행', '조직 검사 후 치료 방향 결정'],
        'radiation': ['전뇌 방사선 치료 진행', '정위적 방사선 수술 계획', 'IMRT 치료 시행', '양성자 치료 고려'],
        'chemotherapy': ['테모졸로마이드 치료 시작', '베바시주맙 치료 진행', '복합 항암 요법 적용', '면역 항암 치료 시행'],
        'observation': ['정기 MRI 추적 관찰', '증상 모니터링 지속', '경과 관찰 후 치료 결정'],
        'combined': ['수술 후 방사선+항암 병합', '동시 화학방사선 요법 진행', '복합 치료 프로토콜 적용']
    }

    created_count = 0

    for i in range(num_plans):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        treatment_type = random.choice(treatment_types)
        treatment_goal = random.choice(treatment_goals)
        status = random.choice(statuses)

        days_ago = random.randint(0, 180)
        start_date = timezone.now().date() - timedelta(days=days_ago)

        end_date = None
        actual_start = None
        actual_end = None

        if status == 'completed':
            actual_start = start_date
            actual_end = start_date + timedelta(days=random.randint(14, 90))
            end_date = actual_end
        elif status == 'in_progress':
            actual_start = start_date
            end_date = start_date + timedelta(days=random.randint(30, 120))
        elif status == 'cancelled':
            end_date = start_date + timedelta(days=random.randint(7, 30))
        elif status == 'planned':
            end_date = start_date + timedelta(days=random.randint(30, 90))

        try:
            with transaction.atomic():
                plan = TreatmentPlan.objects.create(
                    patient=patient,
                    treatment_type=treatment_type,
                    treatment_goal=treatment_goal,
                    plan_summary=random.choice(plan_summaries[treatment_type]),
                    planned_by=doctor,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    actual_start_date=actual_start,
                    actual_end_date=actual_end,
                    notes=f"담당의: {doctor.name}" if random.random() < 0.3 else ""
                )

                # 치료 세션 생성 (방사선, 항암의 경우)
                if treatment_type in ['radiation', 'chemotherapy'] and status in ['in_progress', 'completed']:
                    num_sessions = random.randint(3, 8)
                    session_statuses = [choice[0] for choice in TreatmentSession.Status.choices]

                    for j in range(num_sessions):
                        session_datetime = timezone.now() - timedelta(days=days_ago - j * 7)
                        if session_datetime < timezone.now():
                            session_status = 'completed'
                        else:
                            session_status = 'scheduled'

                        TreatmentSession.objects.create(
                            treatment_plan=plan,
                            session_number=j + 1,
                            session_date=session_datetime,
                            performed_by=doctor if session_status == 'completed' else None,
                            status=session_status,
                            session_note=f"{j + 1}회차 치료 진행" if session_status == 'completed' else ""
                        )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 치료 계획 생성: {created_count}건")
    print(f"  현재 전체 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  현재 전체 치료 세션: {TreatmentSession.objects.count()}건")
    return True


def create_dummy_followups(num_followups=25, force=False):
    """더미 경과 추적 데이터 생성"""
    print(f"\n[9단계] 경과 추적 데이터 생성 (목표: {num_followups}건)...")

    from apps.followup.models import FollowUp
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = FollowUp.objects.count()
    if existing_count >= num_followups and not force:
        print(f"[SKIP] 이미 {existing_count}건의 경과 기록이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    # 실제 모델의 choices 사용
    followup_types = [choice[0] for choice in FollowUp.FollowUpType.choices]
    clinical_statuses = [choice[0] for choice in FollowUp.ClinicalStatus.choices]

    symptoms_list = [
        ['두통'], ['어지러움'], ['시야 흐림'], ['손발 저림'],
        [], ['피로감'], ['기억력 저하'], ['수면 장애'],
        ['오심', '구토'], ['경련']
    ]

    notes_list = [
        '전반적으로 안정적인 상태 유지',
        '영상 소견상 변화 없음',
        '치료 반응 양호',
        '경미한 증상 악화 관찰',
        '추가 검사 필요',
        '현 치료 계획 유지 권고',
        '다음 정기 검진 예정',
        'MRI 추적 검사 예정'
    ]

    created_count = 0

    for i in range(num_followups):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        followup_type = random.choice(followup_types)
        clinical_status = random.choice(clinical_statuses)

        days_ago = random.randint(0, 365)
        followup_datetime = timezone.now() - timedelta(days=days_ago)

        # 다음 방문일 (50% 확률로 설정)
        next_followup = None
        if random.random() < 0.5:
            next_followup = followup_datetime.date() + timedelta(days=random.randint(30, 90))

        # 바이탈 사인 (JSON 형식)
        vitals = {}
        if random.random() < 0.6:
            vitals = {
                'bp_systolic': random.randint(110, 140),
                'bp_diastolic': random.randint(70, 90),
                'heart_rate': random.randint(60, 100),
                'temperature': round(random.uniform(36.0, 37.5), 1)
            }

        try:
            FollowUp.objects.create(
                patient=patient,
                followup_date=followup_datetime,
                followup_type=followup_type,
                clinical_status=clinical_status,
                symptoms=random.choice(symptoms_list) if random.random() < 0.7 else [],
                kps_score=random.choice([None, 70, 80, 90, 100]),
                ecog_score=random.choice([None, 0, 1, 2]),
                vitals=vitals,
                weight_kg=round(random.uniform(50, 85), 2) if random.random() < 0.6 else None,
                note=random.choice(notes_list),
                next_followup_date=next_followup,
                recorded_by=doctor
            )
            created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 경과 기록 생성: {created_count}건")
    print(f"  현재 전체 경과 기록: {FollowUp.objects.count()}건")
    return True


def create_dummy_ai_requests(num_requests=10, force=False):
    """더미 AI 추론 요청 데이터 생성"""
    print(f"\n[10단계] AI 추론 요청 데이터 생성 (목표: {num_requests}건)...")

    from apps.ai_inference.models import AIModel, AIInferenceRequest, AIInferenceResult
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = AIInferenceRequest.objects.count()
    if existing_count >= num_requests and not force:
        print(f"[SKIP] 이미 {existing_count}건의 AI 요청이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    ai_models = list(AIModel.objects.filter(is_active=True))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not ai_models:
        print("[ERROR] 활성화된 AI 모델이 없습니다.")
        print("  AI 모델을 먼저 생성합니다...")
        create_ai_models()
        ai_models = list(AIModel.objects.filter(is_active=True))
        if not ai_models:
            return False

    # AIInferenceRequest.Status에 맞춤
    statuses = ['PENDING', 'VALIDATING', 'PROCESSING', 'COMPLETED', 'FAILED']
    priorities = ['low', 'normal', 'high', 'urgent']

    created_count = 0

    for i in range(num_requests):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        model = random.choice(ai_models)
        status = random.choice(statuses)

        days_ago = random.randint(0, 60)
        requested_at = timezone.now() - timedelta(days=days_ago)

        # 시작/완료 시간 설정
        started_at = None
        completed_at = None
        error_message = None

        if status in ['PROCESSING', 'COMPLETED', 'FAILED']:
            started_at = requested_at + timedelta(minutes=random.randint(1, 30))

        if status == 'COMPLETED':
            completed_at = started_at + timedelta(minutes=random.randint(5, 60)) if started_at else None
        elif status == 'FAILED':
            completed_at = started_at + timedelta(minutes=random.randint(1, 10)) if started_at else None
            error_message = random.choice([
                "입력 데이터 검증 실패",
                "모델 처리 중 오류 발생",
                "타임아웃 초과",
                "필수 데이터 누락"
            ])

        try:
            with transaction.atomic():
                ai_request = AIInferenceRequest.objects.create(
                    patient=patient,
                    model=model,
                    requested_by=doctor,
                    status=status,
                    priority=random.choice(priorities),
                    ocs_references=[],
                    input_data={"patient_id": patient.id, "model_code": model.code},
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message=error_message,
                )

                # COMPLETED인 경우 결과도 생성
                if status == 'COMPLETED':
                    tumor_detected = random.random() < 0.7
                    result_data = {
                        "analysis_type": model.code,
                        "tumor_detected": tumor_detected,
                        "tumor_grade": random.choice(['Grade I', 'Grade II', 'Grade III', 'Grade IV']) if tumor_detected else None,
                        "tumor_location": random.choice(["frontal", "temporal", "parietal", "occipital"]) if tumor_detected else None,
                        "recommendations": [
                            "추가 영상 검사 권장" if tumor_detected else "정기 검진 권장",
                            "전문의 상담 권장"
                        ],
                    }

                    review_status = random.choice(['pending', 'approved', 'rejected'])
                    reviewed_by = doctor if review_status != 'pending' else None
                    reviewed_at = completed_at + timedelta(hours=random.randint(1, 48)) if reviewed_by else None

                    AIInferenceResult.objects.create(
                        inference_request=ai_request,
                        result_data=result_data,
                        confidence_score=round(random.uniform(0.75, 0.98), 2),
                        visualization_paths=[],
                        reviewed_by=reviewed_by,
                        review_status=review_status,
                        review_comment="결과 확인함" if reviewed_by else None,
                        reviewed_at=reviewed_at,
                    )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] AI 요청 생성: {created_count}건")
    print(f"  현재 전체 AI 요청: {AIInferenceRequest.objects.count()}건")
    return True


# ============================================================
# 처방 데이터 (from 3_prescriptions.py)
# ============================================================

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
    print(f"\n[11단계] 처방 데이터 생성 (목표: 처방 {num_prescriptions}건, 항목 약 {num_prescriptions * num_items_per_rx}건)...")

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


# ============================================================
# 데이터 리셋 및 요약
# ============================================================

def reset_clinical_data():
    """임상 더미 데이터 삭제"""
    print("\n[RESET] 임상 더미 데이터 삭제 중...")

    from apps.ocs.models import OCS, OCSHistory
    from apps.imaging.models import ImagingStudy
    from apps.encounters.models import Encounter
    from apps.patients.models import Patient, PatientAlert
    from apps.ai_inference.models import AIInferenceRequest, AIInferenceResult, AIInferenceLog
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp
    from apps.prescriptions.models import Prescription, PrescriptionItem

    # 삭제 순서: 의존성 역순
    # 처방 삭제
    prescription_item_count = PrescriptionItem.objects.count()
    PrescriptionItem.objects.all().delete()
    print(f"  PrescriptionItem: {prescription_item_count}건 삭제")

    prescription_count = Prescription.objects.count()
    Prescription.objects.all().delete()
    print(f"  Prescription: {prescription_count}건 삭제")

    # AI 로그/결과/요청 삭제
    ai_log_count = AIInferenceLog.objects.count()
    AIInferenceLog.objects.all().delete()
    print(f"  AIInferenceLog: {ai_log_count}건 삭제")

    ai_result_count = AIInferenceResult.objects.count()
    AIInferenceResult.objects.all().delete()
    print(f"  AIInferenceResult: {ai_result_count}건 삭제")

    ai_request_count = AIInferenceRequest.objects.count()
    AIInferenceRequest.objects.all().delete()
    print(f"  AIInferenceRequest: {ai_request_count}건 삭제")

    # 치료 세션/계획 삭제
    treatment_session_count = TreatmentSession.objects.count()
    TreatmentSession.objects.all().delete()
    print(f"  TreatmentSession: {treatment_session_count}건 삭제")

    treatment_plan_count = TreatmentPlan.objects.count()
    TreatmentPlan.objects.all().delete()
    print(f"  TreatmentPlan: {treatment_plan_count}건 삭제")

    # 경과 기록 삭제
    followup_count = FollowUp.objects.count()
    FollowUp.objects.all().delete()
    print(f"  FollowUp: {followup_count}건 삭제")

    # 환자 주의사항 삭제
    patient_alert_count = PatientAlert.objects.count()
    PatientAlert.objects.all().delete()
    print(f"  PatientAlert: {patient_alert_count}건 삭제")

    # OCS 관련 삭제
    ocs_history_count = OCSHistory.objects.count()
    OCSHistory.objects.all().delete()
    print(f"  OCSHistory: {ocs_history_count}건 삭제")

    imaging_count = ImagingStudy.objects.count()
    ImagingStudy.objects.all().delete()
    print(f"  ImagingStudy: {imaging_count}건 삭제")

    ocs_count = OCS.objects.count()
    OCS.objects.all().delete()
    print(f"  OCS: {ocs_count}건 삭제")

    encounter_count = Encounter.objects.count()
    Encounter.objects.all().delete()
    print(f"  Encounter: {encounter_count}건 삭제")

    patient_count = Patient.objects.count()
    Patient.objects.all().delete()
    print(f"  Patient: {patient_count}건 삭제")

    print("[OK] 임상 더미 데이터 삭제 완료")


def print_summary():
    """임상 더미 데이터 요약"""
    print("\n" + "="*60)
    print("임상 더미 데이터 생성 완료! (2/3)")
    print("="*60)

    from apps.patients.models import Patient, PatientAlert
    from apps.encounters.models import Encounter
    from apps.imaging.models import ImagingStudy
    from apps.ocs.models import OCS
    from apps.ai_inference.models import AIModel, AIInferenceRequest
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp
    from apps.prescriptions.models import Prescription, PrescriptionItem

    print(f"\n[통계 - 임상 데이터]")
    print(f"  - 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 환자 주의사항: {PatientAlert.objects.count()}건")
    print(f"  - 진료: {Encounter.objects.count()}건")
    print(f"  - OCS (RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  - OCS (LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    print(f"  - 영상 검사: {ImagingStudy.objects.count()}건")
    print(f"  - AI 모델: {AIModel.objects.count()}개")
    print(f"  - AI 요청: {AIInferenceRequest.objects.count()}건")
    print(f"  - 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  - 치료 세션: {TreatmentSession.objects.count()}건")
    print(f"  - 경과 기록: {FollowUp.objects.count()}건")
    print(f"  - 처방전: {Prescription.objects.count()}건")
    print(f"  - 처방 항목: {PrescriptionItem.objects.count()}건")

    print(f"\n[다음 단계]")
    print(f"  확장 데이터 생성:")
    print(f"    python setup_dummy_data_3_extended.py")
    print(f"")
    print(f"  또는 서버 실행:")
    print(f"    python manage.py runserver")
    print(f"")
    print(f"  테스트 계정:")
    print(f"    system / system001 (시스템 관리자)")
    print(f"    admin / admin001 (병원 관리자)")
    print(f"    doctor1~5 / doctor1001~5001 (의사)")
    print(f"    nurse1~3 / nurse1001~3001 (간호사)")
    print(f"    patient1~5 / patient1001~5001 (환자)")
    print(f"    ris1~3 / ris1001~3001 (영상과)")
    print(f"    lis1~3 / lis1001~3001 (검사과)")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 임상 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='임상 데이터 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    parser.add_argument('-y', '--yes', action='store_true', help='확인 없이 자동 실행 (비대화형 모드)')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 임상 더미 데이터 생성 (2/3)")
    print("="*60)

    # 선행 조건 확인
    if not check_prerequisites():
        sys.exit(1)

    # --reset 옵션: 임상 데이터만 삭제
    if args.reset:
        if args.yes:
            reset_clinical_data()
        else:
            confirm = input("\n임상 데이터(환자, 진료, OCS, 치료, 경과, 처방)를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                reset_clinical_data()
            else:
                print("삭제 취소됨")
                sys.exit(0)

    force = args.reset or args.force  # reset 시에는 force=True

    # ===== 환자 / 진료 / OCS =====
    # 환자 생성
    create_dummy_patients(50, force=force)

    # 진료 생성
    create_dummy_encounters(20, force=force)

    # 영상 검사 (OCS + ImagingStudy)
    create_dummy_imaging_with_ocs(30, force=force)

    # 검사 오더 (LIS)
    create_dummy_lis_orders(20, force=force)

    # AI 모델
    create_ai_models()

    # 환자 주의사항
    create_patient_alerts(force=force)

    # 환자 계정 연결
    link_patient_user_account()

    # ===== 치료 / 경과 / AI 요청 =====
    # 치료 계획
    create_dummy_treatment_plans(15, force=force)

    # 경과 추적
    create_dummy_followups(25, force=force)

    # AI 요청
    create_dummy_ai_requests(10, force=force)

    # ===== 처방 =====
    # 처방 데이터
    create_dummy_prescriptions(20, 3, force=force)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
