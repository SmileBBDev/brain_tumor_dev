# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.patients.models import Patient
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create dummy patient data for testing'

    def handle(self, *args, **options):
        # Get registered_by user
        registered_by = User.objects.filter(is_superuser=True).first()
        if not registered_by:
            registered_by = User.objects.first()

        if not registered_by:
            self.stdout.write(self.style.ERROR('No user found. Create a user first.'))
            return

        # Dummy patient data
        dummy_patients = [
            {
                "name": "김철수",
                "birth_date": timezone.now().date() - timedelta(days=365*45),
                "gender": "M",
                "phone": "010-1234-5678",
                "email": "kim.cs@example.com",
                "address": "서울특별시 강남구 테헤란로 123",
                "ssn": "7801011234567",
                "blood_type": "A+",
                "allergies": ["페니실린"],
                "chronic_diseases": ["고혈압"],
                "status": "active",
            },
            {
                "name": "이영희",
                "birth_date": timezone.now().date() - timedelta(days=365*38),
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
                "birth_date": timezone.now().date() - timedelta(days=365*52),
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
                "birth_date": timezone.now().date() - timedelta(days=365*29),
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
                "birth_date": timezone.now().date() - timedelta(days=365*61),
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
                "birth_date": timezone.now().date() - timedelta(days=365*34),
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
                "birth_date": timezone.now().date() - timedelta(days=365*47),
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
                "birth_date": timezone.now().date() - timedelta(days=365*55),
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
                "birth_date": timezone.now().date() - timedelta(days=365*26),
                "gender": "O",
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
                "birth_date": timezone.now().date() - timedelta(days=365*42),
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

        existing_count = Patient.objects.filter(is_deleted=False).count()
        self.stdout.write(f'Existing patients: {existing_count}')

        created_count = 0
        for patient_data in dummy_patients:
            try:
                if Patient.objects.filter(ssn=patient_data['ssn']).exists():
                    self.stdout.write(f'Skipped: {patient_data["name"]} (already exists)')
                    continue

                patient = Patient.objects.create(
                    registered_by=registered_by,
                    **patient_data
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created: {patient.patient_number} - {patient.name} '
                        f'({patient.get_gender_display()}, {patient.age} years old)'
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error ({patient_data["name"]}): {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} patients created'))
        self.stdout.write(f'Total patients: {Patient.objects.filter(is_deleted=False).count()}')

        # Show statistics
        from apps.patients.services import PatientService
        stats = PatientService.get_patient_statistics()
        self.stdout.write('\n=== Patient Statistics ===')
        self.stdout.write(f'Total: {stats["total"]}')
        self.stdout.write(f'Active: {stats["active"]}')
        self.stdout.write(f'Inactive: {stats["inactive"]}')
        self.stdout.write('\nGender distribution:')
        for gender_stat in stats['by_gender']:
            gender_display = dict(Patient.GENDER_CHOICES).get(
                gender_stat['gender'],
                gender_stat['gender']
            )
            self.stdout.write(f'  {gender_display}: {gender_stat["count"]}')
