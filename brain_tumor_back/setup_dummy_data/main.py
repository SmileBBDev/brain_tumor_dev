#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (통합 래퍼)

이 스크립트는 두 개의 더미 데이터 스크립트를 순차 실행합니다:
1. setup_dummy_data_1_base.py - 기본 데이터 (메뉴/권한, 환자, 진료, OCS, 영상, AI모델)
2. setup_dummy_data_2_add.py  - 추가 데이터 (치료계획, 경과추적, AI요청)

사용법:
    python -m setup_dummy_data          # 기존 데이터 유지, 부족분만 추가
    python -m setup_dummy_data --reset  # 기존 데이터 삭제 후 새로 생성
    python -m setup_dummy_data --force  # 목표 수량 이상이어도 강제 추가
    python -m setup_dummy_data --base   # 기본 데이터만 생성
    python -m setup_dummy_data --add    # 추가 데이터만 생성

선행 조건:
    python setup_database.py  (마이그레이션 및 기본 데이터)

개별 실행:
    python setup_dummy_data/setup_dummy_data_1_base.py [--reset] [--force]
    python setup_dummy_data/setup_dummy_data_2_add.py [--reset] [--force]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 현재 디렉토리 (setup_dummy_data 폴더)
SCRIPT_DIR = Path(__file__).resolve().parent
# 프로젝트 루트 디렉토리 (상위 폴더)
PROJECT_ROOT = SCRIPT_DIR.parent


def run_script(script_name, args_list=None, description=""):
    """스크립트 실행"""
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        print(f"[ERROR] {script_name} 파일이 없습니다.")
        return False

    cmd = [sys.executable, str(script_path)]
    if args_list:
        cmd.extend(args_list)

    print(f"\n{'='*60}")
    print(f"[실행] {description}")
    print(f"{'='*60}")
    print(f"$ python setup_dummy_data/{script_name} {' '.join(args_list or [])}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] 스크립트 실행 실패: {e}")
        return False


def print_final_summary():
    """최종 요약 출력"""
    # Django 설정
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.chdir(PROJECT_ROOT)

    import django
    django.setup()

    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from apps.imaging.models import ImagingStudy
    from apps.ocs.models import OCS
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.accounts.models import Permission
    from apps.ai_inference.models import AIModel, AIInferenceRequest
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp

    print("\n" + "="*60)
    print("전체 더미 데이터 생성 완료!")
    print("="*60)

    print(f"\n[통계]")
    print(f"  - 메뉴: {Menu.objects.count()}개")
    print(f"  - 메뉴 라벨: {MenuLabel.objects.count()}개")
    print(f"  - 메뉴-권한 매핑: {MenuPermission.objects.count()}개")
    print(f"  - 권한: {Permission.objects.count()}개")
    print(f"  - 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 진료: {Encounter.objects.count()}건")
    print(f"  - OCS (RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  - OCS (LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    print(f"  - 영상 검사: {ImagingStudy.objects.count()}건")
    print(f"  - 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  - 치료 세션: {TreatmentSession.objects.count()}건")
    print(f"  - 경과 기록: {FollowUp.objects.count()}건")
    print(f"  - AI 모델: {AIModel.objects.count()}개")
    print(f"  - AI 요청: {AIInferenceRequest.objects.count()}건")

    print(f"\n[다음 단계]")
    print(f"  서버 실행:")
    print(f"    python manage.py runserver")
    print(f"")
    print(f"  테스트 계정:")
    print(f"    system / system001 (시스템 관리자)")
    print(f"    admin / admin001 (병원 관리자)")
    print(f"    doctor1~5 / doctor001~005 (의사 5명)")
    print(f"    nurse1 / nurse001 (간호사)")
    print(f"    patient1 / patient001 (환자)")
    print(f"    ris1 / ris001 (영상과)")
    print(f"    lis1 / lis001 (검사과)")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 더미 데이터 생성 (통합)')
    parser.add_argument('--reset', action='store_true', help='기존 데이터 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    parser.add_argument('--base', action='store_true', help='기본 데이터만 생성 (1_base)')
    parser.add_argument('--add', action='store_true', help='추가 데이터만 생성 (2_add)')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 더미 데이터 생성 (통합)")
    print("="*60)

    # 실행할 스크립트 결정
    run_base = not args.add  # --add만 지정하면 base 스킵
    run_add = not args.base   # --base만 지정하면 add 스킵

    # 옵션 전달
    script_args = []
    if args.reset:
        script_args.append('--reset')
    if args.force:
        script_args.append('--force')

    success = True

    # 1. 기본 데이터 생성
    if run_base:
        if not run_script(
            'setup_dummy_data_1_base.py',
            script_args,
            '기본 더미 데이터 생성 (1/2)'
        ):
            print("\n[WARNING] 기본 데이터 생성에 문제가 있습니다.")
            success = False

    # 2. 추가 데이터 생성
    if run_add:
        if not run_script(
            'setup_dummy_data_2_add.py',
            script_args,
            '추가 더미 데이터 생성 (2/2)'
        ):
            print("\n[WARNING] 추가 데이터 생성에 문제가 있습니다.")
            success = False

    # 3. 최종 요약
    if run_base and run_add:
        print_final_summary()

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
