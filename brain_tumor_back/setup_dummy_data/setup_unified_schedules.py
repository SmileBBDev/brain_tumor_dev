#!/usr/bin/env python
"""
통합 캘린더 더미 데이터 생성 스크립트

공유 일정(SharedSchedule)과 개인 일정(PersonalSchedule)을 생성합니다.
- 공유 일정: Admin이 관리하는 권한별 공유 일정
- 개인 일정: 모든 사용자의 개인 일정

사용법:
    python setup_dummy_data/setup_unified_schedules.py
    python setup_dummy_data/setup_unified_schedules.py --reset  # 기존 데이터 삭제 후 생성
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
from apps.schedules.models import SharedSchedule, PersonalSchedule


def get_admin_user():
    """Admin 역할의 사용자 조회"""
    return User.objects.filter(
        role__code='ADMIN',
        is_active=True
    ).first()


def get_all_users():
    """활성 사용자 목록 조회"""
    return list(User.objects.filter(is_active=True).select_related('role'))


def create_shared_schedules(admin_user, reset=False):
    """공유 일정 더미 데이터 생성"""

    if not admin_user:
        print("[ERROR] ADMIN 역할의 사용자가 없습니다.")
        return 0

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if reset:
        deleted_count = SharedSchedule.objects.filter(is_deleted=False).delete()[0]
        print(f"[INFO] 기존 공유 일정 {deleted_count}건 삭제됨")

    # 공유 일정 샘플 데이터
    shared_samples = [
        # (제목, 유형, 색상, 대상 권한, 종일여부)
        ('전체 직원 회의', 'meeting', '#5b8def', 'ALL', False),
        ('월례 조회', 'announcement', '#8b5cf6', 'ALL', False),
        ('시스템 점검 안내', 'announcement', '#8b5cf6', 'ALL', True),
        ('신년 휴무', 'event', '#ec4899', 'ALL', True),
        ('의료진 워크샵', 'training', '#f2a65a', 'DOCTOR', False),
        ('간호사 보수교육', 'training', '#f2a65a', 'NURSE', False),
        ('검사실 품질관리 교육', 'training', '#f2a65a', 'LIS', False),
        ('영상실 안전교육', 'training', '#f2a65a', 'RIS', False),
        ('관리자 회의', 'meeting', '#5b8def', 'ADMIN', False),
        ('의사 진료지침 세미나', 'training', '#f2a65a', 'DOCTOR', False),
        ('간호 프로토콜 회의', 'meeting', '#5b8def', 'NURSE', False),
        ('외부기관 연계 미팅', 'meeting', '#5b8def', 'EXTERNAL', False),
        ('환자 안내 공지', 'announcement', '#8b5cf6', 'PATIENT', True),
        ('LIS 시스템 업데이트', 'announcement', '#8b5cf6', 'LIS', True),
        ('RIS 장비 점검', 'announcement', '#8b5cf6', 'RIS', True),
    ]

    time_slots = [
        (9, 0, 10, 0),
        (10, 0, 11, 30),
        (13, 0, 14, 0),
        (14, 0, 15, 30),
        (15, 0, 17, 0),
    ]

    created_count = 0

    for title, schedule_type, color, visibility, is_all_day in shared_samples:
        # 날짜: 오늘부터 45일 이내
        day_offset = random.randint(0, 45)
        schedule_date = today_start + timedelta(days=day_offset)

        if is_all_day:
            start_dt = schedule_date.replace(hour=0, minute=0)
            end_dt = schedule_date.replace(hour=23, minute=59)
        else:
            slot = random.choice(time_slots)
            start_dt = schedule_date.replace(hour=slot[0], minute=slot[1])
            end_dt = schedule_date.replace(hour=slot[2], minute=slot[3])

        try:
            schedule = SharedSchedule.objects.create(
                title=title,
                schedule_type=schedule_type,
                start_datetime=start_dt,
                end_datetime=end_dt,
                all_day=is_all_day,
                color=color,
                visibility=visibility,
                description=f'{title} - 자동 생성된 공유 일정',
                created_by=admin_user,
            )
            created_count += 1

            date_str = start_dt.strftime('%m/%d')
            if not is_all_day:
                date_str += f" {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
            print(f"  [+] 공유: {title} ({visibility}) - {date_str}")

        except Exception as e:
            print(f"  [ERROR] 공유 일정 생성 실패: {e}")

    return created_count


def create_personal_schedules(users, reset=False):
    """개인 일정 더미 데이터 생성"""

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if reset:
        deleted_count = PersonalSchedule.objects.filter(is_deleted=False).delete()[0]
        print(f"[INFO] 기존 개인 일정 {deleted_count}건 삭제됨")

    # 개인 일정 샘플 데이터
    personal_samples = {
        'personal': [
            ('개인 약속', '#5fb3a2'),
            ('병원 외 미팅', '#5fb3a2'),
            ('건강검진', '#5fb3a2'),
            ('가족 행사', '#5fb3a2'),
        ],
        'meeting': [
            ('팀 미팅', '#5b8def'),
            ('프로젝트 회의', '#5b8def'),
        ],
        'leave': [
            ('연차', '#e56b6f'),
            ('반차', '#e56b6f'),
            ('조퇴', '#e56b6f'),
        ],
        'training': [
            ('온라인 교육', '#f2a65a'),
            ('자격증 공부', '#f2a65a'),
        ],
        'other': [
            ('기타 일정', '#9ca3af'),
        ],
    }

    time_slots = [
        (8, 0, 9, 0),
        (9, 0, 10, 0),
        (12, 0, 13, 0),
        (14, 0, 15, 0),
        (17, 0, 18, 0),
        (18, 0, 19, 0),
    ]

    created_count = 0

    for user in users:
        # PATIENT는 제외 (환자는 개인 일정 없음)
        if user.role and user.role.code == 'PATIENT':
            continue

        # 기존 개인 일정 수 확인
        existing = PersonalSchedule.objects.filter(
            user=user,
            is_deleted=False
        ).count()

        if existing >= 5:
            print(f"[SKIP] {user.name}: 이미 {existing}건의 개인 일정 존재")
            continue

        # 각 사용자에게 3-6개의 개인 일정 생성
        num_schedules = random.randint(3, 6)

        for i in range(num_schedules):
            # 날짜: 오늘부터 30일 이내
            day_offset = random.randint(-3, 30)
            schedule_date = today_start + timedelta(days=day_offset)

            # 일정 유형 선택
            schedule_type = random.choice(list(personal_samples.keys()))
            title, color = random.choice(personal_samples[schedule_type])

            # 종일 여부
            if schedule_type == 'leave':
                all_day = random.random() < 0.6
            else:
                all_day = random.random() < 0.15

            if all_day:
                start_dt = schedule_date.replace(hour=0, minute=0)
                end_dt = schedule_date.replace(hour=23, minute=59)
            else:
                slot = random.choice(time_slots)
                start_dt = schedule_date.replace(hour=slot[0], minute=slot[1])
                end_dt = schedule_date.replace(hour=slot[2], minute=slot[3])

            try:
                schedule = PersonalSchedule.objects.create(
                    user=user,
                    title=title,
                    schedule_type=schedule_type,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    all_day=all_day,
                    color=color,
                    description=f'{title} - 자동 생성된 개인 일정',
                )
                created_count += 1

                date_str = start_dt.strftime('%m/%d')
                if not all_day:
                    date_str += f" {start_dt.strftime('%H:%M')}"
                print(f"  [+] 개인: {user.name} - {title} ({schedule_type}) - {date_str}")

            except Exception as e:
                print(f"  [ERROR] 개인 일정 생성 실패: {e}")

    return created_count


def main(reset=False):
    """메인 실행 함수"""

    print("=" * 60)
    print("통합 캘린더 더미 데이터 생성")
    print("=" * 60)

    admin_user = get_admin_user()
    all_users = get_all_users()

    if not admin_user:
        print("[ERROR] Admin 사용자가 없습니다. setup_dummy_data_1_base.py를 먼저 실행하세요.")
        return

    print(f"\n[INFO] Admin 사용자: {admin_user.name} ({admin_user.login_id})")
    print(f"[INFO] 전체 활성 사용자: {len(all_users)}명")

    # 1. 공유 일정 생성
    print("\n" + "-" * 40)
    print("1. 공유 일정 생성")
    print("-" * 40)
    shared_count = create_shared_schedules(admin_user, reset)

    # 2. 개인 일정 생성
    print("\n" + "-" * 40)
    print("2. 개인 일정 생성")
    print("-" * 40)
    personal_count = create_personal_schedules(all_users, reset)

    # 결과 요약
    print("\n" + "=" * 60)
    print("[DONE] 더미 데이터 생성 완료")
    print("=" * 60)
    print(f"  - 공유 일정: {shared_count}건")
    print(f"  - 개인 일정: {personal_count}건")

    # 권한별 공유 일정 현황
    print("\n[SUMMARY] 권한별 공유 일정:")
    for visibility in ['ALL', 'ADMIN', 'DOCTOR', 'NURSE', 'LIS', 'RIS', 'PATIENT', 'EXTERNAL']:
        count = SharedSchedule.objects.filter(
            visibility=visibility,
            is_deleted=False
        ).count()
        if count > 0:
            print(f"  {visibility}: {count}건")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='통합 캘린더 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='기존 일정 삭제 후 생성')
    args = parser.parse_args()

    main(reset=args.reset)
