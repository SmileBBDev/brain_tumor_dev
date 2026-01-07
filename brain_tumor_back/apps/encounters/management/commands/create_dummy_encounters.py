from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.encounters.models import Encounter
from apps.patients.models import Patient
from apps.accounts.models import User


class Command(BaseCommand):
    help = '진료 더미 데이터 생성'

    def handle(self, *args, **kwargs):
        # 기존 진료 수 확인
        existing_count = Encounter.objects.count()
        self.stdout.write(f'Existing encounters: {existing_count}')

        # 환자 및 의사 가져오기
        patients = list(Patient.objects.filter(is_deleted=False))
        doctors = list(User.objects.filter(role__code='DOCTOR'))

        if not patients:
            self.stdout.write(self.style.ERROR('No patients found. Please create patients first.'))
            return

        if not doctors:
            self.stdout.write(self.style.ERROR('No doctors found. Please create doctors first.'))
            return

        # 진료 데이터 정의
        encounter_data = [
            {
                'encounter_type': 'outpatient',
                'department': 'neurology',
                'chief_complaint': '두통과 어지러움이 지속됩니다',
                'primary_diagnosis': '긴장성 두통',
                'secondary_diagnoses': ['불면증'],
                'status': 'completed',
                'days_ago': 10,
                'duration_days': 0,
            },
            {
                'encounter_type': 'inpatient',
                'department': 'neurosurgery',
                'chief_complaint': '급성 두통 및 시야 장애',
                'primary_diagnosis': '뇌종양 의심',
                'secondary_diagnoses': ['고혈압', '당뇨'],
                'status': 'in-progress',
                'days_ago': 5,
                'duration_days': None,
            },
            {
                'encounter_type': 'emergency',
                'department': 'neurosurgery',
                'chief_complaint': '갑작스런 의식 저하',
                'primary_diagnosis': '뇌출혈',
                'secondary_diagnoses': [],
                'status': 'completed',
                'days_ago': 15,
                'duration_days': 7,
            },
            {
                'encounter_type': 'outpatient',
                'department': 'neurology',
                'chief_complaint': '손떨림 증상',
                'primary_diagnosis': '파킨슨병 의심',
                'secondary_diagnoses': [],
                'status': 'completed',
                'days_ago': 20,
                'duration_days': 0,
            },
            {
                'encounter_type': 'inpatient',
                'department': 'neurosurgery',
                'chief_complaint': '뇌종양 수술을 위한 입원',
                'primary_diagnosis': '교모세포종',
                'secondary_diagnoses': ['고혈압'],
                'status': 'completed',
                'days_ago': 30,
                'duration_days': 14,
            },
            {
                'encounter_type': 'outpatient',
                'department': 'neurology',
                'chief_complaint': '기억력 감퇴',
                'primary_diagnosis': '경도인지장애',
                'secondary_diagnoses': [],
                'status': 'scheduled',
                'days_ago': -5,
                'duration_days': None,
            },
            {
                'encounter_type': 'emergency',
                'department': 'neurosurgery',
                'chief_complaint': '교통사고로 인한 두부 외상',
                'primary_diagnosis': '외상성 뇌손상',
                'secondary_diagnoses': ['골절'],
                'status': 'completed',
                'days_ago': 25,
                'duration_days': 10,
            },
            {
                'encounter_type': 'outpatient',
                'department': 'neurology',
                'chief_complaint': '수면 장애',
                'primary_diagnosis': '불면증',
                'secondary_diagnoses': ['불안장애'],
                'status': 'completed',
                'days_ago': 12,
                'duration_days': 0,
            },
            {
                'encounter_type': 'inpatient',
                'department': 'neurology',
                'chief_complaint': '경련 발작',
                'primary_diagnosis': '뇌전증',
                'secondary_diagnoses': [],
                'status': 'in-progress',
                'days_ago': 3,
                'duration_days': None,
            },
            {
                'encounter_type': 'outpatient',
                'department': 'neurosurgery',
                'chief_complaint': '수술 후 경과 관찰',
                'primary_diagnosis': '뇌종양 수술 후 상태',
                'secondary_diagnoses': [],
                'status': 'scheduled',
                'days_ago': -7,
                'duration_days': None,
            },
        ]

        created_count = 0

        for i, data in enumerate(encounter_data):
            # 환자와 의사 무작위 선택
            patient = random.choice(patients)
            doctor = random.choice(doctors)

            # 날짜 계산
            admission_date = timezone.now() - timedelta(days=data['days_ago'])
            discharge_date = None
            if data['duration_days'] is not None:
                discharge_date = admission_date + timedelta(days=data['duration_days'])

            encounter = Encounter.objects.create(
                patient=patient,
                encounter_type=data['encounter_type'],
                status=data['status'],
                attending_doctor=doctor,
                department=data['department'],
                admission_date=admission_date,
                discharge_date=discharge_date,
                chief_complaint=data['chief_complaint'],
                primary_diagnosis=data['primary_diagnosis'],
                secondary_diagnoses=data['secondary_diagnoses'],
            )

            created_count += 1
            self.stdout.write(
                f"Created: {encounter.patient.name} - {encounter.get_encounter_type_display()} "
                f"({encounter.admission_date.strftime('%Y-%m-%d')})"
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'{created_count} encounters created'))
        self.stdout.write(f'Total encounters: {Encounter.objects.count()}')

        # 통계 출력
        self.stdout.write('')
        self.stdout.write('=== Encounter Statistics ===')
        self.stdout.write(f'Total: {Encounter.objects.count()}')
        active_count = Encounter.objects.filter(
            status__in=['scheduled', 'in-progress'],
            is_deleted=False
        ).count()
        self.stdout.write(f'Active: {active_count}')

        self.stdout.write('')
        self.stdout.write('Type distribution:')
        for enc_type, label in Encounter.ENCOUNTER_TYPE_CHOICES:
            count = Encounter.objects.filter(encounter_type=enc_type).count()
            self.stdout.write(f'  {label}: {count}')

        self.stdout.write('')
        self.stdout.write('Status distribution:')
        for enc_status, label in Encounter.STATUS_CHOICES:
            count = Encounter.objects.filter(status=enc_status).count()
            self.stdout.write(f'  {label}: {count}')
