#!/usr/bin/env python
"""
Brain Tumor CDSS - 데이터베이스 설정 스크립트 (1/2)

이 스크립트는 마이그레이션을 실행하고 기본 사용자/메뉴/권한 데이터를 설정합니다.
중복 실행에도 안전합니다.

사용법:
    python setup_database.py

실행 후:
    python setup_dummy_data.py  (더미 데이터 생성)
"""

import os
import sys
import subprocess
from pathlib import Path

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 프로젝트 루트 디렉토리로 이동
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)


def run_command(cmd, description, check=True):
    """명령어 실행 및 결과 출력"""
    print(f"\n{'='*60}")
    print(f"[실행] {description}")
    print(f"{'='*60}")
    print(f"$ {cmd}")
    print()

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"[OK] {description} 완료")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} 실패")
        print(f"  Exit code: {e.returncode}")
        return False


def create_database_if_not_exists():
    """데이터베이스가 없으면 생성"""
    print("\n[0단계] 데이터베이스 존재 확인...")

    # dbconn.env에서 설정 읽기
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


def check_database_connection():
    """데이터베이스 연결 확인"""
    print("\n[1단계] 데이터베이스 연결 확인...")

    try:
        import django
        django.setup()

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("[OK] 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"[ERROR] 데이터베이스 연결 실패: {e}")
        print("  config/settings.py의 DATABASES 설정을 확인하세요.")
        return False


def run_migrations():
    """마이그레이션 실행 (순서대로)"""
    print("\n[2단계] 마이그레이션 실행...")

    # 마이그레이션 파일 생성 (필요한 경우)
    if not run_command("python manage.py makemigrations --no-input", "마이그레이션 파일 생성", check=False):
        print("  (새 마이그레이션이 없을 수 있음)")

    # 순서대로 마이그레이션 실행 (의존성 해결)
    migrations = [
        ("contenttypes", "contenttypes 앱"),
        ("auth", "auth 앱"),
        ("accounts", "accounts 앱"),
        ("menus", "menus 앱"),
        ("patients", "patients 앱"),
        ("encounters", "encounters 앱"),
        ("ocs", "ocs 앱"),
        ("imaging", "imaging 앱"),
        ("audit", "audit 앱"),
        (None, "나머지 모든 앱"),  # 나머지 전체 실행
    ]

    for app, desc in migrations:
        if app:
            cmd = f"python manage.py migrate {app} --no-input"
        else:
            cmd = "python manage.py migrate --no-input"

        if not run_command(cmd, desc):
            if app:
                print(f"  경고: {app} 마이그레이션 실패 - 계속 진행")
            else:
                return False

    return True


def create_superuser():
    """슈퍼유저 생성 (없는 경우)"""
    print("\n[3단계] 슈퍼유저 확인...")

    import django
    django.setup()

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.filter(is_superuser=True).exists():
        superuser = User.objects.filter(is_superuser=True).first()
        print(f"[OK] 슈퍼유저 이미 존재: {superuser.login_id}")
        return True

    print("슈퍼유저가 없습니다. 기본 슈퍼유저를 생성합니다.")

    # Role 생성 (없는 경우)
    from apps.accounts.models import Role
    system_role, _ = Role.objects.get_or_create(
        code='SYSTEMMANAGER',
        defaults={'name': 'System Manager', 'description': '시스템 관리자', 'is_active': True}
    )

    # 슈퍼유저 생성
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


def setup_roles():
    """기본 역할 생성"""
    print("\n[4단계] 기본 역할 설정...")

    import django
    django.setup()

    from apps.accounts.models import Role

    roles = [
        ('SYSTEMMANAGER', 'System Manager', '시스템 관리자'),
        ('ADMIN', 'Admin', '병원 관리자'),
        ('DOCTOR', 'Doctor', '의사'),
        ('NURSE', 'nurse', '간호사'),
        ('PATIENT', 'Patient', '환자'),
        ('RIS', 'Ris', '영상과'),
        ('LIS', 'Lis', '검사과'),
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


def setup_test_users():
    """테스트 사용자 생성"""
    print("\n[5단계] 테스트 사용자 설정...")

    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role

    User = get_user_model()

    # (login_id, password, name, role_code, is_staff)
    test_users = [
        ('admin', 'admin001', '병원관리자', 'ADMIN', True),
        ('doctor1', 'doctor001', '김철수 의사', 'DOCTOR', False),
        ('doctor2', 'doctor002', '이영희 의사', 'DOCTOR', False),
        ('doctor3', 'doctor003', '박민수 의사', 'DOCTOR', False),
        ('doctor4', 'doctor004', '최지은 의사', 'DOCTOR', False),
        ('doctor5', 'doctor005', '정현우 의사', 'DOCTOR', False),
        ('nurse1', 'nurse001', '간호사', 'NURSE', False),
        ('patient1', 'patient001', '환자', 'PATIENT', False),
        ('ris1', 'ris001', '영상과', 'RIS', False),
        ('lis1', 'lis001', '검사과', 'LIS', False),
    ]

    created_count = 0
    for login_id, password, name, role_code, is_staff in test_users:
        if User.objects.filter(login_id=login_id).exists():
            print(f"  존재: {login_id}")
            continue

        try:
            role = Role.objects.filter(code=role_code).first()
            user = User(
                login_id=login_id,
                name=name,
                is_staff=is_staff,
                is_active=True,
                role=role
            )
            user.set_password(password)
            user.save()
            created_count += 1
            print(f"  생성: {login_id} / {password}")
        except Exception as e:
            print(f"  오류 ({login_id}): {e}")

    print(f"[OK] 테스트 사용자 설정 완료 ({created_count}개 생성)")
    return True


def load_seed_data():
    """시드 데이터 로드 (메뉴/권한)"""
    print("\n[6단계] 시드 데이터 확인...")

    import django
    django.setup()

    from apps.menus.models import Menu
    from apps.accounts.models import Permission

    menu_count = Menu.objects.count()
    permission_count = Permission.objects.count()

    if menu_count > 0 and permission_count > 0:
        print(f"[OK] 시드 데이터 이미 존재 (메뉴: {menu_count}개, 권한: {permission_count}개)")
        print("  메뉴/권한 시드를 다시 로드하려면:")
        print("  mysql -u root -p brain_tumor < 메뉴-권한\\ 매핑\\ seed\\ 데이터.sql")
        return True

    print("[경고] 메뉴/권한 시드 데이터가 없습니다.")
    print("  다음 명령을 실행하세요:")
    print("  mysql -u root -p brain_tumor < 메뉴-권한\\ 매핑\\ seed\\ 데이터.sql")
    return True


def print_summary():
    """설정 결과 요약"""
    print("\n" + "="*60)
    print("데이터베이스 설정 완료!")
    print("="*60)

    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role, Permission
    from apps.menus.models import Menu

    User = get_user_model()

    print(f"\n[통계]")
    print(f"  - 사용자: {User.objects.count()}명")
    print(f"  - 역할: {Role.objects.count()}개")
    print(f"  - 권한: {Permission.objects.count()}개")
    print(f"  - 메뉴: {Menu.objects.count()}개")

    print(f"\n[다음 단계]")
    print(f"  1. (선택) SQL 시드 데이터 로드:")
    print(f"     mysql -u root -p brain_tumor < 메뉴-권한\\ 매핑\\ seed\\ 데이터.sql")
    print(f"")
    print(f"  2. 더미 데이터 생성:")
    print(f"     python setup_dummy_data.py")
    print(f"")
    print(f"  3. 서버 실행:")
    print(f"     python manage.py runserver")


def main():
    """메인 실행 함수"""
    print("="*60)
    print("Brain Tumor CDSS - 데이터베이스 설정")
    print("="*60)

    # 0. DB가 없으면 자동 생성
    if not create_database_if_not_exists():
        print("\n[WARNING] 데이터베이스 자동 생성 실패")
        print("수동으로 생성하세요:")
        print("  mysql -u root -p -e \"CREATE DATABASE brain_tumor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci\"")

    # 1. DB 연결 확인
    if not check_database_connection():
        sys.exit(1)

    # 2. 마이그레이션 실행
    if not run_migrations():
        print("\n[WARNING] 마이그레이션에 문제가 있습니다.")
        print("수동으로 실행하세요:")
        print("  python manage.py migrate")

    # 3. 슈퍼유저 생성
    create_superuser()

    # 4. 기본 역할 설정
    setup_roles()

    # 5. 테스트 사용자 생성
    setup_test_users()

    # 6. 시드 데이터 확인
    load_seed_data()

    # 결과 요약
    print_summary()


if __name__ == '__main__':
    main()
