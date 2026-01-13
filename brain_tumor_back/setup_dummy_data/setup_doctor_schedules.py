#!/usr/bin/env python
"""
의사 일정 더미 데이터 생성 스크립트

의사 대시보드의 "의사 일정 캘린더" 기능 테스트를 위한 스크립트입니다.
모든 DOCTOR 역할 사용자에게 일정을 생성합니다.

사용법:
    python setup_dummy_data/setup_doctor_schedules.py
    python setup_dummy_data/setup_doctor_schedules.py --reset  # 기존 데이터 삭제 후 생성
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
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
from apps.schedules.models import DoctorSchedule


def get_doctors():
    """DOCTOR 역할의 사용자 목록 조회"""
    return list(User.objects.filter(
        role__code='DOCTOR',
        is_active=True
    ))


def create_doctor_schedules(reset=False):
    """의사 일정 더미 데이터 생성"""

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    doctors = get_doctors()

    if not doctors:
        print("[ERROR] DOCTOR 역할의 사용자가 없습니다.")
        print("  먼저 setup_dummy_data_1_base.py를 실행하세요.")
        return

    print(f"\n[INFO] 발견된 의사: {len(doctors)}명")
    for doc in doctors:
        print(f"  - {doc.name} ({doc.login_id})")

    # 기존 데이터 삭제 (reset 옵션)
    if reset:
        deleted_count = DoctorSchedule.objects.filter(is_deleted=False).delete()[0]
        print(f"[INFO] 기존 일정 {deleted_count}건 삭제됨")

    # 일정 유형별 샘플 데이터
    schedule_samples = {
        'meeting': [
            ('부서 회의', '#5b8def'),
            ('의료진 회의', '#5b8def'),
            ('케이스 컨퍼런스', '#5b8def'),
            ('월례 회의', '#5b8def'),
            ('다학제 회의', '#5b8def'),
        ],
        'leave': [
            ('연차 휴가', '#e56b6f'),
            ('반차', '#e56b6f'),
            ('가족 행사', '#e56b6f'),
            ('개인 사유', '#e56b6f'),
        ],
        'training': [
            ('학술 세미나', '#f2a65a'),
            ('신기술 교육', '#f2a65a'),
            ('안전 교육', '#f2a65a'),
            ('직무 연수', '#f2a65a'),
        ],
        'personal': [
            ('개인 일정', '#5fb3a2'),
            ('병원 외 미팅', '#5fb3a2'),
            ('논문 작성', '#5fb3a2'),
        ],
        'other': [
            ('외부 일정', '#9ca3af'),
            ('기타', '#9ca3af'),
        ],
    }

    # 시간대 (시작시간, 종료시간)
    time_slots = [
        (8, 0, 9, 0),    # 08:00-09:00
        (9, 0, 10, 0),   # 09:00-10:00
        (10, 0, 11, 0),  # 10:00-11:00
        (13, 0, 14, 0),  # 13:00-14:00
        (14, 0, 15, 0),  # 14:00-15:00
        (15, 0, 17, 0),  # 15:00-17:00
        (17, 0, 18, 0),  # 17:00-18:00
    ]

    created_count = 0

    for doctor in doctors:
        # 이 의사의 기존 일정 수 확인
        existing = DoctorSchedule.objects.filter(
            doctor=doctor,
            is_deleted=False
        ).count()

        if existing >= 10:
            print(f"[SKIP] {doctor.name}: 이미 {existing}건의 일정 존재")
            continue

        # 각 의사에게 7-10개의 일정 생성 (이번 달 + 다음 달)
        num_schedules = random.randint(7, 10)

        for i in range(num_schedules):
            # 날짜: 오늘부터 30일 이내 (과거 3일 포함)
            day_offset = random.randint(-3, 30)
            schedule_date = today_start + timedelta(days=day_offset)

            # 일정 유형 및 제목 선택
            schedule_type = random.choice(list(schedule_samples.keys()))
            title, color = random.choice(schedule_samples[schedule_type])

            # 종일 여부 (휴가는 종일일 확률 높음)
            if schedule_type == 'leave':
                all_day = random.random() < 0.7
            else:
                all_day = random.random() < 0.1

            if all_day:
                # 종일 일정
                start_dt = schedule_date.replace(hour=0, minute=0)
                # 휴가는 여러 날일 수 있음
                if schedule_type == 'leave' and random.random() < 0.3:
                    end_dt = schedule_date + timedelta(days=random.randint(1, 3))
                    end_dt = end_dt.replace(hour=23, minute=59)
                else:
                    end_dt = schedule_date.replace(hour=23, minute=59)
            else:
                # 시간 지정 일정
                slot = random.choice(time_slots)
                start_dt = schedule_date.replace(hour=slot[0], minute=slot[1])
                end_dt = schedule_date.replace(hour=slot[2], minute=slot[3])

            try:
                schedule = DoctorSchedule.objects.create(
                    doctor=doctor,
                    title=title,
                    schedule_type=schedule_type,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    all_day=all_day,
                    color=color,
                    description=f'{title} - 자동 생성된 테스트 데이터',
                )
                created_count += 1

                if all_day:
                    date_str = start_dt.strftime('%m/%d')
                    if start_dt.date() != end_dt.date():
                        date_str += f" ~ {end_dt.strftime('%m/%d')}"
                    print(f"  [+] {doctor.name}: {title} ({schedule_type}) - {date_str} (종일)")
                else:
                    time_str = f"{start_dt.strftime('%m/%d %H:%M')}-{end_dt.strftime('%H:%M')}"
                    print(f"  [+] {doctor.name}: {title} ({schedule_type}) - {time_str}")

            except Exception as e:
                print(f"  [ERROR] 생성 실패: {e}")

    print(f"\n[DONE] 총 {created_count}건의 의사 일정 생성 완료")

    # 의사별 요약
    print("\n[SUMMARY] 의사별 일정 현황:")
    for doctor in doctors:
        count = DoctorSchedule.objects.filter(
            doctor=doctor,
            is_deleted=False
        ).count()

        # 유형별 카운트
        by_type = {}
        for schedule_type in ['meeting', 'leave', 'training', 'personal', 'other']:
            type_count = DoctorSchedule.objects.filter(
                doctor=doctor,
                schedule_type=schedule_type,
                is_deleted=False
            ).count()
            if type_count > 0:
                by_type[schedule_type] = type_count

        type_str = ', '.join([f"{k}:{v}" for k, v in by_type.items()])
        print(f"  {doctor.name}: {count}건 ({type_str})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='의사 일정 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='기존 일정 삭제 후 생성')
    args = parser.parse_args()

    print("=" * 50)
    print("의사 일정 더미 데이터 생성")
    print("=" * 50)

    create_doctor_schedules(reset=args.reset)
