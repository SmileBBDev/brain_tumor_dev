import os
import django
import random
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.encounters.models import Encounter
from apps.patients.models import Patient
from apps.accounts.models import User

def create_dummy_encounters(count=20):
    """더미 진료 데이터 생성"""

    # Get active patients and doctors
    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("No active patients found. Please create patients first.")
        return

    if not doctors:
        print("No doctors found. Please create doctor users first.")
        return

    encounter_types = ['outpatient', 'inpatient', 'emergency']
    statuses = ['scheduled', 'in-progress', 'completed', 'cancelled']
    departments = ['neurology', 'neurosurgery']

    chief_complaints = [
        '두통이 심해요',
        '어지러움증이 계속됩니다',
        '손발 저림 증상',
        '기억력 감퇴',
        '수면 장애',
        '편두통',
        '목 통증',
        '허리 통증',
        '시야 흐림',
        '균형 감각 이상',
        '근육 경련',
        '안면 마비 증상',
        '발작 증세',
        '의식 저하',
        '보행 장애',
    ]

    primary_diagnoses = [
        '뇌종양 의심',
        '편두통',
        '뇌졸중',
        '파킨슨병',
        '치매',
        '간질',
        '다발성 경화증',
        '신경통',
        '뇌수막염',
        '뇌출혈',
    ]

    secondary_diagnoses_pool = [
        '고혈압',
        '당뇨',
        '고지혈증',
        '부정맥',
        '우울증',
        '불안장애',
        '수면무호흡증',
    ]

    created_count = 0

    for i in range(count):
        # Random admission date within last 60 days
        days_ago = random.randint(0, 60)
        admission_date = timezone.now() - timedelta(days=days_ago)

        # Random encounter type
        encounter_type = random.choice(encounter_types)

        # Status logic based on admission date
        if days_ago > 30:
            # Old encounters are likely completed or cancelled
            status = random.choice(['completed', 'cancelled'])
        elif days_ago > 7:
            # Recent encounters might be in-progress or completed
            status = random.choice(['in-progress', 'completed'])
        else:
            # Very recent encounters could be any status
            status = random.choice(statuses)

        # Discharge date logic
        discharge_date = None
        if status == 'completed':
            # Completed encounters have discharge date
            # For outpatient: same day or next day
            if encounter_type == 'outpatient':
                discharge_days = random.choice([0, 1])
            # For inpatient: 1-14 days later
            elif encounter_type == 'inpatient':
                discharge_days = random.randint(1, 14)
            # For emergency: same day to 7 days
            else:
                discharge_days = random.randint(0, 7)

            discharge_date = admission_date + timedelta(days=discharge_days)
        elif status == 'cancelled':
            # Cancelled encounters might have discharge date (same day)
            if random.choice([True, False]):
                discharge_date = admission_date
        # scheduled and in-progress: discharge_date remains None (still admitted)

        # Random secondary diagnoses
        num_secondary = random.randint(0, 3)
        secondary_diagnoses = random.sample(secondary_diagnoses_pool, num_secondary) if num_secondary > 0 else []

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
                secondary_diagnoses=secondary_diagnoses,
            )
            created_count += 1

            status_str = f"{encounter.get_status_display()}"
            discharge_str = discharge_date.strftime('%Y-%m-%d') if discharge_date else '입원중'
            print(f"{created_count}. Created: {encounter.patient.name} - {encounter.get_encounter_type_display()} - {status_str} - 퇴원: {discharge_str}")

        except Exception as e:
            print(f"Error creating encounter: {e}")

    print(f"\n총 {created_count}개의 더미 진료 데이터가 생성되었습니다.")

if __name__ == '__main__':
    create_dummy_encounters(20)
