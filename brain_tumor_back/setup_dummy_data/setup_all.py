#!/usr/bin/env python
"""
전체 더미 데이터 설정 스크립트

모든 더미 데이터를 순서대로 생성합니다.

사용법:
    python setup_dummy_data/setup_all.py
    python setup_dummy_data/setup_all.py --reset  # 일부 데이터 초기화 후 생성
    python setup_dummy_data/setup_all.py --migrate  # 마이그레이션 후 생성
"""

import os
import sys
from pathlib import Path
import argparse
import subprocess

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def run_migrations():
    """마이그레이션 실행"""
    print("\n" + "=" * 50)
    print("마이그레이션 실행")
    print("=" * 50)

    # makemigrations
    print("\n[1/2] makemigrations 실행...")
    result = subprocess.run(
        [sys.executable, 'manage.py', 'makemigrations'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return False

    # migrate
    print("\n[2/2] migrate 실행...")
    result = subprocess.run(
        [sys.executable, 'manage.py', 'migrate'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return False

    print("[DONE] 마이그레이션 완료")
    return True


def run_script(script_name, reset=False):
    """개별 스크립트 실행"""
    script_path = PROJECT_ROOT / 'setup_dummy_data' / script_name

    if not script_path.exists():
        print(f"[SKIP] {script_name} - 파일 없음")
        return True

    print(f"\n[RUN] {script_name}")
    print("-" * 40)

    cmd = [sys.executable, str(script_path)]
    if reset and script_name in ['setup_today_encounters.py', 'setup_doctor_schedules.py']:
        cmd.append('--reset')

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return False

    return True


def main(reset=False, migrate=False):
    """메인 실행 함수"""

    print("=" * 60)
    print("   전체 더미 데이터 설정")
    print("=" * 60)

    # 마이그레이션 (옵션)
    if migrate:
        if not run_migrations():
            print("\n[ABORT] 마이그레이션 실패로 중단합니다.")
            return

    # 스크립트 실행 순서
    scripts = [
        'setup_dummy_data_1_base.py',        # 기본 데이터 (사용자, 환자 등)
        'setup_dummy_data_2_add.py',         # 추가 데이터
        'setup_dummy_data_3_prescriptions.py', # 처방 데이터
        'setup_dummy_data_4_extended.py',    # 확장 데이터
        'setup_today_encounters.py',         # 오늘 예약 환자
        'setup_doctor_schedules.py',         # 의사 일정
    ]

    success_count = 0
    fail_count = 0

    for script in scripts:
        if run_script(script, reset):
            success_count += 1
        else:
            fail_count += 1

    # 결과 요약
    print("\n" + "=" * 60)
    print("   실행 결과 요약")
    print("=" * 60)
    print(f"  성공: {success_count}개")
    print(f"  실패: {fail_count}개")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='전체 더미 데이터 설정')
    parser.add_argument('--reset', action='store_true',
                        help='오늘 예약 및 의사 일정 초기화 후 생성')
    parser.add_argument('--migrate', action='store_true',
                        help='마이그레이션 먼저 실행')
    args = parser.parse_args()

    main(reset=args.reset, migrate=args.migrate)
