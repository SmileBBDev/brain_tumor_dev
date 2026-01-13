#!/usr/bin/env python
"""
오늘 예약 환자 더미 데이터 생성 스크립트

의사 대시보드의 "금일 예약 환자" 기능 테스트를 위한 스크립트입니다.
모든 DOCTOR 역할 사용자에게 오늘 예약 환자를 생성합니다.

사용법:
    python setup_dummy_data/setup_today_encounters.py
    python setup_dummy_data/setup_today_encounters.py --reset  # 오늘 데이터 삭제 후 생성
"""

import os
import sys
from pathlib import Path
from datetime import time as dt_time
import random
import argparse

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.encounters.models import Encounter


def get_doctors():
    """DOCTOR 역할의 사용자 목록 조회"""
    return list(User.objects.filter(
        role__code='DOCTOR',
        is_active=True
    ))


def get_patients():
    """활성 환자 목록 조회"""
    return list(Patient.objects.filter(is_deleted=False)[:50])


def create_today_encounters(reset=False):
    """오늘 예약 환자 데이터 생성"""

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    doctors = get_doctors()
    patients = get_patients()

    if not doctors:
        print("[ERROR] DOCTOR 역할의 사용자가 없습니다.")
        print("  먼저 setup_dummy_data_1_base.py를 실행하세요.")
        return

    if not patients:
        print("[ERROR] 환자 데이터가 없습니다.")
        print("  먼저 setup_dummy_data_1_base.py를 실행하세요.")
        return

    print(f"\n[INFO] 발견된 의사: {len(doctors)}명")
    for doc in doctors:
        print(f"  - {doc.name} ({doc.login_id})")

    print(f"[INFO] 사용 가능한 환자: {len(patients)}명")

    # 오늘 예약 삭제 (reset 옵션)
    if reset:
        deleted_count = Encounter.objects.filter(
            admission_date__gte=today_start,
            admission_date__lt=today_start + timezone.timedelta(days=1)
        ).delete()[0]
        print(f"[INFO] 기존 오늘 예약 {deleted_count}건 삭제됨")

    # 예약 시간대
    scheduled_times = [
        dt_time(9, 0),
        dt_time(10, 0),
        dt_time(11, 0),
        dt_time(14, 0),
        dt_time(15, 0),
        dt_time(16, 0),
    ]

    # 진료 유형
    encounter_types = ['outpatient', 'outpatient', 'outpatient', 'inpatient', 'emergency']

    # 주호소 샘플
    chief_complaints = [
        '두통 지속',
        '어지러움',
        '정기 검진',
        '추적 관찰',
        '증상 악화',
        'MRI 결과 확인',
        '약 처방 요청',
    ]

    # 각 의사에게 5명씩 예약 생성
    created_count = 0

    for doctor in doctors:
        # 이 의사의 오늘 예약 수 확인
        existing = Encounter.objects.filter(
            attending_doctor=doctor,
            admission_date__gte=today_start,
            admission_date__lt=today_start + timezone.timedelta(days=1),
            is_deleted=False
        ).count()

        if existing >= 5:
            print(f"[SKIP] {doctor.name}: 이미 {existing}건의 오늘 예약 존재")
            continue

        # 5명 생성 (상태: scheduled 3, in_progress 1, completed 1)
        statuses = ['scheduled', 'scheduled', 'scheduled', 'in_progress', 'completed']
        random.shuffle(statuses)

        used_patients = set()

        for i, status in enumerate(statuses):
            # 환자 선택 (중복 방지)
            available = [p for p in patients if p.id not in used_patients]
            if not available:
                break
            patient = random.choice(available)
            used_patients.add(patient.id)

            # 예약 시간 (오늘 날짜 + 시간)
            sched_time = scheduled_times[i % len(scheduled_times)]
            admission_dt = today_start.replace(
                hour=sched_time.hour,
                minute=sched_time.minute
            )

            try:
                enc = Encounter.objects.create(
                    patient=patient,
                    attending_doctor=doctor,
                    admission_date=admission_dt,
                    scheduled_time=sched_time,
                    status=status,
                    encounter_type=random.choice(encounter_types),
                    department=random.choice(['neurology', 'neurosurgery']),
                    chief_complaint=random.choice(chief_complaints),
                )
                created_count += 1
                print(f"  [+] {doctor.name} <- {patient.name} ({status}) @ {sched_time.strftime('%H:%M')}")
            except Exception as e:
                print(f"  [ERROR] 생성 실패: {e}")

    print(f"\n[DONE] 총 {created_count}건의 오늘 예약 생성 완료")

    # 의사별 요약
    print("\n[SUMMARY] 의사별 오늘 예약 현황:")
    for doctor in doctors:
        count = Encounter.objects.filter(
            attending_doctor=doctor,
            admission_date__gte=today_start,
            admission_date__lt=today_start + timezone.timedelta(days=1),
            is_deleted=False
        ).exclude(status='cancelled').count()
        print(f"  {doctor.name}: {count}건")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='오늘 예약 환자 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='기존 오늘 예약 삭제 후 생성')
    args = parser.parse_args()

    print("=" * 50)
    print("오늘 예약 환자 더미 데이터 생성")
    print("=" * 50)

    create_today_encounters(reset=args.reset)
