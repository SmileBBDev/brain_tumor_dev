#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (1/2) - 기본 데이터

이 스크립트는 기본 더미 데이터를 생성합니다:
- DB 자동 생성 (없는 경우)
- 마이그레이션 자동 실행
- 역할/사용자 기본 데이터
- 메뉴/권한 시드 데이터
- 환자 데이터
- 진료 데이터
- OCS (RIS/LIS) 데이터
- 영상 검사 데이터
- AI 모델 시드 데이터

사용법:
    python setup_dummy_data_1_base.py          # 기존 데이터 유지, 부족분만 추가
    python setup_dummy_data_1_base.py --reset  # 기존 데이터 삭제 후 새로 생성
    python setup_dummy_data_1_base.py --force  # 목표 수량 이상이어도 강제 추가
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import timedelta
import random
import argparse

# 프로젝트 루트 디렉토리로 이동 (상위 폴더)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)


def create_database_if_not_exists():
    """데이터베이스가 없으면 생성 (Django 초기화 전에 실행)"""
    print("\n[0단계] 데이터베이스 존재 확인...")

    from dotenv import load_dotenv
    import environ

    env_path = PROJECT_ROOT / 'dbconn.env'
    load_dotenv(env_path)

    env = environ.Env()

    db_name = env('MYSQL_DB', default='brain_tumor')
    db_user = env('MYSQL_USER', default='root')
    db_password = env('MYSQL_PASSWORD', default='')
    db_host = env('MYSQL_HOST', default='localhost')
    db_port = env('MYSQL_PORT', default='3306')

    try:
        import pymysql
    except ImportError:
        print("[WARNING] pymysql이 설치되지 않았습니다.")
        print("  pip install pymysql")
        return False

    try:
        # DB 없이 MySQL 서버에 연결
        conn = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            charset='utf8mb4'
        )

        cursor = conn.cursor()

        # DB 존재 확인
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"[OK] 데이터베이스 '{db_name}' 이미 존재")
        else:
            # DB 생성
            print(f"[INFO] 데이터베이스 '{db_name}' 생성 중...")
            cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            print(f"[OK] 데이터베이스 '{db_name}' 생성 완료")

        cursor.close()
        conn.close()
        return True

    except pymysql.Error as e:
        print(f"[ERROR] MySQL 연결 실패: {e}")
        print(f"  Host: {db_host}:{db_port}")
        print(f"  User: {db_user}")
        print("  MySQL 서버가 실행 중인지 확인하세요.")
        return False


def run_migrations():
    """마이그레이션 실행"""
    print("\n[1단계] 마이그레이션 실행...")

    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate', '--no-input'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[OK] 마이그레이션 완료")
            return True
        else:
            print(f"[ERROR] 마이그레이션 실패")
            if result.stderr:
                print(result.stderr[:500])
            return False
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실행 실패: {e}")
        return False


# DB 생성 및 마이그레이션 (Django 초기화 전)
if __name__ == '__main__' or True:  # import 시에도 실행
    if not create_database_if_not_exists():
        print("[WARNING] DB 자동 생성 실패 - 계속 진행합니다.")

    if not run_migrations():
        print("[WARNING] 마이그레이션 실패 - 계속 진행합니다.")

# Django 설정 (DB 생성 후)
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.utils import timezone
from django.db import IntegrityError, transaction


def setup_roles():
    """기본 역할 생성"""
    print("\n[1단계] 기본 역할 설정...")

    from apps.accounts.models import Role

    roles = [
        ('SYSTEMMANAGER', 'System Manager', '시스템 관리자'),
        ('ADMIN', 'Admin', '병원 관리자'),
        ('DOCTOR', 'Doctor', '의사'),
        ('NURSE', 'Nurse', '간호사'),
        ('PATIENT', 'Patient', '환자'),
        ('RIS', 'RIS', '영상과'),
        ('LIS', 'LIS', '검사과'),
    ]

    created_count = 0
    for code, name, description in roles:
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={'name': name, 'description': description, 'is_active': True}
        )
        if created:
            created_count += 1
            print(f"  생성: {code}")
        else:
            print(f"  존재: {code}")

    print(f"[OK] 역할 설정 완료 ({created_count}개 생성)")
    return True


def setup_superuser():
    """슈퍼유저 생성"""
    print("\n[2단계] 슈퍼유저 확인...")

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role

    User = get_user_model()

    if User.objects.filter(is_superuser=True).exists():
        superuser = User.objects.filter(is_superuser=True).first()
        print(f"[OK] 슈퍼유저 이미 존재: {superuser.login_id}")
        return True

    print("슈퍼유저가 없습니다. 기본 슈퍼유저를 생성합니다.")

    # Role 가져오기
    system_role = Role.objects.filter(code='SYSTEMMANAGER').first()

    try:
        superuser = User(
            login_id='system',
            name='시스템관리자',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            role=system_role
        )
        superuser.set_password('system001')
        superuser.save()
        print(f"[OK] 슈퍼유저 생성: system / system001")
        return True
    except Exception as e:
        print(f"[ERROR] 슈퍼유저 생성 실패: {e}")
        return False


def setup_test_users():
    """테스트 사용자 생성 (UserProfile 포함)"""
    print("\n[3단계] 테스트 사용자 설정...")

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role, UserProfile
    from datetime import date

    User = get_user_model()

    # (login_id, password, name, email, role_code, is_staff, profile_data)
    # 비밀번호 규칙: {login_id}001 (예: admin → admin001, doctor1 → doctor1001)
    test_users = [
        ('admin', 'admin001', '병원관리자', 'admin@neuronova.hospital', 'ADMIN', True, {
            'birthDate': date(1975, 3, 15),
            'phoneMobile': '010-1234-0001',
            'phoneOffice': '02-1234-1001',
            'hireDate': date(2010, 1, 1),
            'departmentId': 1,
            'title': '병원 관리자',
        }),
        ('doctor1', 'doctor1001', '김철수', 'doctor1@neuronova.hospital', 'DOCTOR', False, {
            'birthDate': date(1978, 5, 20),
            'phoneMobile': '010-2345-1001',
            'phoneOffice': '02-1234-2001',
            'hireDate': date(2015, 3, 1),
            'departmentId': 10,
            'title': '신경외과 전문의',
        }),
        ('doctor2', 'doctor2001', '이영희', 'doctor2@neuronova.hospital', 'DOCTOR', False, {
            'birthDate': date(1982, 8, 12),
            'phoneMobile': '010-3456-2001',
            'phoneOffice': '02-1234-2002',
            'hireDate': date(2018, 6, 15),
            'departmentId': 10,
            'title': '신경외과 부교수',
        }),
        ('doctor3', 'doctor3001', '박민수', 'doctor3@neuronova.hospital', 'DOCTOR', False, {
            'birthDate': date(1985, 11, 8),
            'phoneMobile': '010-4567-3001',
            'phoneOffice': '02-1234-2003',
            'hireDate': date(2020, 2, 1),
            'departmentId': 11,
            'title': '신경과 전문의',
        }),
        ('doctor4', 'doctor4001', '최지은', 'doctor4@neuronova.hospital', 'DOCTOR', False, {
            'birthDate': date(1988, 2, 25),
            'phoneMobile': '010-5678-4001',
            'phoneOffice': '02-1234-2004',
            'hireDate': date(2021, 9, 1),
            'departmentId': 12,
            'title': '영상의학과 전문의',
        }),
        ('doctor5', 'doctor5001', '정현우', 'doctor5@neuronova.hospital', 'DOCTOR', False, {
            'birthDate': date(1990, 7, 3),
            'phoneMobile': '010-6789-5001',
            'phoneOffice': '02-1234-2005',
            'hireDate': date(2022, 3, 1),
            'departmentId': 10,
            'title': '신경외과 레지던트 4년차',
        }),
        ('nurse1', 'nurse1001', '홍수진', 'nurse1@neuronova.hospital', 'NURSE', False, {
            'birthDate': date(1992, 4, 18),
            'phoneMobile': '010-7890-6001',
            'phoneOffice': '02-1234-3001',
            'hireDate': date(2019, 5, 1),
            'departmentId': 20,
            'title': '신경외과 병동 수간호사',
        }),
        ('nurse2', 'nurse2001', '김미영', 'nurse2@neuronova.hospital', 'NURSE', False, {
            'birthDate': date(1994, 7, 12),
            'phoneMobile': '010-7890-6002',
            'phoneOffice': '02-1234-3002',
            'hireDate': date(2020, 3, 1),
            'departmentId': 20,
            'title': '신경외과 병동 간호사',
        }),
        ('nurse3', 'nurse3001', '박지현', 'nurse3@neuronova.hospital', 'NURSE', False, {
            'birthDate': date(1996, 11, 25),
            'phoneMobile': '010-7890-6003',
            'phoneOffice': '02-1234-3003',
            'hireDate': date(2021, 9, 1),
            'departmentId': 21,
            'title': '신경과 외래 간호사',
        }),
        # PATIENT 역할 사용자 (5명) - 환자 테이블과 연결됨
        ('patient1', 'patient1001', '김철수', 'patient1@example.com', 'PATIENT', False, {
            'birthDate': date(1981, 1, 15),
            'phoneMobile': '010-1234-5678',
            'phoneOffice': None,
            'hireDate': None,
            'departmentId': None,
            'title': None,
        }),
        ('patient2', 'patient2001', '이영희', 'patient2@example.com', 'PATIENT', False, {
            'birthDate': date(1988, 3, 20),
            'phoneMobile': '010-2345-6789',
            'phoneOffice': None,
            'hireDate': None,
            'departmentId': None,
            'title': None,
        }),
        ('patient3', 'patient3001', '박민수', 'patient3@example.com', 'PATIENT', False, {
            'birthDate': date(1974, 5, 8),
            'phoneMobile': '010-3456-7890',
            'phoneOffice': None,
            'hireDate': None,
            'departmentId': None,
            'title': None,
        }),
        ('patient4', 'patient4001', '최지은', 'patient4@example.com', 'PATIENT', False, {
            'birthDate': date(1997, 6, 25),
            'phoneMobile': '010-4567-8901',
            'phoneOffice': None,
            'hireDate': None,
            'departmentId': None,
            'title': None,
        }),
        ('patient5', 'patient5001', '정현우', 'patient5@example.com', 'PATIENT', False, {
            'birthDate': date(1965, 9, 12),
            'phoneMobile': '010-5678-9012',
            'phoneOffice': None,
            'hireDate': None,
            'departmentId': None,
            'title': None,
        }),
        ('ris1', 'ris1001', '강민호', 'ris1@neuronova.hospital', 'RIS', False, {
            'birthDate': date(1987, 6, 22),
            'phoneMobile': '010-9012-8001',
            'phoneOffice': '02-1234-4001',
            'hireDate': date(2017, 8, 1),
            'departmentId': 30,
            'title': '영상의학과 방사선사',
        }),
        ('ris2', 'ris2001', '이준혁', 'ris2@neuronova.hospital', 'RIS', False, {
            'birthDate': date(1990, 3, 15),
            'phoneMobile': '010-9012-8002',
            'phoneOffice': '02-1234-4002',
            'hireDate': date(2019, 6, 1),
            'departmentId': 30,
            'title': '영상의학과 방사선사',
        }),
        ('ris3', 'ris3001', '최수빈', 'ris3@neuronova.hospital', 'RIS', False, {
            'birthDate': date(1993, 8, 28),
            'phoneMobile': '010-9012-8003',
            'phoneOffice': '02-1234-4003',
            'hireDate': date(2021, 2, 1),
            'departmentId': 30,
            'title': '영상의학과 방사선사',
        }),
        ('lis1', 'lis1001', '윤서연', 'lis1@neuronova.hospital', 'LIS', False, {
            'birthDate': date(1991, 12, 5),
            'phoneMobile': '010-0123-9001',
            'phoneOffice': '02-1234-5001',
            'hireDate': date(2020, 4, 15),
            'departmentId': 31,
            'title': '진단검사의학과 임상병리사',
        }),
        ('lis2', 'lis2001', '정다은', 'lis2@neuronova.hospital', 'LIS', False, {
            'birthDate': date(1989, 5, 10),
            'phoneMobile': '010-0123-9002',
            'phoneOffice': '02-1234-5002',
            'hireDate': date(2018, 9, 1),
            'departmentId': 31,
            'title': '진단검사의학과 임상병리사',
        }),
        ('lis3', 'lis3001', '한승우', 'lis3@neuronova.hospital', 'LIS', False, {
            'birthDate': date(1995, 1, 20),
            'phoneMobile': '010-0123-9003',
            'phoneOffice': '02-1234-5003',
            'hireDate': date(2022, 1, 1),
            'departmentId': 31,
            'title': '진단검사의학과 임상병리사',
        }),
    ]

    created_count = 0
    profile_count = 0

    for login_id, password, name, email, role_code, is_staff, profile_data in test_users:
        user = User.objects.filter(login_id=login_id).first()

        if user:
            print(f"  존재: {login_id}")
            # 기존 사용자에도 프로필이 없으면 생성
            if not hasattr(user, 'profile') or not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(user=user, **profile_data)
                profile_count += 1
                print(f"    → 프로필 추가: {login_id}")
            continue

        try:
            role = Role.objects.filter(code=role_code).first()
            user = User(
                login_id=login_id,
                name=name,
                email=email,
                is_staff=is_staff,
                is_active=True,
                role=role
            )
            user.set_password(password)
            user.save()

            # UserProfile 생성
            UserProfile.objects.create(user=user, **profile_data)

            created_count += 1
            profile_count += 1
            print(f"  생성: {login_id} / {password} (프로필 포함)")
        except Exception as e:
            print(f"  오류 ({login_id}): {e}")

    print(f"[OK] 테스트 사용자 설정 완료 ({created_count}개 생성, 프로필 {profile_count}개)")
    return True


def load_menu_permission_seed():
    """
    메뉴/권한 시드 데이터 로드

    메뉴 그룹 구조:
    ├── DASHBOARD
    ├── PATIENT: PATIENT_LIST, PATIENT_DETAIL, PATIENT_CARE, ENCOUNTER_LIST
    ├── OCS: OCS_STATUS, OCS_CREATE, OCS_MANAGE
    ├── IMAGING: IMAGE_VIEWER, OCS_RIS, OCS_RIS_DETAIL, RIS_DASHBOARD, RIS_RESULT_UPLOAD
    ├── LAB: LAB_RESULT_VIEW, LAB_RESULT_UPLOAD, OCS_LIS, OCS_LIS_DETAIL, LIS_PROCESS_STATUS
    ├── AI_SUMMARY: AI_REQUEST_LIST, AI_REQUEST_CREATE, AI_REQUEST_DETAIL
    ├── NURSE_RECEPTION
    └── ADMIN: ADMIN_USER, ADMIN_USER_DETAIL, ADMIN_ROLE, ADMIN_MENU_PERMISSION, ADMIN_AUDIT_LOG, ADMIN_SYSTEM_MONITOR
    """
    print("\n[1단계] 메뉴/권한 시드 데이터 로드...")

    from apps.menus.models import Menu
    from apps.accounts.models import Permission, Role

    # 변경 사항 추적을 위한 딕셔너리
    changes = {
        'Permission': {'before': 0, 'created': 0},
        'Menu': {'before': 0, 'created': 0},
        'MenuPermission': {'before': 0, 'created': 0},
        'MenuLabel': {'before': 0, 'created': 0},
    }

    changes['Permission']['before'] = Permission.objects.count()
    changes['Menu']['before'] = Menu.objects.count()

    print(f"  기존 데이터: 메뉴 {changes['Menu']['before']}개, 권한 {changes['Permission']['before']}개")
    print("  메뉴/권한 데이터 동기화 중...")

    # ========== 권한 데이터 ==========
    permissions_data = [
        ('DASHBOARD', '대시보드', '대시보드 화면 접근'),
        ('PATIENT', '환자', '환자 메뉴'),
        ('PATIENT_LIST', '환자 목록', '환자 목록 화면'),
        ('PATIENT_DETAIL', '환자 상세', '환자 상세 화면'),
        ('PATIENT_CARE', '환자 진료', '환자 진료 화면 접근'),
        ('ENCOUNTER_LIST', '진료 예약', '진료 예약/목록 화면'),
        ('OCS', '검사 오더', '검사 오더 메뉴'),
        ('OCS_STATUS', '검사 현황', '검사 오더 현황 조회 (간호사/관리자용)'),
        ('OCS_CREATE', '오더 생성', '검사 오더 생성 화면'),
        ('OCS_MANAGE', '오더 관리', '의사용 검사 오더 관리'),
        ('OCS_RIS', '영상 워크리스트', 'RIS 작업자용 영상 오더 처리'),
        ('OCS_RIS_DETAIL', '영상 검사 상세', 'RIS 영상 검사 상세 페이지'),
        ('RIS_DASHBOARD', '판독 현황 대시보드', 'RIS 전체 판독 현황 대시보드'),
        ('RIS_RESULT_UPLOAD', '영상 결과 업로드', '외부 영상 결과 업로드 화면'),
        ('OCS_LIS', '검사 워크리스트', 'LIS 작업자용 검사 오더 처리'),
        ('OCS_LIS_DETAIL', '검사 결과 상세', 'LIS 검사 결과 상세 페이지'),
        ('LIS_PROCESS_STATUS', '결과 처리 상태', 'LIS 업로드 데이터 처리 상태 모니터링'),
        ('NURSE_RECEPTION', '진료 접수 현황', '간호사용 진료 접수 현황 페이지'),
        ('IMAGING', '영상', '영상 메뉴'),
        ('IMAGE_VIEWER', '영상 조회', '영상 조회 화면'),
        ('RIS_WORKLIST', '판독 Worklist', 'RIS 판독 Worklist 화면'),
        ('LAB', '검사', '검사 메뉴'),
        ('LAB_RESULT_VIEW', '검사 결과 조회', '검사 결과 조회 화면'),
        ('LAB_RESULT_UPLOAD', '검사 결과 업로드', '검사 결과 업로드 화면'),
        ('AI_SUMMARY', 'AI 분석 요약', 'AI 분석 요약 화면'),
        ('AI_REQUEST_LIST', 'AI 분석 요청 목록', 'AI 분석 요청 목록 화면'),
        ('AI_REQUEST_CREATE', 'AI 분석 요청 생성', 'AI 분석 요청 생성 화면'),
        ('AI_REQUEST_DETAIL', 'AI 분석 요청 상세', 'AI 분석 요청 상세 화면'),
        ('ADMIN', '관리자', '관리자 메뉴'),
        ('ADMIN_USER', '사용자 관리', '사용자 관리 화면'),
        ('ADMIN_USER_DETAIL', '사용자 관리 상세', '사용자 상세 화면'),
        ('ADMIN_ROLE', '역할 관리', '역할 관리 화면'),
        ('ADMIN_MENU_PERMISSION', '메뉴 권한 관리', '메뉴 권한 관리 화면'),
        ('ADMIN_AUDIT_LOG', '접근 감사 로그', '접근 감사 로그 화면'),
        ('ADMIN_SYSTEM_MONITOR', '시스템 모니터링', '시스템 모니터링 화면'),
    ]

    permission_map = {}
    for code, name, description in permissions_data:
        perm, created = Permission.objects.get_or_create(
            code=code,
            defaults={'name': name, 'description': description}
        )
        permission_map[code] = perm
        if created:
            changes['Permission']['created'] += 1

    print(f"  권한 생성: {changes['Permission']['created']}개")

    # ========== 메뉴 데이터 ==========
    # 업데이트 추적 리스트
    menu_updates = []

    # 메뉴 생성 헬퍼 함수 (기존 레코드도 parent_id, order 업데이트)
    def create_menu(menu_id, **kwargs):
        menu, created = Menu.objects.get_or_create(id=menu_id, defaults=kwargs)
        if created:
            changes['Menu']['created'] += 1
        else:
            # 기존 레코드 업데이트 (parent, order 등)
            update_fields = []
            update_details = []
            if 'parent' in kwargs and menu.parent != kwargs['parent']:
                menu.parent = kwargs['parent']
                update_fields.append('parent')
            if 'parent_id' in kwargs and menu.parent_id != kwargs['parent_id']:
                menu.parent_id = kwargs['parent_id']
                update_fields.append('parent_id')
            if 'order' in kwargs and menu.order != kwargs['order']:
                old_order = menu.order
                menu.order = kwargs['order']
                update_fields.append('order')
                update_details.append(f"order: {old_order} → {kwargs['order']}")
            if update_fields:
                menu.save(update_fields=update_fields)
                changes['Menu']['updated'] = changes['Menu'].get('updated', 0) + 1
                menu_updates.append({'code': menu.code, 'details': update_details or update_fields})
        return menu, created

    # 최상위 메뉴
    menu_admin, _ = create_menu(1, code='ADMIN', path=None, icon='settings', order=7, is_active=True)
    menu_ai, _ = create_menu(2, code='AI_SUMMARY', path='/ai', icon='brain', order=6, is_active=True)
    menu_dashboard, _ = create_menu(3, code='DASHBOARD', path='/dashboard', icon='home', order=1, is_active=True)
    menu_imaging, _ = create_menu(4, code='IMAGING', path=None, icon=None, group_label='영상', order=4, is_active=True)
    menu_lab, _ = create_menu(5, code='LAB', path=None, icon=None, group_label='검사', order=5, is_active=True)
    menu_ocs, _ = create_menu(6, code='OCS', path=None, icon=None, group_label='검사 오더', order=3, is_active=True)
    menu_patient, _ = create_menu(7, code='PATIENT', path=None, icon=None, group_label='환자', order=2, is_active=True)

    # Admin 하위
    create_menu(8, code='ADMIN_AUDIT_LOG', path='/admin/audit', order=4, is_active=True, parent=menu_admin)
    create_menu(9, code='ADMIN_MENU_PERMISSION', path='/admin/permissions', order=3, is_active=True, parent=menu_admin)
    create_menu(10, code='ADMIN_ROLE', path='/admin/roles', order=2, is_active=True, parent=menu_admin)
    create_menu(11, code='ADMIN_SYSTEM_MONITOR', path='/admin/monitor', order=5, is_active=True, parent=menu_admin)
    create_menu(12, code='ADMIN_USER', path='/admin/users', order=1, is_active=True, parent=menu_admin)
    menu_admin_user_detail, _ = create_menu(13, code='ADMIN_USER_DETAIL', path='/admin/users/:id', breadcrumb_only=True, order=1, is_active=True, parent_id=12)

    # Imaging 하위
    create_menu(14, code='IMAGE_VIEWER', path='/imaging', icon='image', order=1, is_active=True, parent=menu_imaging)
    # RIS_WORKLIST 비활성화 - OCS_RIS와 중복되므로 사용하지 않음
    create_menu(15, code='RIS_WORKLIST', path='/ris/worklist', icon='x-ray', order=2, is_active=False, parent=menu_imaging)

    # Lab 하위
    create_menu(17, code='LAB_RESULT_VIEW', path='/lab', icon='book', order=1, is_active=True, parent=menu_lab)

    # OCS 하위 (검사 오더)
    create_menu(18, code='OCS_CREATE', path='/ocs/create', breadcrumb_only=True, order=2, is_active=True, parent=menu_ocs)
    create_menu(19, code='OCS_STATUS', path='/ocs/status', icon='clipboard', order=1, is_active=True, parent=menu_ocs)
    menu_ocs_manage, _ = create_menu(23, code='OCS_MANAGE', path='/ocs/manage', icon='file-medical', order=3, is_active=True, parent=menu_ocs)

    # Patient 하위
    create_menu(20, code='PATIENT_LIST', path='/patients', order=1, is_active=True, parent=menu_patient)
    create_menu(21, code='PATIENT_DETAIL', path='/patients/:patientId', breadcrumb_only=True, order=1, is_active=True, parent_id=20)
    create_menu(22, code='PATIENT_CARE', path='/patientsCare', order=2, is_active=True, parent=menu_patient)
    create_menu(36, code='ENCOUNTER_LIST', path='/encounters', order=3, is_active=True, parent=menu_patient)

    # OCS_RIS: IMAGING 그룹 (영상과용)
    menu_ocs_ris, _ = create_menu(24, code='OCS_RIS', path='/ocs/ris', icon='x-ray', order=3, is_active=True, parent=menu_imaging)

    # OCS_LIS: LAB 그룹 (검사과용)
    menu_ocs_lis, _ = create_menu(25, code='OCS_LIS', path='/ocs/lis', icon='flask', order=3, is_active=True, parent=menu_lab)

    # OCS 상세 페이지 메뉴 (breadcrumb_only)
    create_menu(26, code='OCS_RIS_DETAIL', path='/ocs/ris/:ocsId', icon='x-ray', breadcrumb_only=True, order=1, is_active=True, parent=menu_ocs_ris)
    create_menu(27, code='OCS_LIS_DETAIL', path='/ocs/lis/:ocsId', icon='flask', breadcrumb_only=True, order=1, is_active=True, parent=menu_ocs_lis)

    # 간호사 진료 접수 메뉴
    create_menu(28, code='NURSE_RECEPTION', path='/nurse/reception', icon='clipboard-list', order=30, is_active=True, parent=None)

    # RIS Dashboard 메뉴 (IMAGING 그룹) - process-status로 경로 통일
    create_menu(30, code='RIS_DASHBOARD', path='/ocs/ris/process-status', icon='chart-bar', order=4, is_active=True, parent=menu_imaging)

    # RIS Result Upload 메뉴 (IMAGING 그룹)
    create_menu(32, code='RIS_RESULT_UPLOAD', path='/ris/upload', icon='upload', order=5, is_active=True, parent=menu_imaging)

    # LIS Process Status 메뉴 (LAB 그룹)
    create_menu(31, code='LIS_PROCESS_STATUS', path='/ocs/lis/process-status', icon='tasks', order=4, is_active=True, parent=menu_lab)

    # LIS Result Upload 메뉴 (LAB 그룹)
    create_menu(16, code='LAB_RESULT_UPLOAD', path='/lab/upload', icon='upload', order=5, is_active=True, parent=menu_lab)

    # AI 추론 요청 메뉴 (AI_SUMMARY 하위)
    menu_ai_request, _ = create_menu(33, code='AI_REQUEST_LIST', path='/ai/requests', icon='list', order=1, is_active=True, parent=menu_ai)
    create_menu(34, code='AI_REQUEST_CREATE', path='/ai/requests/create', breadcrumb_only=True, order=2, is_active=True, parent=menu_ai_request)
    create_menu(35, code='AI_REQUEST_DETAIL', path='/ai/requests/:id', breadcrumb_only=True, order=3, is_active=True, parent=menu_ai_request)

    print(f"  메뉴 생성: {changes['Menu']['created']}개 (전체: {Menu.objects.count()}개)")
    if menu_updates:
        print(f"  메뉴 업데이트: {len(menu_updates)}개")
        for update in menu_updates:
            details = ', '.join(update['details']) if isinstance(update['details'][0], str) else ', '.join(update['details'])
            print(f"    - {update['code']}: {details}")

    # ========== 메뉴-권한 매핑 (MenuPermission) ==========
    from apps.menus.models import MenuPermission

    changes['MenuPermission']['before'] = MenuPermission.objects.count()

    # path가 있는 모든 메뉴에 대해 동일 code의 권한 매핑 (breadcrumb_only 포함)
    for menu in Menu.objects.filter(path__isnull=False):
        if menu.code in permission_map:
            _, created = MenuPermission.objects.get_or_create(
                menu=menu,
                permission=permission_map[menu.code]
            )
            if created:
                changes['MenuPermission']['created'] += 1

    print(f"  메뉴-권한 매핑: {changes['MenuPermission']['created']}개 (전체: {MenuPermission.objects.count()}개)")

    # ========== 메뉴 라벨 (MenuLabel) ==========
    from apps.menus.models import MenuLabel

    changes['MenuLabel']['before'] = MenuLabel.objects.count()

    menu_labels_data = [
        # DASHBOARD
        (3, 'DEFAULT', '대시보드'),
        (3, 'DOCTOR', '의사 대시보드'),
        (3, 'NURSE', '간호 대시보드'),
        # PATIENT
        (7, 'DEFAULT', '환자'),
        (20, 'DEFAULT', '환자 목록'),
        (21, 'DEFAULT', '환자 상세'),
        (22, 'DEFAULT', '환자 진료'),
        (36, 'DEFAULT', '진료 예약'),
        # OCS (검사 오더)
        (6, 'DEFAULT', '검사 오더'),
        (6, 'DOCTOR', '검사 오더'),
        (6, 'NURSE', '검사 현황'),
        (19, 'DEFAULT', '검사 현황'),  # 간호사/관리자용 - 전체 조회
        (18, 'DEFAULT', '오더 생성'),
        (23, 'DEFAULT', '오더 관리'),  # 의사용 - 본인 오더 관리
        (23, 'DOCTOR', '내 오더 관리'),
        (24, 'DEFAULT', '영상 워크리스트'),
        (25, 'DEFAULT', '검사 워크리스트'),
        (26, 'DEFAULT', '영상 검사 상세'),
        (27, 'DEFAULT', '검사 결과 상세'),
        # 간호사
        (28, 'DEFAULT', '진료 접수 현황'),
        (28, 'NURSE', '진료 접수'),
        # LIS Alert
        (29, 'DEFAULT', '검사 결과 Alert'),
        (29, 'LIS', '결과 Alert'),
        # RIS Dashboard
        (30, 'DEFAULT', '영상 판독 상세'),
        (30, 'RIS', '영상 판독 상세'),
        # RIS Result Upload
        (32, 'DEFAULT', '영상 결과 업로드'),
        (32, 'RIS', '영상 결과 업로드'),
        # LIS Process Status
        (31, 'DEFAULT', 'LIS 검사 상세'),
        (31, 'LIS', 'LIS 검사 상세'),
        # IMAGING
        (4, 'DEFAULT', '영상'),
        (14, 'DEFAULT', '영상 조회'),
        (15, 'DEFAULT', '판독 Worklist'),
        # AI
        (2, 'DEFAULT', 'AI 분석 요약'),
        (33, 'DEFAULT', 'AI 분석 요청'),
        (33, 'DOCTOR', 'AI 분석 요청'),
        (34, 'DEFAULT', 'AI 분석 요청 생성'),
        (35, 'DEFAULT', 'AI 분석 요청 상세'),
        # LAB
        (5, 'DEFAULT', '검사'),
        (17, 'DEFAULT', '검사 조회'),  # 검사 결과 조회 → 검사 조회
        (16, 'DEFAULT', '검사 결과 업로드'),  # breadcrumb_only - OCS에서 이동
        # ADMIN
        (1, 'DEFAULT', '관리자'),
        (12, 'DEFAULT', '사용자 관리'),
        (13, 'DEFAULT', '사용자 관리 상세조회'),
        (10, 'DEFAULT', '역할 권한 관리'),
        (9, 'DEFAULT', '메뉴 권한 관리'),
        (8, 'DEFAULT', '접근 감사 로그'),
        (11, 'DEFAULT', '시스템 모니터링'),
    ]

    for menu_id, role, text in menu_labels_data:
        try:
            menu = Menu.objects.get(id=menu_id)
            _, created = MenuLabel.objects.get_or_create(
                menu=menu,
                role=role,
                defaults={'text': text}
            )
            if created:
                changes['MenuLabel']['created'] += 1
        except Menu.DoesNotExist:
            pass

    print(f"  메뉴 라벨: {changes['MenuLabel']['created']}개 (전체: {MenuLabel.objects.count()}개)")

    # ========== 역할별 권한 매핑 (RolePermission - Menu 연결) ==========
    from apps.accounts.models import RolePermission

    # 메뉴 code → Menu 객체 매핑
    menu_map = {menu.code: menu for menu in Menu.objects.all()}

    role_menu_permissions = {
        'SYSTEMMANAGER': list(menu_map.keys()),  # 모든 메뉴
        'ADMIN': [
            'DASHBOARD', 'PATIENT', 'PATIENT_LIST', 'PATIENT_DETAIL', 'PATIENT_CARE', 'ENCOUNTER_LIST',
            'OCS', 'OCS_STATUS', 'OCS_CREATE', 'OCS_MANAGE',
            'OCS_RIS', 'OCS_RIS_DETAIL', 'OCS_LIS', 'OCS_LIS_DETAIL',
            'IMAGING', 'IMAGE_VIEWER', 'RIS_WORKLIST', 'RIS_DASHBOARD', 'RIS_RESULT_UPLOAD',
            'LAB', 'LAB_RESULT_VIEW', 'LAB_RESULT_UPLOAD', 'LIS_PROCESS_STATUS',
            'AI_SUMMARY', 'AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL',
            'NURSE_RECEPTION',
            'ADMIN', 'ADMIN_USER', 'ADMIN_USER_DETAIL', 'ADMIN_ROLE', 'ADMIN_MENU_PERMISSION', 'ADMIN_AUDIT_LOG', 'ADMIN_SYSTEM_MONITOR'
        ],
        'DOCTOR': ['DASHBOARD', 'PATIENT_LIST', 'PATIENT_DETAIL', 'PATIENT_CARE', 'ENCOUNTER_LIST', 'OCS_STATUS', 'OCS_CREATE', 'OCS_MANAGE', 'IMAGE_VIEWER', 'RIS_WORKLIST', 'LAB_RESULT_VIEW', 'AI_SUMMARY', 'AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL'],
        'NURSE': ['DASHBOARD', 'PATIENT_LIST', 'PATIENT_DETAIL', 'ENCOUNTER_LIST', 'OCS_STATUS', 'IMAGE_VIEWER', 'LAB_RESULT_VIEW', 'NURSE_RECEPTION'],  # PATIENT_CARE 제거 (DOCTOR, SYSTEMMANAGER만)
        'RIS': ['DASHBOARD', 'IMAGE_VIEWER', 'RIS_WORKLIST', 'OCS_RIS', 'OCS_RIS_DETAIL', 'RIS_DASHBOARD', 'RIS_RESULT_UPLOAD'],
        'LIS': ['DASHBOARD', 'LAB_RESULT_VIEW', 'LAB_RESULT_UPLOAD', 'OCS_LIS', 'OCS_LIS_DETAIL', 'LIS_PROCESS_STATUS'],
    }

    for role_code, menu_codes in role_menu_permissions.items():
        try:
            role = Role.objects.get(code=role_code)
            # 기존 RolePermission 삭제 후 새로 생성
            RolePermission.objects.filter(role=role).delete()
            created_count = 0
            for menu_code in menu_codes:
                if menu_code in menu_map:
                    RolePermission.objects.create(
                        role=role,
                        permission=menu_map[menu_code]  # permission 필드가 Menu를 참조
                    )
                    created_count += 1
            print(f"  {role_code}: {created_count}개 메뉴 권한 설정")
        except Role.DoesNotExist:
            print(f"  경고: {role_code} 역할이 없습니다")

    # ========== 변경 요약 출력 ==========
    print("\n  [결과 요약]")
    for table, counts in changes.items():
        created = counts['created']
        if created > 0:
            print(f"  결과: {table} 테이블에 {created}개가 추가되었습니다.")
        else:
            print(f"  결과: {table} 테이블에 변경 없음 (기존 {counts['before']}개)")

    print(f"\n[OK] 메뉴/권한 시드 완료")
    return True


def create_dummy_patients(target_count=30, force=False):
    """더미 환자 데이터 생성"""
    print(f"\n[2단계] 환자 데이터 생성 (목표: {target_count}명)...")

    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = Patient.objects.filter(is_deleted=False).count()
    if existing_count >= target_count and not force:
        print(f"[SKIP] 이미 {existing_count}명의 환자가 존재합니다.")
        return True

    # 등록자 (슈퍼유저 또는 첫 번째 사용자)
    registered_by = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not registered_by:
        print("[ERROR] 사용자가 없습니다.")
        return False

    # 더미 환자 데이터
    dummy_patients = [
        {"name": "김철수", "birth_date": timezone.now().date() - timedelta(days=365*45), "gender": "M", "phone": "010-1234-5678", "ssn": "7801011234567", "blood_type": "A+", "allergies": ["페니실린"], "chronic_diseases": ["고혈압"], "address": "서울특별시 강남구 테헤란로 123"},
        {"name": "이영희", "birth_date": timezone.now().date() - timedelta(days=365*38), "gender": "F", "phone": "010-2345-6789", "ssn": "8603151234568", "blood_type": "B+", "allergies": [], "chronic_diseases": ["당뇨"], "address": "서울특별시 서초구 서초대로 456"},
        {"name": "박민수", "birth_date": timezone.now().date() - timedelta(days=365*52), "gender": "M", "phone": "010-3456-7890", "ssn": "7205201234569", "blood_type": "O+", "allergies": ["조영제"], "chronic_diseases": ["고혈압", "당뇨"], "address": "경기도 성남시 분당구 판교로 789"},
        {"name": "최지은", "birth_date": timezone.now().date() - timedelta(days=365*29), "gender": "F", "phone": "010-4567-8901", "ssn": "9506101234560", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 송파구 올림픽로 321"},
        {"name": "정현우", "birth_date": timezone.now().date() - timedelta(days=365*61), "gender": "M", "phone": "010-5678-9012", "ssn": "6309251234561", "blood_type": "A-", "allergies": ["아스피린"], "chronic_diseases": ["고혈압", "고지혈증"], "address": "서울특별시 마포구 월드컵로 654"},
        {"name": "강미라", "birth_date": timezone.now().date() - timedelta(days=365*34), "gender": "F", "phone": "010-6789-0123", "ssn": "9002051234562", "blood_type": "B-", "allergies": [], "chronic_diseases": [], "address": "인천광역시 연수구 센트럴로 987"},
        {"name": "윤서준", "birth_date": timezone.now().date() - timedelta(days=365*47), "gender": "M", "phone": "010-7890-1234", "ssn": "7707151234563", "blood_type": "O-", "allergies": ["설파제"], "chronic_diseases": [], "address": "경기도 고양시 일산동구 중앙로 147"},
        {"name": "임수진", "birth_date": timezone.now().date() - timedelta(days=365*55), "gender": "F", "phone": "010-8901-2345", "ssn": "6912201234564", "blood_type": "AB-", "allergies": ["페니실린", "조영제"], "chronic_diseases": ["당뇨", "고혈압"], "address": "서울특별시 강동구 천호대로 258"},
        {"name": "한지우", "birth_date": timezone.now().date() - timedelta(days=365*26), "gender": "O", "phone": "010-9012-3456", "ssn": "9808301234565", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "서울특별시 관악구 관악로 369"},
        {"name": "오민지", "birth_date": timezone.now().date() - timedelta(days=365*42), "gender": "F", "phone": "010-0123-4567", "ssn": "8204101234566", "blood_type": "B+", "allergies": [], "chronic_diseases": ["고지혈증"], "address": "경기도 수원시 영통구 광교로 741"},
        {"name": "서동훈", "birth_date": timezone.now().date() - timedelta(days=365*58), "gender": "M", "phone": "010-1111-2222", "ssn": "6605121234567", "blood_type": "A+", "allergies": [], "chronic_diseases": ["고혈압"], "address": "부산광역시 해운대구 해운대로 100"},
        {"name": "배수연", "birth_date": timezone.now().date() - timedelta(days=365*31), "gender": "F", "phone": "010-2222-3333", "ssn": "9303152234567", "blood_type": "O+", "allergies": ["페니실린"], "chronic_diseases": [], "address": "대구광역시 수성구 수성로 200"},
        {"name": "조성민", "birth_date": timezone.now().date() - timedelta(days=365*49), "gender": "M", "phone": "010-3333-4444", "ssn": "7508203234567", "blood_type": "B+", "allergies": [], "chronic_diseases": ["당뇨", "고지혈증"], "address": "광주광역시 서구 상무대로 300"},
        {"name": "신예린", "birth_date": timezone.now().date() - timedelta(days=365*27), "gender": "F", "phone": "010-4444-5555", "ssn": "9707154234567", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "대전광역시 유성구 대학로 400"},
        {"name": "권도현", "birth_date": timezone.now().date() - timedelta(days=365*65), "gender": "M", "phone": "010-5555-6666", "ssn": "5909205234567", "blood_type": "A-", "allergies": ["조영제", "아스피린"], "chronic_diseases": ["고혈압", "당뇨", "고지혈증"], "address": "울산광역시 남구 삼산로 500"},
        {"name": "황지현", "birth_date": timezone.now().date() - timedelta(days=365*36), "gender": "F", "phone": "010-6666-7777", "ssn": "8804156234567", "blood_type": "O-", "allergies": [], "chronic_diseases": [], "address": "경기도 용인시 수지구 포은대로 600"},
        {"name": "안재호", "birth_date": timezone.now().date() - timedelta(days=365*53), "gender": "M", "phone": "010-7777-8888", "ssn": "7102207234567", "blood_type": "B-", "allergies": ["설파제"], "chronic_diseases": ["고혈압"], "address": "경기도 화성시 동탄대로 700"},
        {"name": "문서아", "birth_date": timezone.now().date() - timedelta(days=365*24), "gender": "F", "phone": "010-8888-9999", "ssn": "0001158234567", "blood_type": "AB-", "allergies": [], "chronic_diseases": [], "address": "서울특별시 노원구 동일로 800"},
        {"name": "송준혁", "birth_date": timezone.now().date() - timedelta(days=365*44), "gender": "M", "phone": "010-9999-0000", "ssn": "8007209234567", "blood_type": "A+", "allergies": [], "chronic_diseases": ["당뇨"], "address": "서울특별시 영등포구 여의대로 900"},
        {"name": "류하은", "birth_date": timezone.now().date() - timedelta(days=365*33), "gender": "F", "phone": "010-1234-0000", "ssn": "9106150234568", "blood_type": "O+", "allergies": ["페니실린"], "chronic_diseases": [], "address": "경기도 성남시 중원구 성남대로 1000"},
        {"name": "장태웅", "birth_date": timezone.now().date() - timedelta(days=365*57), "gender": "M", "phone": "010-2345-0000", "ssn": "6703201234568", "blood_type": "B+", "allergies": [], "chronic_diseases": ["고혈압", "고지혈증"], "address": "인천광역시 남동구 구월로 1100"},
        {"name": "노은지", "birth_date": timezone.now().date() - timedelta(days=365*29), "gender": "F", "phone": "010-3456-0000", "ssn": "9509152234568", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "부산광역시 부산진구 중앙대로 1200"},
        {"name": "하승우", "birth_date": timezone.now().date() - timedelta(days=365*41), "gender": "M", "phone": "010-4567-0000", "ssn": "8310203234568", "blood_type": "O-", "allergies": ["조영제"], "chronic_diseases": ["당뇨"], "address": "대구광역시 달서구 달구벌대로 1300"},
        {"name": "전소희", "birth_date": timezone.now().date() - timedelta(days=365*38), "gender": "F", "phone": "010-5678-0000", "ssn": "8605154234568", "blood_type": "AB+", "allergies": [], "chronic_diseases": [], "address": "광주광역시 북구 용봉로 1400"},
        {"name": "곽민재", "birth_date": timezone.now().date() - timedelta(days=365*62), "gender": "M", "phone": "010-6789-0000", "ssn": "6204205234568", "blood_type": "B-", "allergies": ["아스피린"], "chronic_diseases": ["고혈압", "당뇨"], "address": "대전광역시 서구 둔산로 1500"},
        {"name": "우다인", "birth_date": timezone.now().date() - timedelta(days=365*25), "gender": "F", "phone": "010-7890-0000", "ssn": "9908156234568", "blood_type": "A-", "allergies": [], "chronic_diseases": [], "address": "울산광역시 중구 성남로 1600"},
        {"name": "남기훈", "birth_date": timezone.now().date() - timedelta(days=365*50), "gender": "M", "phone": "010-8901-0000", "ssn": "7406207234568", "blood_type": "O+", "allergies": [], "chronic_diseases": ["고지혈증"], "address": "세종특별자치시 한누리대로 1700"},
        {"name": "심유나", "birth_date": timezone.now().date() - timedelta(days=365*35), "gender": "F", "phone": "010-9012-0000", "ssn": "8902158234568", "blood_type": "B+", "allergies": ["설파제"], "chronic_diseases": [], "address": "제주특별자치도 제주시 연동로 1800"},
        {"name": "엄태식", "birth_date": timezone.now().date() - timedelta(days=365*68), "gender": "M", "phone": "010-0123-0000", "ssn": "5607209234568", "blood_type": "AB-", "allergies": ["페니실린", "아스피린"], "chronic_diseases": ["고혈압", "당뇨", "고지혈증"], "address": "강원도 춘천시 중앙로 1900"},
        {"name": "차준영", "birth_date": timezone.now().date() - timedelta(days=365*40), "gender": "M", "phone": "010-1122-3344", "ssn": "8405201234569", "blood_type": "A+", "allergies": [], "chronic_diseases": [], "address": "경상북도 포항시 북구 중앙로 2000"},
    ]

    created_count = 0
    skipped_count = 0

    for patient_data in dummy_patients:
        try:
            # SSN 중복 확인
            if Patient.objects.filter(ssn=patient_data['ssn']).exists():
                skipped_count += 1
                continue

            patient = Patient.objects.create(
                registered_by=registered_by,
                status='active',
                **patient_data
            )
            created_count += 1
        except IntegrityError:
            skipped_count += 1
        except Exception as e:
            print(f"  오류 ({patient_data['name']}): {e}")

    print(f"[OK] 환자 생성: {created_count}명, 스킵: {skipped_count}명")
    print(f"  현재 전체 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    return True


def create_dummy_encounters(target_count=20, force=False):
    """더미 진료 데이터 생성"""
    print(f"\n[3단계] 진료 데이터 생성 (목표: {target_count}건)...")

    from apps.encounters.models import Encounter
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = Encounter.objects.count()
    if existing_count >= target_count and not force:
        print(f"[SKIP] 이미 {existing_count}건의 진료가 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False, status='active'))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 활성 환자가 없습니다.")
        return False

    if not doctors:
        print("[WARNING] DOCTOR 역할 사용자가 없습니다. 첫 번째 사용자를 사용합니다.")
        doctors = list(User.objects.all()[:1])

    encounter_types = ['outpatient', 'inpatient', 'emergency']
    statuses = ['scheduled', 'in_progress', 'completed', 'cancelled']
    departments = ['neurology', 'neurosurgery']

    chief_complaints = [
        '두통이 심해요', '어지러움증이 계속됩니다', '손발 저림 증상',
        '기억력 감퇴', '수면 장애', '편두통', '목 통증',
        '시야 흐림', '균형 감각 이상', '근육 경련', '발작 증세'
    ]

    primary_diagnoses = [
        '뇌종양 의심', '편두통', '뇌졸중', '파킨슨병',
        '치매', '간질', '다발성 경화증', '신경통'
    ]

    # SOAP 노트 샘플 데이터
    subjective_samples = [
        '3일 전부터 지속되는 두통, 아침에 더 심함',
        '일주일간 어지러움 증상, 구역감 동반',
        '양손 저림 증상, 특히 야간에 심해짐',
        '최근 건망증이 심해졌다고 호소',
        '잠들기 어렵고 자주 깸, 피로감 호소',
        '우측 관자놀이 쪽 박동성 두통',
        '경추 부위 통증, 고개 돌릴 때 악화',
    ]

    objective_samples = [
        'BP 130/85, HR 72, BT 36.5',
        '신경학적 검사 정상, 경부 강직 없음',
        '동공 반사 정상, 안구 운동 정상',
        'Romberg test 양성, 보행 시 불안정',
        'MMT 정상, DTR 정상, 병적 반사 없음',
        'GCS 15, 의식 명료, 지남력 정상',
        '뇌 MRI: T2 고신호 병변 확인',
    ]

    assessment_samples = [
        '긴장성 두통 의심, R/O 편두통',
        '말초성 현훈 vs 중추성 현훈 감별 필요',
        '수근관 증후군 의심',
        '경도 인지장애 가능성, 치매 스크리닝 필요',
        '불면증, 수면 무호흡 가능성',
        '뇌종양 의심, 추가 검사 필요',
        '경추 디스크 탈출증 의심',
    ]

    plan_samples = [
        '뇌 MRI 촬영, 진통제 처방, 2주 후 재진',
        '청력검사, 전정기능검사 예정, 어지럼증 약물 처방',
        '신경전도검사 의뢰, 보존적 치료',
        '인지기능검사, 혈액검사 (갑상선, B12)',
        '수면다원검사 의뢰, 수면위생 교육',
        'MRI 추적검사, 신경외과 협진',
        '물리치료 의뢰, NSAIDs 처방',
    ]

    created_count = 0

    for i in range(target_count):
        days_ago = random.randint(0, 60)
        admission_date = timezone.now() - timedelta(days=days_ago)
        encounter_type = random.choice(encounter_types)

        if days_ago > 30:
            status = random.choice(['completed', 'cancelled'])
        elif days_ago > 7:
            status = random.choice(['in_progress', 'completed'])
        else:
            status = random.choice(statuses)

        discharge_date = None
        if status == 'completed':
            if encounter_type == 'outpatient':
                discharge_days = random.choice([0, 1])
            elif encounter_type == 'inpatient':
                discharge_days = random.randint(1, 14)
            else:
                discharge_days = random.randint(0, 7)
            discharge_date = admission_date + timedelta(days=discharge_days)
        elif status == 'cancelled' and random.choice([True, False]):
            discharge_date = admission_date

        # 완료된 진료는 SOAP 노트 작성
        soap_data = {}
        if status in ['completed', 'in_progress']:
            soap_data = {
                'subjective': random.choice(subjective_samples),
                'objective': random.choice(objective_samples),
                'assessment': random.choice(assessment_samples),
                'plan': random.choice(plan_samples),
            }

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
                secondary_diagnoses=random.sample(['고혈압', '당뇨', '고지혈증'], random.randint(0, 2)),
                **soap_data,
            )
            created_count += 1
        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 진료 생성: {created_count}건")

    # 오늘 예약 진료 3건 생성 (금일 예약 환자 목록 테스트용)
    print("\n[3-1단계] 오늘 예약 진료 생성...")
    from datetime import time as dt_time
    today_scheduled_count = Encounter.objects.filter(
        admission_date__date=timezone.now().date(),
        status='scheduled'
    ).count()

    # 예약 시간 목록
    scheduled_times = [dt_time(9, 0), dt_time(10, 30), dt_time(14, 0), dt_time(15, 30), dt_time(16, 0)]

    if today_scheduled_count < 3:
        for i in range(3 - today_scheduled_count):
            try:
                Encounter.objects.create(
                    patient=random.choice(patients),
                    attending_doctor=random.choice(doctors),
                    admission_date=timezone.now(),
                    scheduled_time=scheduled_times[i % len(scheduled_times)],
                    status='scheduled',
                    encounter_type='outpatient',
                    department=random.choice(departments),
                    chief_complaint=random.choice(['정기 진료', '추적 검사', '상담', '재진'])
                )
            except Exception as e:
                print(f"  오류: {e}")
        print(f"[OK] 오늘 예약 진료: {3 - today_scheduled_count}건 추가 생성")
    else:
        print(f"[SKIP] 오늘 예약 진료 이미 {today_scheduled_count}건 존재")

    print(f"  현재 전체 진료: {Encounter.objects.count()}건")
    return True


def create_dummy_imaging_with_ocs(num_orders=30, force=False):
    """더미 영상 검사 데이터 생성 (OCS 통합 버전)"""
    print(f"\n[4단계] 영상 검사 데이터 생성 - OCS 통합 (목표: {num_orders}건)...")

    from apps.ocs.models import OCS
    from apps.imaging.models import ImagingStudy
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_ocs = OCS.objects.filter(job_role='RIS').count()
    if existing_ocs >= num_orders and not force:
        print(f"[SKIP] 이미 {existing_ocs}건의 RIS 오더가 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    encounters = list(Encounter.objects.all())
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    radiologists = list(User.objects.filter(role__code__in=['RIS', 'DOCTOR']))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not radiologists:
        radiologists = doctors

    modalities = ['CT', 'MRI', 'PET', 'X-RAY']
    body_parts = ['Brain', 'Head', 'Skull', 'Neck', 'Cervical Spine']
    ocs_statuses = ['ORDERED', 'ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']
    priorities = ['urgent', 'normal']
    clinical_indications = ['headache', 'dizziness', 'seizure', 'follow-up', 'screening', 'brain tumor evaluation']

    created_count = 0

    for i in range(num_orders):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters else None
        modality = random.choice(modalities)
        body_part = random.choice(body_parts)

        days_ago = random.randint(0, 90)
        ocs_status = random.choice(ocs_statuses)

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(radiologists)

        # doctor_request 데이터
        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": f"{random.choice(clinical_indications)} - {patient.name}",
            "request_detail": f"{modality} {body_part} 촬영 요청",
            "special_instruction": random.choice(["", "조영제 사용", "조영제 없이", "긴급"]),
        }

        # worker_result 데이터 (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            tumor_detected = random.random() < 0.3
            lobes = ['frontal', 'temporal', 'parietal', 'occipital']
            hemispheres = ['left', 'right']

            worker_result = {
                "_template": "RIS",
                "_version": "1.0",
                "_confirmed": ocs_status == 'CONFIRMED',
                "findings": "Mass lesion identified." if tumor_detected else "No acute intracranial abnormality.",
                "impression": "Brain tumor suspected." if tumor_detected else "Normal study.",
                "recommendation": "Further evaluation recommended." if tumor_detected else "",
                "tumor": {
                    "detected": tumor_detected,
                    "location": {"lobe": random.choice(lobes), "hemisphere": random.choice(hemispheres)} if tumor_detected else {},
                    "size": {"max_diameter_cm": round(random.uniform(1.0, 4.0), 1), "volume_cc": round(random.uniform(2.0, 30.0), 1)} if tumor_detected else {}
                },
                "dicom": {
                    "study_uid": f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1000, 9999)}",
                    "series_count": random.randint(1, 5),
                    "instance_count": random.randint(20, 200)
                },
                "work_notes": []
            }

        try:
            with transaction.atomic():
                # OCS 생성
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='RIS',
                    job_type=modality,
                    ocs_status=ocs_status,
                    priority=random.choice(priorities),
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                )

                # ImagingStudy 생성 (OCS에 연결)
                scheduled_at = None
                performed_at = None

                if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    scheduled_at = timezone.now() - timedelta(days=days_ago) + timedelta(days=random.randint(1, 3))

                if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
                    performed_at = scheduled_at + timedelta(hours=random.randint(1, 24)) if scheduled_at else None

                study = ImagingStudy.objects.create(
                    ocs=ocs,
                    modality=modality,
                    body_part=body_part,
                    study_uid=worker_result.get('dicom', {}).get('study_uid') if worker_result else None,
                    series_count=worker_result.get('dicom', {}).get('series_count', 0) if worker_result else 0,
                    instance_count=worker_result.get('dicom', {}).get('instance_count', 0) if worker_result else 0,
                    scheduled_at=scheduled_at,
                    performed_at=performed_at,
                )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS + ImagingStudy 생성: {created_count}건")
    print(f"  현재 전체 OCS(RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  현재 전체 ImagingStudy: {ImagingStudy.objects.count()}건")
    return True


def create_dummy_lis_orders(num_orders=30, force=False):
    """더미 LIS (검사) 오더 생성"""
    print(f"\n[5단계] 검사 오더 데이터 생성 - LIS (목표: {num_orders}건)...")

    from apps.ocs.models import OCS
    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_ocs = OCS.objects.filter(job_role='LIS').count()
    if existing_ocs >= num_orders and not force:
        print(f"[SKIP] 이미 {existing_ocs}건의 LIS 오더가 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    encounters = list(Encounter.objects.all())
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    lab_workers = list(User.objects.filter(role__code__in=['LIS', 'DOCTOR']))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not lab_workers:
        lab_workers = doctors

    # 검사 항목 (BLOOD, GENETIC, PROTEIN 포함)
    test_types = [
        # BLOOD 검사
        'CBC', 'BMP', 'CMP', 'Lipid Panel', 'LFT', 'RFT',
        'Thyroid Panel', 'Coagulation', 'Urinalysis', 'Tumor Markers',
        # GENETIC 검사 (유전자)
        'GENETIC', 'RNA_SEQ', 'DNA_SEQ', 'GENE_PANEL',
        # PROTEIN 검사 (단백질)
        'PROTEIN', 'PROTEIN_PANEL', 'BIOMARKER',
    ]
    ocs_statuses = ['ORDERED', 'ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']
    priorities = ['urgent', 'normal']

    created_count = 0

    for i in range(num_orders):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters else None
        test_type = random.choice(test_types)

        # 날짜 분포: 1주일 ~ 6개월 (180일)
        days_ago = random.randint(0, 180)

        # 상태 결정: 오래된 데이터일수록 CONFIRMED 확률 높음
        if days_ago > 90:  # 3개월 이상
            ocs_status = random.choice(['CONFIRMED', 'CONFIRMED', 'CONFIRMED', 'CANCELLED'])
        elif days_ago > 30:  # 1개월 이상
            ocs_status = random.choice(['RESULT_READY', 'CONFIRMED', 'CONFIRMED'])
        elif days_ago > 7:  # 1주일 이상
            ocs_status = random.choice(['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED'])
        else:  # 최근 1주일
            ocs_status = random.choice(ocs_statuses)

        # 작업자 (ACCEPTED 이후에만)
        worker = None
        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            worker = random.choice(lab_workers)

        # doctor_request 데이터
        doctor_request = {
            "_template": "default",
            "_version": "1.0",
            "clinical_info": f"{patient.name} - 정기검사",
            "request_detail": f"{test_type} 검사 요청",
            "special_instruction": random.choice(["", "공복 필요", "아침 첫 소변", ""]),
        }

        # worker_result 데이터 (RESULT_READY 이후에만)
        worker_result = {}
        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            is_abnormal = random.random() < 0.2

            # 검사 결과 샘플
            test_results = []
            if test_type == 'CBC':
                test_results = [
                    {"code": "WBC", "name": "백혈구", "value": str(round(random.uniform(4.0, 11.0), 1)), "unit": "10^3/uL", "reference": "4.0-11.0", "is_abnormal": False},
                    {"code": "RBC", "name": "적혈구", "value": str(round(random.uniform(4.0, 6.0), 2)), "unit": "10^6/uL", "reference": "4.0-6.0", "is_abnormal": False},
                    {"code": "HGB", "name": "혈색소", "value": str(round(random.uniform(12.0, 17.0), 1)), "unit": "g/dL", "reference": "12.0-17.0", "is_abnormal": False},
                    {"code": "PLT", "name": "혈소판", "value": str(random.randint(150, 400)), "unit": "10^3/uL", "reference": "150-400", "is_abnormal": False},
                ]
            elif test_type == 'Tumor Markers':
                cea_val = round(random.uniform(0.5, 5.0), 2) if not is_abnormal else round(random.uniform(5.1, 20.0), 2)
                afp_val = round(random.uniform(0.5, 10.0), 2) if not is_abnormal else round(random.uniform(10.1, 50.0), 2)
                test_results = [
                    {"code": "CEA", "name": "암배아항원", "value": str(cea_val), "unit": "ng/mL", "reference": "0-5.0", "is_abnormal": cea_val > 5.0},
                    {"code": "AFP", "name": "알파태아단백", "value": str(afp_val), "unit": "ng/mL", "reference": "0-10.0", "is_abnormal": afp_val > 10.0},
                ]
            elif test_type in ['GENETIC', 'RNA_SEQ', 'DNA_SEQ', 'GENE_PANEL']:
                # 유전자 검사 결과
                gene_mutations = [
                    {"gene_name": "IDH1", "mutation_type": "R132H" if is_abnormal else "Wild Type", "status": "Mutant" if is_abnormal else "Normal", "allele_frequency": round(random.uniform(0.1, 0.5), 2) if is_abnormal else None, "clinical_significance": "Favorable prognosis" if is_abnormal else "N/A"},
                    {"gene_name": "TP53", "mutation_type": random.choice(["Missense", "Nonsense", "Wild Type"]), "status": random.choice(["Mutant", "Normal"]), "allele_frequency": round(random.uniform(0.05, 0.3), 2), "clinical_significance": "Variable"},
                    {"gene_name": "MGMT", "mutation_type": "Methylated" if random.random() > 0.5 else "Unmethylated", "status": "Methylated" if random.random() > 0.5 else "Unmethylated", "allele_frequency": None, "clinical_significance": "TMZ response predictor"},
                    {"gene_name": "EGFR", "mutation_type": random.choice(["Amplified", "Normal"]), "status": random.choice(["Amplified", "Normal"]), "allele_frequency": None, "clinical_significance": "GBM marker"},
                ]
                test_results = [{"code": "GENE", "name": "유전자 변이 분석", "value": "분석 완료", "unit": "", "reference": "", "is_abnormal": is_abnormal}]
                worker_result = {
                    "_template": "LIS", "_version": "1.0", "_confirmed": ocs_status == 'CONFIRMED',
                    "test_type": "GENETIC", "test_results": test_results, "gene_mutations": gene_mutations,
                    "summary": "유전자 변이 검출됨" if is_abnormal else "유전자 변이 없음",
                    "interpretation": "IDH1 변이 양성 - 예후 양호" if is_abnormal else "특이 변이 없음", "_custom": {}
                }
            elif test_type in ['PROTEIN', 'PROTEIN_PANEL', 'BIOMARKER']:
                # 단백질 검사 결과
                protein_markers = [
                    {"marker_name": "GFAP", "value": round(random.uniform(0.1, 5.0), 2), "unit": "ng/mL", "reference_range": "0-2.0", "is_abnormal": random.random() > 0.7, "interpretation": "Astrocyte marker"},
                    {"marker_name": "S100B", "value": round(random.uniform(0.01, 0.5), 3), "unit": "ug/L", "reference_range": "0-0.15", "is_abnormal": random.random() > 0.6, "interpretation": "Brain injury marker"},
                    {"marker_name": "NSE", "value": round(random.uniform(5, 25), 1), "unit": "ng/mL", "reference_range": "0-16.3", "is_abnormal": random.random() > 0.7, "interpretation": "Neuroendocrine marker"},
                ]
                test_results = [{"code": "PROT", "name": "단백질 마커 분석", "value": "분석 완료", "unit": "", "reference": "", "is_abnormal": is_abnormal}]
                worker_result = {
                    "_template": "LIS", "_version": "1.0", "_confirmed": ocs_status == 'CONFIRMED',
                    "test_type": "PROTEIN", "test_results": test_results, "protein_markers": protein_markers,
                    "protein": "GFAP, S100B 상승" if is_abnormal else "정상 범위",
                    "summary": "단백질 마커 이상" if is_abnormal else "정상 범위",
                    "interpretation": "뇌종양 관련 마커 상승 소견" if is_abnormal else "특이 소견 없음", "_custom": {}
                }
            else:
                # 일반 검사
                test_results = [
                    {"code": "TEST1", "name": f"{test_type} 항목1", "value": str(round(random.uniform(50, 150), 1)), "unit": "mg/dL", "reference": "50-150", "is_abnormal": False},
                    {"code": "TEST2", "name": f"{test_type} 항목2", "value": str(round(random.uniform(10, 50), 1)), "unit": "U/L", "reference": "10-50", "is_abnormal": False},
                ]

            # GENETIC/PROTEIN은 위에서 이미 worker_result 설정됨
            if test_type not in ['GENETIC', 'RNA_SEQ', 'DNA_SEQ', 'GENE_PANEL', 'PROTEIN', 'PROTEIN_PANEL', 'BIOMARKER']:
                worker_result = {
                "_template": "LIS",
                "_version": "1.0",
                "_confirmed": ocs_status == 'CONFIRMED',
                "test_results": test_results,
                "summary": "이상 소견 있음" if is_abnormal else "정상 범위",
                "interpretation": "추가 검사 권장" if is_abnormal else "특이 소견 없음",
                "_custom": {}
            }

        # 타임스탬프 계산
        base_time = timezone.now() - timedelta(days=days_ago)
        timestamps = {
            'accepted_at': None,
            'in_progress_at': None,
            'result_ready_at': None,
            'confirmed_at': None,
            'cancelled_at': None,
        }

        if ocs_status in ['ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['accepted_at'] = base_time + timedelta(hours=random.randint(1, 4))

        if ocs_status in ['IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']:
            timestamps['in_progress_at'] = base_time + timedelta(hours=random.randint(4, 12))

        if ocs_status in ['RESULT_READY', 'CONFIRMED']:
            timestamps['result_ready_at'] = base_time + timedelta(hours=random.randint(12, 48))

        if ocs_status == 'CONFIRMED':
            timestamps['confirmed_at'] = base_time + timedelta(hours=random.randint(48, 72))

        if ocs_status == 'CANCELLED':
            timestamps['cancelled_at'] = base_time + timedelta(hours=random.randint(1, 24))

        try:
            with transaction.atomic():
                # OCS 생성
                ocs = OCS.objects.create(
                    patient=patient,
                    doctor=doctor,
                    worker=worker,
                    encounter=encounter,
                    job_role='LIS',
                    job_type=test_type,
                    ocs_status=ocs_status,
                    priority=random.choice(priorities),
                    doctor_request=doctor_request,
                    worker_result=worker_result,
                    ocs_result=True if ocs_status == 'CONFIRMED' else None,
                    accepted_at=timestamps['accepted_at'],
                    in_progress_at=timestamps['in_progress_at'],
                    result_ready_at=timestamps['result_ready_at'],
                    confirmed_at=timestamps['confirmed_at'],
                    cancelled_at=timestamps['cancelled_at'],
                )
                # created_at은 auto_now_add이므로 별도 업데이트
                OCS.objects.filter(pk=ocs.pk).update(created_at=base_time)
                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS(LIS) 생성: {created_count}건")
    print(f"  현재 전체 OCS(LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    return True


def create_ai_models():
    """AI 모델 시드 데이터 생성"""
    print(f"\n[6단계] AI 모델 데이터 생성...")

    from apps.ai_inference.models import AIModel

    # 기존 데이터 확인
    existing_count = AIModel.objects.count()
    if existing_count >= 3:
        print(f"[SKIP] 이미 {existing_count}개의 AI 모델이 존재합니다.")
        return True

    ai_models_data = [
        {
            "code": "M1",
            "name": "MRI 4-Channel Analysis",
            "description": "MRI 4채널(T1, T2, T1C, FLAIR) 기반 뇌종양 분석 모델",
            "ocs_sources": ["RIS"],
            "required_keys": {
                "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"]
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 300,
                "batch_size": 1,
                "gpu_required": True
            }
        },
        {
            "code": "MG",
            "name": "Genetic Analysis",
            "description": "RNA 시퀀싱 기반 유전자 분석 모델 (MGMT 메틸화, IDH 변이 등)",
            "ocs_sources": ["LIS"],
            "required_keys": {
                "LIS": ["RNA_seq"]  # job_type='GENETIC'인 OCS에서 조회
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 600,
                "batch_size": 1,
                "gpu_required": False
            }
        },
        {
            "code": "MM",
            "name": "Multimodal Analysis",
            "description": "MRI + 유전 + 단백질 통합 분석 모델 (종합 예후 예측)",
            "ocs_sources": ["RIS", "LIS"],
            "required_keys": {
                "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"],
                "LIS": ["RNA_seq", "protein"]  # job_type='GENETIC', 'PROTEIN'인 OCS에서 조회
            },
            "version": "1.0.0",
            "is_active": True,
            "config": {
                "timeout_seconds": 900,
                "batch_size": 1,
                "gpu_required": True
            }
        }
    ]

    created_count = 0
    for model_data in ai_models_data:
        model, created = AIModel.objects.get_or_create(
            code=model_data["code"],
            defaults=model_data
        )
        if created:
            created_count += 1
            print(f"  생성: {model.code} - {model.name}")
        else:
            print(f"  스킵: {model.code} (이미 존재)")

    print(f"[OK] AI 모델 생성: {created_count}개")
    print(f"  현재 전체 AI 모델: {AIModel.objects.count()}개")
    return True


def create_patient_alerts(force=False):
    """환자 주의사항 더미 데이터 생성"""
    print("\n[6단계] 환자 주의사항 데이터 생성...")

    from apps.patients.models import Patient, PatientAlert
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = PatientAlert.objects.count()
    if existing_count > 0 and not force:
        print(f"[SKIP] 이미 {existing_count}건의 주의사항이 존재합니다.")
        return True

    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    alert_samples = [
        {'alert_type': 'ALLERGY', 'severity': 'HIGH', 'title': '페니실린 알레르기', 'description': '페니실린 계열 항생제 투여 시 아나필락시스 반응 가능'},
        {'alert_type': 'ALLERGY', 'severity': 'HIGH', 'title': '조영제 알레르기', 'description': 'CT/MRI 조영제 투여 시 두드러기, 호흡곤란 발생 이력'},
        {'alert_type': 'ALLERGY', 'severity': 'MEDIUM', 'title': '아스피린 과민반응', 'description': 'NSAIDs 사용 시 주의 필요'},
        {'alert_type': 'CONTRAINDICATION', 'severity': 'HIGH', 'title': '와파린 복용 중', 'description': '항응고제 복용 중 - 출혈 위험'},
        {'alert_type': 'CONTRAINDICATION', 'severity': 'HIGH', 'title': 'MRI 금기', 'description': '심장 박동기 삽입 환자 - MRI 촬영 금지'},
        {'alert_type': 'PRECAUTION', 'severity': 'MEDIUM', 'title': '낙상 주의', 'description': '보행 장애로 인한 낙상 위험'},
        {'alert_type': 'PRECAUTION', 'severity': 'LOW', 'title': '당뇨 환자', 'description': '혈당 관리 필요 - 공복 검사 시 저혈당 주의'},
        {'alert_type': 'OTHER', 'severity': 'LOW', 'title': '보호자 연락 필요', 'description': '중요 결정 시 보호자 동의 필요'},
    ]

    created_count = 0

    # 각 환자에게 0~3개의 주의사항 추가
    for patient in patients:
        num_alerts = random.randint(0, 3)
        if num_alerts == 0:
            continue

        selected_alerts = random.sample(alert_samples, min(num_alerts, len(alert_samples)))
        for alert_data in selected_alerts:
            try:
                PatientAlert.objects.create(
                    patient=patient,
                    alert_type=alert_data['alert_type'],
                    severity=alert_data['severity'],
                    title=alert_data['title'],
                    description=alert_data['description'],
                    is_active=True,
                    created_by=random.choice(doctors),
                )
                created_count += 1
            except Exception as e:
                print(f"  오류: {e}")

    print(f"[OK] 환자 주의사항 생성: {created_count}건")
    print(f"  현재 전체 주의사항: {PatientAlert.objects.count()}건")
    return True


def update_encounters_with_soap(force=False):
    """기존 진료에 SOAP 데이터 추가"""
    print("\n[7단계] 진료 SOAP 데이터 업데이트...")

    from apps.encounters.models import Encounter

    # 완료/진행중 진료만 업데이트
    encounters = Encounter.objects.filter(
        status__in=['completed', 'in_progress'],
        subjective='',  # SOAP 데이터가 없는 진료만
    )

    if not encounters.exists() and not force:
        print("[SKIP] 업데이트 대상 진료가 없거나 이미 SOAP 데이터가 있습니다.")
        return True

    soap_samples = [
        {
            'subjective': '두통이 2주 전부터 시작되어 점점 심해지고 있습니다. 오심, 구토 동반됨.',
            'objective': 'V/S: BP 130/85, HR 78, BT 36.5\nNeuro exam: Pupil reflex (+/+), MMT 5/5',
            'assessment': '두통 - 원인 감별 필요 (Tension type vs. Secondary headache)',
            'plan': '1. Brain MRI with contrast 처방\n2. 진통제 처방 (Acetaminophen 500mg tid)\n3. 2주 후 F/U',
        },
        {
            'subjective': '왼쪽 팔다리 저림 증상이 3일 전부터 있습니다. 힘이 빠지는 느낌도 있음.',
            'objective': 'V/S: 안정적\nNeuro exam: Lt. side weakness (MMT 4/5), sensory decreased',
            'assessment': 'Rt. hemisphere lesion 의심 - Brain tumor vs. Infarction R/O',
            'plan': '1. Brain CT & MRI 시행\n2. Lab 검사 (CBC, Coag, Chemistry)\n3. 신경외과 협진 의뢰',
        },
        {
            'subjective': '경련이 어제 발생했습니다. 의식 소실 동반, 약 2분간 지속.',
            'objective': 'V/S: 안정적\nEEG: Abnormal findings at Rt. temporal area',
            'assessment': 'New onset seizure - Structural lesion 감별 필요',
            'plan': '1. Anti-epileptic drug 시작 (Levetiracetam 500mg bid)\n2. Brain MRI 시행\n3. 발작 일지 작성 교육',
        },
        {
            'subjective': '정기 추적 검사 방문. 특이 증상 없음.',
            'objective': 'V/S: 정상\nNeuro exam: No focal neurological deficit',
            'assessment': 'Brain tumor s/p treatment - Stable disease',
            'plan': '1. Brain MRI F/U 예약\n2. 현재 투약 유지\n3. 3개월 후 재방문',
        },
    ]

    updated_count = 0
    for encounter in encounters[:15]:  # 최대 15건만 업데이트
        soap = random.choice(soap_samples)
        encounter.subjective = soap['subjective']
        encounter.objective = soap['objective']
        encounter.assessment = soap['assessment']
        encounter.plan = soap['plan']
        encounter.save()
        updated_count += 1

    print(f"[OK] 진료 SOAP 데이터 업데이트: {updated_count}건")
    return True


def link_patient_user_account():
    """
    PATIENT 역할 사용자를 환자(Patient) 테이블과 연결

    patient1~5 계정 → 환자 테이블의 김철수, 이영희, 박민수, 최지은, 정현우와 연결
    """
    print("\n[추가 단계] 환자 계정-환자 테이블 연결...")

    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # PATIENT 역할 사용자 ↔ 환자 이름 매핑 (5명)
    patient_mapping = [
        ('patient1', '김철수'),
        ('patient2', '이영희'),
        ('patient3', '박민수'),
        ('patient4', '최지은'),
        ('patient5', '정현우'),
    ]

    linked_count = 0
    skipped_count = 0

    for login_id, patient_name in patient_mapping:
        # 사용자 확인
        patient_user = User.objects.filter(login_id=login_id, role__code='PATIENT').first()
        if not patient_user:
            print(f"  [SKIP] {login_id} 사용자가 없거나 PATIENT 역할이 아닙니다.")
            skipped_count += 1
            continue

        # 이미 연결된 환자가 있는지 확인
        if Patient.objects.filter(user=patient_user).exists():
            linked_patient = Patient.objects.get(user=patient_user)
            print(f"  [OK] 이미 연결됨: {login_id} → {linked_patient.name}")
            skipped_count += 1
            continue

        # 환자 찾기
        patient = Patient.objects.filter(name=patient_name, is_deleted=False, user__isnull=True).first()
        if not patient:
            print(f"  [SKIP] {patient_name} 환자가 없거나 이미 연결됨")
            skipped_count += 1
            continue

        # 연결
        patient.user = patient_user
        patient.save()
        linked_count += 1
        print(f"  [OK] 연결: {login_id} → {patient.name} ({patient.patient_number})")

    print(f"[OK] 환자 계정 연결 완료 (연결: {linked_count}건, 스킵: {skipped_count}건)")
    print(f"     테스트 계정: patient1~5 / patient1001~patient5001")
    return True


def reset_base_data():
    """기본 더미 데이터 삭제 (base 영역만)"""
    print("\n[RESET] 기본 더미 데이터 삭제 중...")

    from apps.ocs.models import OCS, OCSHistory
    from apps.imaging.models import ImagingStudy
    from apps.encounters.models import Encounter
    from apps.patients.models import Patient, PatientAlert
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.ai_inference.models import AIInferenceRequest, AIInferenceResult, AIInferenceLog
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp
    from apps.prescriptions.models import Prescription, PrescriptionItem

    # 삭제 순서: 의존성 역순
    # 환자 주의사항 삭제
    patient_alert_count = PatientAlert.objects.count()
    PatientAlert.objects.all().delete()
    print(f"  PatientAlert: {patient_alert_count}건 삭제")

    # 처방 삭제 (Patient 참조)
    prescription_item_count = PrescriptionItem.objects.count()
    PrescriptionItem.objects.all().delete()
    print(f"  PrescriptionItem: {prescription_item_count}건 삭제")

    prescription_count = Prescription.objects.count()
    Prescription.objects.all().delete()
    print(f"  Prescription: {prescription_count}건 삭제")

    # AI 로그/결과/요청 삭제 (추가 데이터지만 base 데이터에 의존)
    ai_log_count = AIInferenceLog.objects.count()
    AIInferenceLog.objects.all().delete()
    print(f"  AIInferenceLog: {ai_log_count}건 삭제")

    ai_result_count = AIInferenceResult.objects.count()
    AIInferenceResult.objects.all().delete()
    print(f"  AIInferenceResult: {ai_result_count}건 삭제")

    ai_request_count = AIInferenceRequest.objects.count()
    AIInferenceRequest.objects.all().delete()
    print(f"  AIInferenceRequest: {ai_request_count}건 삭제")

    # 치료 세션/계획 삭제 (추가 데이터지만 base 데이터에 의존)
    treatment_session_count = TreatmentSession.objects.count()
    TreatmentSession.objects.all().delete()
    print(f"  TreatmentSession: {treatment_session_count}건 삭제")

    treatment_plan_count = TreatmentPlan.objects.count()
    TreatmentPlan.objects.all().delete()
    print(f"  TreatmentPlan: {treatment_plan_count}건 삭제")

    # 경과 기록 삭제 (추가 데이터지만 base 데이터에 의존)
    followup_count = FollowUp.objects.count()
    FollowUp.objects.all().delete()
    print(f"  FollowUp: {followup_count}건 삭제")

    # 기본 데이터 삭제
    ocs_history_count = OCSHistory.objects.count()
    OCSHistory.objects.all().delete()
    print(f"  OCSHistory: {ocs_history_count}건 삭제")

    imaging_count = ImagingStudy.objects.count()
    ImagingStudy.objects.all().delete()
    print(f"  ImagingStudy: {imaging_count}건 삭제")

    ocs_count = OCS.objects.count()
    OCS.objects.all().delete()
    print(f"  OCS: {ocs_count}건 삭제")

    encounter_count = Encounter.objects.count()
    Encounter.objects.all().delete()
    print(f"  Encounter: {encounter_count}건 삭제")

    patient_count = Patient.objects.count()
    Patient.objects.all().delete()
    print(f"  Patient: {patient_count}건 삭제")

    # 불필요한 메뉴 삭제 (PATIENT_IMAGING_HISTORY 등)
    deprecated_menus = ['PATIENT_IMAGING_HISTORY']
    for menu_code in deprecated_menus:
        try:
            menu = Menu.objects.filter(code=menu_code).first()
            if menu:
                MenuLabel.objects.filter(menu=menu).delete()
                MenuPermission.objects.filter(menu=menu).delete()
                menu.delete()
                print(f"  Menu '{menu_code}' 삭제됨")
        except Exception as e:
            print(f"  Menu '{menu_code}' 삭제 실패: {e}")

    print("[OK] 기본 더미 데이터 삭제 완료")


def print_summary():
    """기본 더미 데이터 요약"""
    print("\n" + "="*60)
    print("기본 더미 데이터 생성 완료!")
    print("="*60)

    from apps.patients.models import Patient, PatientAlert
    from apps.encounters.models import Encounter
    from apps.imaging.models import ImagingStudy
    from apps.ocs.models import OCS
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.accounts.models import Permission
    from apps.ai_inference.models import AIModel

    print(f"\n[통계 - 기본 데이터]")
    print(f"  - 메뉴: {Menu.objects.count()}개")
    print(f"  - 메뉴 라벨: {MenuLabel.objects.count()}개")
    print(f"  - 메뉴-권한 매핑: {MenuPermission.objects.count()}개")
    print(f"  - 권한: {Permission.objects.count()}개")
    print(f"  - 환자: {Patient.objects.filter(is_deleted=False).count()}명")
    print(f"  - 환자 주의사항: {PatientAlert.objects.count()}건")
    print(f"  - 진료: {Encounter.objects.count()}건")
    print(f"  - 진료 (SOAP 포함): {Encounter.objects.exclude(subjective='').count()}건")
    print(f"  - OCS (RIS): {OCS.objects.filter(job_role='RIS').count()}건")
    print(f"  - OCS (LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    print(f"  - 영상 검사: {ImagingStudy.objects.count()}건")
    print(f"  - AI 모델: {AIModel.objects.count()}개")

    print(f"\n[다음 단계]")
    print(f"  추가 데이터 생성:")
    print(f"    python setup_dummy_data_2_add.py")
    print(f"")
    print(f"  또는 전체 실행:")
    print(f"    python setup_dummy_data.py")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 기본 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='기존 데이터 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    parser.add_argument('--menu', action='store_true', help='메뉴/권한만 업데이트 (네비게이션 바 반영)')
    parser.add_argument('-y', '--yes', action='store_true', help='확인 없이 자동 실행 (비대화형 모드)')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 기본 더미 데이터 생성 (1/2)")
    print("="*60)

    # --menu 옵션: 메뉴/권한만 업데이트
    if args.menu:
        print("\n[메뉴/권한 업데이트 모드]")
        load_menu_permission_seed()
        print("\n" + "="*60)
        print("메뉴/권한 업데이트 완료!")
        print("="*60)
        return

    # --reset 옵션: 기존 데이터 삭제
    if args.reset:
        if args.yes:
            # 비대화형 모드: 확인 없이 삭제
            reset_base_data()
        else:
            confirm = input("\n정말 기존 데이터를 모두 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                reset_base_data()
            else:
                print("삭제 취소됨")
                sys.exit(0)

    force = args.reset or args.force  # reset 시에는 force=True

    # 역할 생성
    setup_roles()

    # 슈퍼유저 생성
    setup_superuser()

    # 테스트 사용자 생성
    setup_test_users()

    # 메뉴/권한 시드 데이터 로드
    load_menu_permission_seed()

    # 환자 데이터 생성
    create_dummy_patients(30, force=force)

    # 진료 데이터 생성
    create_dummy_encounters(20, force=force)

    # 영상 검사 데이터 생성 (OCS 통합)
    create_dummy_imaging_with_ocs(30, force=force)

    # 검사 오더 생성 (LIS) - 30건 (다양한 날짜 분포)
    create_dummy_lis_orders(30, force=force)

    # AI 모델 시드 데이터 생성
    create_ai_models()

    # 환자 주의사항 생성
    create_patient_alerts(force=force)

    # 진료 SOAP 데이터 업데이트
    update_encounters_with_soap(force=force)

    # 환자 계정-환자 테이블 연결 (PATIENT 역할용 마이페이지)
    link_patient_user_account()

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
