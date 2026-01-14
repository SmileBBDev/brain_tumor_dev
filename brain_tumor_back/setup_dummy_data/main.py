#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (통합 래퍼)

이 스크립트는 더미 데이터 스크립트를 순차 실행합니다:
1. setup_dummy_data_1_base.py - 기본 데이터 (메뉴/권한, 환자 30명, 진료, OCS, 영상, AI모델)
2. setup_dummy_data_2_add.py  - 추가 데이터 (치료계획, 경과추적, AI요청)
3. setup_dummy_data_3_prescriptions.py - 처방 데이터
4. setup_dummy_data_4_extended.py - 확장 데이터 (환자 +20명, 오늘 예약 진료, 과거 기록)
5. 추가 사용자 생성 (각 역할별 2명 추가)
6. 환자 계정-데이터 연결
7. setup_unified_schedules.py - 통합 캘린더 데이터 (공유 일정, 개인 일정)

사용법:
    python -m setup_dummy_data          # 기존 데이터 유지, 부족분만 추가
    python -m setup_dummy_data --reset  # 기존 데이터 삭제 후 새로 생성
    python -m setup_dummy_data --force  # 목표 수량 이상이어도 강제 추가
    python -m setup_dummy_data --base   # 기본 데이터만 생성
    python -m setup_dummy_data --add    # 추가 데이터만 생성
    python -m setup_dummy_data --prescriptions  # 처방 데이터만 생성
    python -m setup_dummy_data --extended       # 확장 데이터만 생성 (환자 추가, 오늘 예약)
    python -m setup_dummy_data --menu   # 메뉴/권한만 업데이트 (네비게이션 바 반영)
    python -m setup_dummy_data --schedules      # 통합 캘린더 데이터만 생성

선행 조건:
    python setup_database.py  (마이그레이션 및 기본 데이터)

개별 실행:
    python setup_dummy_data/setup_dummy_data_1_base.py [--reset] [--force]
    python setup_dummy_data/setup_dummy_data_2_add.py [--reset] [--force]
    python setup_dummy_data/setup_dummy_data_3_prescriptions.py [--reset] [--force]
    python setup_dummy_data/setup_dummy_data_4_extended.py
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

    from django.utils import timezone
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from apps.imaging.models import ImagingStudy
    from apps.ocs.models import OCS
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.accounts.models import Permission
    from apps.ai_inference.models import AIModel, AIInferenceRequest
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp
    from apps.prescriptions.models import Prescription, PrescriptionItem
    from apps.accounts.models import User, Role
    from apps.schedules.models import DoctorSchedule, SharedSchedule, PersonalSchedule

    print("\n" + "="*60)
    print("전체 더미 데이터 생성 완료!")
    print("="*60)

    # 사용자 통계
    print(f"\n[사용자 통계]")
    for role in Role.objects.all():
        count = User.objects.filter(role=role).count()
        print(f"  - {role.name}: {count}명")

    # 오늘 예약 진료 수
    today = timezone.now().date()
    today_scheduled = Encounter.objects.filter(
        admission_date__date=today,
        status='scheduled'
    ).count()

    print(f"\n[데이터 통계]")
    print(f"  - 메뉴: {Menu.objects.count()}개")
    print(f"  - 메뉴 라벨: {MenuLabel.objects.count()}개")
    print(f"  - 메뉴-권한 매핑: {MenuPermission.objects.count()}개")
    print(f"  - 권한: {Permission.objects.count()}개")
    print(f"  - 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 환자-계정 연결: {Patient.objects.filter(user__isnull=False).count()}명")
    print(f"  - 진료 (전체): {Encounter.objects.count()}건")
    print(f"  - 진료 (오늘 예약): {today_scheduled}건")
    print(f"  - OCS (RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  - OCS (LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    print(f"  - 영상 검사: {ImagingStudy.objects.count()}건")
    print(f"  - 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  - 치료 세션: {TreatmentSession.objects.count()}건")
    print(f"  - 경과 기록: {FollowUp.objects.count()}건")
    print(f"  - 처방: {Prescription.objects.count()}건")
    print(f"  - 처방 항목: {PrescriptionItem.objects.count()}건")
    print(f"  - AI 모델: {AIModel.objects.count()}개")
    print(f"  - AI 요청: {AIInferenceRequest.objects.count()}건")
    print(f"  - 의사 일정: {DoctorSchedule.objects.filter(is_deleted=False).count()}건")
    print(f"  - 공유 일정: {SharedSchedule.objects.filter(is_deleted=False).count()}건")
    print(f"  - 개인 일정: {PersonalSchedule.objects.filter(is_deleted=False).count()}건")

    print(f"\n[다음 단계]")
    print(f"  서버 실행:")
    print(f"    python manage.py runserver")
    print(f"")
    print(f"  테스트 계정:")
    print(f"    system / system001 (시스템 관리자)")
    print(f"    admin, admin2, admin3 / admin001 (병원 관리자)")
    print(f"    doctor1~5 / doctor001~005 (의사 5명)")
    print(f"    nurse1, nurse2, nurse3 / nurse001 (간호사)")
    print(f"    patient1, patient2, patient3 / patient001 (환자)")
    print(f"    ris1, ris2, ris3 / ris001 (영상과)")
    print(f"    lis1, lis2, lis3 / lis001 (검사과)")


def create_additional_users(reset=False):
    """추가 사용자 생성 (각 역할별 2명 추가, system/doctor 제외)"""
    # Django 설정
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.chdir(PROJECT_ROOT)

    import django
    django.setup()

    from apps.accounts.models import User, Role

    print("\n" + "="*60)
    print("[실행] 추가 사용자 생성")
    print("="*60)

    # 추가할 사용자 정의 (system, doctor 제외)
    additional_users = [
        # ADMIN (병원 관리자)
        {'login_id': 'admin2', 'name': '관리자2', 'email': 'admin2@hospital.com', 'role_code': 'ADMIN', 'password': 'admin001'},
        {'login_id': 'admin3', 'name': '관리자3', 'email': 'admin3@hospital.com', 'role_code': 'ADMIN', 'password': 'admin001'},
        # NURSE (간호사)
        {'login_id': 'nurse2', 'name': '간호사2', 'email': 'nurse2@hospital.com', 'role_code': 'NURSE', 'password': 'nurse001'},
        {'login_id': 'nurse3', 'name': '간호사3', 'email': 'nurse3@hospital.com', 'role_code': 'NURSE', 'password': 'nurse001'},
        # RIS (영상과)
        {'login_id': 'ris2', 'name': '영상과2', 'email': 'ris2@hospital.com', 'role_code': 'RIS', 'password': 'ris001'},
        {'login_id': 'ris3', 'name': '영상과3', 'email': 'ris3@hospital.com', 'role_code': 'RIS', 'password': 'ris001'},
        # LIS (검사과)
        {'login_id': 'lis2', 'name': '검사과2', 'email': 'lis2@hospital.com', 'role_code': 'LIS', 'password': 'lis001'},
        {'login_id': 'lis3', 'name': '검사과3', 'email': 'lis3@hospital.com', 'role_code': 'LIS', 'password': 'lis001'},
        # PATIENT (환자)
        {'login_id': 'patient2', 'name': '환자2', 'email': 'patient2@email.com', 'role_code': 'PATIENT', 'password': 'patient001'},
        {'login_id': 'patient3', 'name': '환자3', 'email': 'patient3@email.com', 'role_code': 'PATIENT', 'password': 'patient001'},
    ]

    created_count = 0
    skipped_count = 0

    for user_data in additional_users:
        login_id = user_data['login_id']

        if reset:
            # 리셋 모드: 기존 사용자 삭제 후 재생성
            User.objects.filter(login_id=login_id).delete()

        if User.objects.filter(login_id=login_id).exists():
            print(f"  [SKIP] {login_id} 이미 존재")
            skipped_count += 1
            continue

        # 역할 가져오기
        role = Role.objects.filter(code=user_data['role_code']).first()

        user = User.objects.create_user(
            login_id=login_id,
            email=user_data['email'],
            password=user_data['password'],
            name=user_data['name'],
            role=role,
        )
        print(f"  [CREATE] {login_id} ({user_data['name']}) - {user_data['role_code']}")
        created_count += 1

    print(f"\n  생성: {created_count}명, 스킵: {skipped_count}명")
    return True


def link_patient_accounts(reset=False):
    """환자 계정을 환자 데이터와 연결"""
    # Django 설정
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.chdir(PROJECT_ROOT)

    import django
    django.setup()

    from apps.accounts.models import User
    from apps.patients.models import Patient

    print("\n" + "="*60)
    print("[실행] 환자 계정-데이터 연결")
    print("="*60)

    # 연결할 환자 계정 매핑 (login_id, patient_number)
    patient_links = [
        ('patient1', 'P202600001'),
        ('patient2', 'P202600002'),
        ('patient3', 'P202600003'),
    ]

    linked_count = 0
    skipped_count = 0

    for login_id, patient_number in patient_links:
        try:
            user = User.objects.filter(login_id=login_id).first()
            patient = Patient.objects.filter(patient_number=patient_number).first()

            if not user:
                print(f"  [SKIP] {login_id} 사용자 없음")
                skipped_count += 1
                continue

            if not patient:
                print(f"  [SKIP] {patient_number} 환자 데이터 없음")
                skipped_count += 1
                continue

            if patient.user and patient.user != user and not reset:
                print(f"  [SKIP] {patient_number} 이미 다른 계정과 연결됨")
                skipped_count += 1
                continue

            patient.user = user
            patient.save()
            print(f"  [LINK] {login_id} <-> {patient_number} ({patient.name})")
            linked_count += 1

        except Exception as e:
            print(f"  [ERROR] {login_id} <-> {patient_number}: {e}")
            skipped_count += 1

    print(f"\n  연결: {linked_count}건, 스킵: {skipped_count}건")
    return True


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 더미 데이터 생성 (통합)')
    parser.add_argument('--reset', action='store_true', help='기존 데이터 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    parser.add_argument('--base', action='store_true', help='기본 데이터만 생성 (1_base)')
    parser.add_argument('--add', action='store_true', help='추가 데이터만 생성 (2_add)')
    parser.add_argument('--prescriptions', action='store_true', help='처방 데이터만 생성 (3_prescriptions)')
    parser.add_argument('--extended', action='store_true', help='확장 데이터만 생성 (4_extended: 환자 추가, 오늘 예약)')
    parser.add_argument('--menu', action='store_true', help='메뉴/권한만 업데이트 (네비게이션 바 반영)')
    parser.add_argument('--schedules', action='store_true', help='통합 캘린더 데이터만 생성 (공유 일정, 개인 일정)')
    parser.add_argument('-y', '--yes', action='store_true', help='확인 없이 자동 실행 (비대화형 모드)')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 더미 데이터 생성 (통합)")
    print("="*60)

    # --menu 옵션: 메뉴/권한만 업데이트
    if args.menu:
        run_script(
            'setup_dummy_data_1_base.py',
            ['--menu'],
            '메뉴/권한 업데이트'
        )
        return

    # --prescriptions 옵션: 처방 데이터만 생성
    if args.prescriptions:
        script_args = []
        if args.reset:
            script_args.append('--reset')
        if args.force:
            script_args.append('--force')
        if args.yes:
            script_args.append('--yes')
        run_script(
            'setup_dummy_data_3_prescriptions.py',
            script_args,
            '처방 더미 데이터 생성'
        )
        return

    # --extended 옵션: 확장 데이터만 생성 (환자 추가, 오늘 예약 진료, 과거 기록)
    if args.extended:
        run_script(
            'setup_dummy_data_4_extended.py',
            [],
            '확장 더미 데이터 생성 (환자 추가, 오늘 예약, 과거 기록)'
        )
        return

    # --schedules 옵션: 통합 캘린더 데이터만 생성
    if args.schedules:
        schedule_args = []
        if args.reset:
            schedule_args.append('--reset')
        run_script(
            'setup_unified_schedules.py',
            schedule_args,
            '통합 캘린더 더미 데이터 생성 (공유 일정, 개인 일정)'
        )
        return

    # 실행할 스크립트 결정
    run_base = not args.add  # --add만 지정하면 base 스킵
    run_add = not args.base   # --base만 지정하면 add 스킵

    # 옵션 전달
    script_args = []
    if args.reset:
        script_args.append('--reset')
    if args.force:
        script_args.append('--force')
    if args.yes:
        script_args.append('--yes')

    success = True

    # 1. 기본 데이터 생성
    if run_base:
        if not run_script(
            'setup_dummy_data_1_base.py',
            script_args,
            '기본 더미 데이터 생성 (1/7)'
        ):
            print("\n[WARNING] 기본 데이터 생성에 문제가 있습니다.")
            success = False

    # 2. 추가 데이터 생성
    if run_add:
        if not run_script(
            'setup_dummy_data_2_add.py',
            script_args,
            '추가 더미 데이터 생성 (2/7)'
        ):
            print("\n[WARNING] 추가 데이터 생성에 문제가 있습니다.")
            success = False

    # 3. 처방 데이터 생성
    if run_add:
        if not run_script(
            'setup_dummy_data_3_prescriptions.py',
            script_args,
            '처방 더미 데이터 생성 (3/7)'
        ):
            print("\n[WARNING] 처방 데이터 생성에 문제가 있습니다.")
            success = False

    # 4. 확장 데이터 생성 (환자 추가, 오늘 예약 진료, 과거 기록)
    if run_add:
        if not run_script(
            'setup_dummy_data_4_extended.py',
            [],
            '확장 더미 데이터 생성 (4/7)'
        ):
            print("\n[WARNING] 확장 데이터 생성에 문제가 있습니다.")
            success = False

    # 5. 추가 사용자 생성 (system, doctor 제외 각 역할별 2명 추가)
    if run_base:
        print(f"\n{'='*60}")
        print(f"[실행] 추가 사용자 생성 (5/7)")
        print(f"{'='*60}")
        try:
            create_additional_users(reset=args.reset)
        except Exception as e:
            print(f"\n[WARNING] 추가 사용자 생성에 문제가 있습니다: {e}")
            success = False

    # 6. 환자 계정-데이터 연결
    if run_base:
        print(f"\n{'='*60}")
        print(f"[실행] 환자 계정-데이터 연결 (6/7)")
        print(f"{'='*60}")
        try:
            link_patient_accounts(reset=args.reset)
        except Exception as e:
            print(f"\n[WARNING] 환자 계정 연결에 문제가 있습니다: {e}")
            success = False

    # 7. 통합 캘린더 데이터 생성 (공유 일정, 개인 일정)
    if run_add:
        schedule_args = []
        if args.reset:
            schedule_args.append('--reset')
        if not run_script(
            'setup_unified_schedules.py',
            schedule_args,
            '통합 캘린더 더미 데이터 생성 (7/7)'
        ):
            print("\n[WARNING] 통합 캘린더 데이터 생성에 문제가 있습니다.")
            success = False

    # 최종 요약
    if run_base and run_add:
        print_final_summary()

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
