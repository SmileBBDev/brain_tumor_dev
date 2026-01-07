"""
더미 환자 데이터 생성 스크립트
Django shell에서 실행: python manage.py shell < create_dummy_patients.py
"""

from apps.patients.models import Patient
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta
import random

# 관리자 사용자 가져오기 (등록자로 사용)
try:
    registered_by = User.objects.filter(is_superuser=True).first()
    if not registered_by:
        print("경고: 슈퍼유저가 없습니다. 첫 번째 사용자를 사용합니다.")
        registered_by = User.objects.first()

    if not registered_by:
        print("오류: 사용자가 없습니다. 먼저 사용자를 생성하세요.")
        exit(1)
except Exception as e:
    print(f"오류: {e}")
    exit(1)

# 더미 환자 데이터
dummy_patients = [
    {
        "name": "김철수",
        "birth_date": timezone.now().date() - timedelta(days=365*45),  # 45세
        "gender": "M",
        "phone": "010-1234-5678",
        "email": "kim.cs@example.com",
        "address": "서울특별시 강남구 테헤란로 123",
        "ssn": "7801011234567",  # 실제로는 암호화 필요
        "blood_type": "A+",
        "allergies": ["페니실린"],
        "chronic_diseases": ["고혈압"],
        "status": "active",
    },
    {
        "name": "이영희",
        "birth_date": timezone.now().date() - timedelta(days=365*38),  # 38세
        "gender": "F",
        "phone": "010-2345-6789",
        "email": "lee.yh@example.com",
        "address": "서울특별시 서초구 서초대로 456",
        "ssn": "8603151234568",
        "blood_type": "B+",
        "allergies": [],
        "chronic_diseases": ["당뇨"],
        "status": "active",
    },
    {
        "name": "박민수",
        "birth_date": timezone.now().date() - timedelta(days=365*52),  # 52세
        "gender": "M",
        "phone": "010-3456-7890",
        "email": "park.ms@example.com",
        "address": "경기도 성남시 분당구 판교로 789",
        "ssn": "7205201234569",
        "blood_type": "O+",
        "allergies": ["조영제"],
        "chronic_diseases": ["고혈압", "당뇨"],
        "status": "active",
    },
    {
        "name": "최지은",
        "birth_date": timezone.now().date() - timedelta(days=365*29),  # 29세
        "gender": "F",
        "phone": "010-4567-8901",
        "email": "choi.je@example.com",
        "address": "서울특별시 송파구 올림픽로 321",
        "ssn": "9506101234560",
        "blood_type": "AB+",
        "allergies": [],
        "chronic_diseases": [],
        "status": "active",
    },
    {
        "name": "정현우",
        "birth_date": timezone.now().date() - timedelta(days=365*61),  # 61세
        "gender": "M",
        "phone": "010-5678-9012",
        "email": "jung.hw@example.com",
        "address": "서울특별시 마포구 월드컵로 654",
        "ssn": "6309251234561",
        "blood_type": "A-",
        "allergies": ["아스피린"],
        "chronic_diseases": ["고혈압", "고지혈증"],
        "status": "active",
    },
    {
        "name": "강미라",
        "birth_date": timezone.now().date() - timedelta(days=365*34),  # 34세
        "gender": "F",
        "phone": "010-6789-0123",
        "email": "kang.mr@example.com",
        "address": "인천광역시 연수구 센트럴로 987",
        "ssn": "9002051234562",
        "blood_type": "B-",
        "allergies": [],
        "chronic_diseases": [],
        "status": "active",
    },
    {
        "name": "윤서준",
        "birth_date": timezone.now().date() - timedelta(days=365*47),  # 47세
        "gender": "M",
        "phone": "010-7890-1234",
        "email": "yoon.sj@example.com",
        "address": "경기도 고양시 일산동구 중앙로 147",
        "ssn": "7707151234563",
        "blood_type": "O-",
        "allergies": ["설파제"],
        "chronic_diseases": [],
        "status": "active",
    },
    {
        "name": "임수진",
        "birth_date": timezone.now().date() - timedelta(days=365*55),  # 55세
        "gender": "F",
        "phone": "010-8901-2345",
        "email": "lim.sj@example.com",
        "address": "서울특별시 강동구 천호대로 258",
        "ssn": "6912201234564",
        "blood_type": "AB-",
        "allergies": ["페니실린", "조영제"],
        "chronic_diseases": ["당뇨", "고혈압"],
        "status": "active",
    },
    {
        "name": "한지우",
        "birth_date": timezone.now().date() - timedelta(days=365*26),  # 26세
        "gender": "O",  # 기타
        "phone": "010-9012-3456",
        "email": "han.jw@example.com",
        "address": "서울특별시 관악구 관악로 369",
        "ssn": "9808301234565",
        "blood_type": "A+",
        "allergies": [],
        "chronic_diseases": [],
        "status": "active",
    },
    {
        "name": "오민지",
        "birth_date": timezone.now().date() - timedelta(days=365*42),  # 42세
        "gender": "F",
        "phone": "010-0123-4567",
        "email": "oh.mj@example.com",
        "address": "경기도 수원시 영통구 광교로 741",
        "ssn": "8204101234566",
        "blood_type": "B+",
        "allergies": [],
        "chronic_diseases": ["고지혈증"],
        "status": "active",
    },
]

# 기존 환자 수 확인
existing_count = Patient.objects.filter(is_deleted=False).count()
print(f"기존 환자 수: {existing_count}")

# 더미 환자 생성
created_count = 0
for patient_data in dummy_patients:
    try:
        # 이미 존재하는 주민등록번호인지 확인
        if Patient.objects.filter(ssn=patient_data['ssn']).exists():
            print(f"건너뜀: {patient_data['name']} (이미 존재)")
            continue

        patient = Patient.objects.create(
            registered_by=registered_by,
            **patient_data
        )
        created_count += 1
        print(f"생성됨: {patient.patient_number} - {patient.name} ({patient.get_gender_display()}, {patient.age}세)")
    except Exception as e:
        print(f"오류 ({patient_data['name']}): {e}")

print(f"\n총 {created_count}명의 환자가 생성되었습니다.")
print(f"현재 전체 환자 수: {Patient.objects.filter(is_deleted=False).count()}")

# 통계 출력
from apps.patients.services import PatientService
stats = PatientService.get_patient_statistics()
print(f"\n=== 환자 통계 ===")
print(f"총 환자: {stats['total']}")
print(f"활성: {stats['active']}")
print(f"비활성: {stats['inactive']}")
print(f"\n성별 분포:")
for gender_stat in stats['by_gender']:
    gender_display = dict(Patient.GENDER_CHOICES).get(gender_stat['gender'], gender_stat['gender'])
    print(f"  {gender_display}: {gender_stat['count']}명")
