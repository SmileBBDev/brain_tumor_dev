#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (2/2)

이 스크립트는 테스트용 더미 데이터를 생성합니다.
중복 실행에도 안전합니다.

사용법:
    python setup_dummy_data.py          # 기존 데이터 유지, 부족분만 추가
    python setup_dummy_data.py --reset  # 기존 데이터 삭제 후 새로 생성

선행 조건:
    python setup_database.py  (마이그레이션 및 기본 데이터)
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import random

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 프로젝트 루트 디렉토리로 이동
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)

# Django 초기화
import django
django.setup()

from django.utils import timezone
from django.db import IntegrityError, transaction
import argparse


def check_prerequisites():
    """선행 조건 확인"""
    print("\n[0단계] 선행 조건 확인...")

    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role

    User = get_user_model()

    # 사용자 확인
    if not User.objects.exists():
        print("[ERROR] 사용자가 없습니다.")
        print("  먼저 실행하세요: python setup_database.py")
        return False

    # 역할 확인
    if not Role.objects.filter(code='DOCTOR').exists():
        print("[ERROR] DOCTOR 역할이 없습니다.")
        print("  먼저 실행하세요: python setup_database.py")
        return False

    print("[OK] 선행 조건 충족")
    return True


def load_menu_permission_seed():
    """
    메뉴/권한 시드 데이터 로드

    메뉴 그룹 구조 (Option A - 역할 기반 분리):
    ├── DASHBOARD
    ├── PATIENT: PATIENT_LIST, PATIENT_DETAIL, PATIENT_CARE
    ├── ORDER: ORDER_LIST, ORDER_CREATE, OCS_ORDER
    ├── IMAGING: IMAGE_VIEWER, RIS_WORKLIST, OCS_RIS, OCS_RIS_DETAIL, RIS_DASHBOARD
    ├── LAB: LAB_RESULT_VIEW, LAB_RESULT_UPLOAD, OCS_LIS, OCS_LIS_DETAIL, LIS_PROCESS_STATUS
    ├── AI_SUMMARY
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
        ('ORDER', '검사 오더', '검사 오더 메뉴'),
        ('ORDER_LIST', '오더 목록', '검사 오더 목록 화면'),
        ('ORDER_CREATE', '오더 생성', '검사 오더 생성 화면'),
        ('OCS_ORDER', '검사 오더', '의사용 검사 오더 생성/관리'),
        ('OCS_RIS', '영상 워크리스트', 'RIS 작업자용 영상 오더 처리'),
        ('OCS_RIS_DETAIL', '영상 검사 상세', 'RIS 영상 검사 상세 페이지'),
        ('RIS_DASHBOARD', '판독 현황 대시보드', 'RIS 전체 판독 현황 대시보드'),
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
    # 메뉴 생성 헬퍼 함수 (기존 레코드도 parent_id 업데이트)
    def create_menu(menu_id, **kwargs):
        menu, created = Menu.objects.get_or_create(id=menu_id, defaults=kwargs)
        if created:
            changes['Menu']['created'] += 1
        else:
            # 기존 레코드의 parent_id가 다르면 업데이트
            update_fields = []
            if 'parent' in kwargs and menu.parent != kwargs['parent']:
                menu.parent = kwargs['parent']
                update_fields.append('parent')
            if 'parent_id' in kwargs and menu.parent_id != kwargs['parent_id']:
                menu.parent_id = kwargs['parent_id']
                update_fields.append('parent_id')
            if update_fields:
                menu.save(update_fields=update_fields)
                print(f"    [UPDATE] {menu.code}: parent_id → {menu.parent_id}")
        return menu, created

    # 최상위 메뉴
    menu_admin, _ = create_menu(1, code='ADMIN', path=None, icon='settings', order=7, is_active=True)
    menu_ai, _ = create_menu(2, code='AI_SUMMARY', path='/ai', icon='brain', order=5, is_active=True)
    menu_dashboard, _ = create_menu(3, code='DASHBOARD', path='/dashboard', icon='home', order=1, is_active=True)
    menu_imaging, _ = create_menu(4, code='IMAGING', path=None, icon=None, group_label='영상', order=4, is_active=True)
    menu_lab, _ = create_menu(5, code='LAB', path=None, icon=None, group_label='검사', order=6, is_active=True)
    menu_order, _ = create_menu(6, code='ORDER', path=None, icon=None, group_label='검사 오더', order=3, is_active=True)
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
    create_menu(16, code='LAB_RESULT_UPLOAD', path='/lab/upload', breadcrumb_only=True, order=2, is_active=True, parent=menu_lab)
    create_menu(17, code='LAB_RESULT_VIEW', path='/lab', icon='book', order=1, is_active=True, parent=menu_lab)

    # Order 하위
    create_menu(18, code='ORDER_CREATE', path='/orders/create', breadcrumb_only=True, order=2, is_active=True, parent=menu_order)
    create_menu(19, code='ORDER_LIST', path='/orders/list', icon='clipboard', order=1, is_active=True, parent=menu_order)

    # Patient 하위
    create_menu(20, code='PATIENT_LIST', path='/patients', order=1, is_active=True, parent=menu_patient)
    create_menu(21, code='PATIENT_DETAIL', path='/patients/:patientId', breadcrumb_only=True, order=1, is_active=True, parent_id=20)
    create_menu(22, code='PATIENT_CARE', path='/patients/care', order=2, is_active=True, parent=menu_patient)

    # OCS 메뉴 (역할 기반 그룹 분리)
    # OCS_ORDER: ORDER 그룹 (의사용 오더)
    menu_ocs_order, _ = create_menu(23, code='OCS_ORDER', path='/ocs/order', icon='file-medical', order=3, is_active=True, parent=menu_order)

    # OCS_RIS: IMAGING 그룹 (영상과용)
    menu_ocs_ris, _ = create_menu(24, code='OCS_RIS', path='/ocs/ris', icon='x-ray', order=3, is_active=True, parent=menu_imaging)

    # OCS_LIS: LAB 그룹 (검사과용)
    menu_ocs_lis, _ = create_menu(25, code='OCS_LIS', path='/ocs/lis', icon='flask', order=3, is_active=True, parent=menu_lab)

    # OCS 상세 페이지 메뉴 (breadcrumb_only)
    create_menu(26, code='OCS_RIS_DETAIL', path='/ocs/ris/:ocsId', icon='x-ray', breadcrumb_only=True, order=1, is_active=True, parent=menu_ocs_ris)
    create_menu(27, code='OCS_LIS_DETAIL', path='/ocs/lis/:ocsId', icon='flask', breadcrumb_only=True, order=1, is_active=True, parent=menu_ocs_lis)

    # 간호사 진료 접수 메뉴
    create_menu(28, code='NURSE_RECEPTION', path='/nurse/reception', icon='clipboard-list', order=30, is_active=True, parent=None)

    # RIS Dashboard 메뉴 (IMAGING 그룹)
    create_menu(30, code='RIS_DASHBOARD', path='/ocs/ris/dashboard', icon='chart-bar', order=4, is_active=True, parent=menu_imaging)

    # LIS Process Status 메뉴 (LAB 그룹)
    create_menu(31, code='LIS_PROCESS_STATUS', path='/ocs/lis/process-status', icon='tasks', order=4, is_active=True, parent=menu_lab)

    print(f"  메뉴 생성: {changes['Menu']['created']}개 (전체: {Menu.objects.count()}개)")

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
        # ORDER
        (6, 'DEFAULT', '검사 오더'),
        (6, 'DOCTOR', '검사 오더'),
        (6, 'NURSE', '검사 현황'),
        (19, 'DEFAULT', '검사 현황'),  # 간호사/관리자용 - 전체 조회
        (18, 'DEFAULT', '오더 생성'),
        # OCS
        (23, 'DEFAULT', '내 검사 오더'),  # 의사용 - 본인 오더만
        (23, 'DOCTOR', '내 검사 오더'),
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
        # LIS Process Status
        (31, 'DEFAULT', 'LIS 검사 상세'),
        (31, 'LIS', 'LIS 검사 상세'),
        # IMAGING
        (4, 'DEFAULT', '영상'),
        (14, 'DEFAULT', '영상 조회'),
        (15, 'DEFAULT', '판독 Worklist'),
        # AI
        (2, 'DEFAULT', 'AI 분석 요약'),
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

    # ========== 역할별 권한 매핑 ==========
    role_permissions = {
        'SYSTEMMANAGER': list(permission_map.keys()),  # 모든 권한
        'ADMIN': [
            'DASHBOARD', 'PATIENT', 'PATIENT_LIST', 'PATIENT_DETAIL', 'PATIENT_CARE',
            'ORDER', 'ORDER_LIST', 'ORDER_CREATE', 'OCS_ORDER',
            'OCS_RIS', 'OCS_RIS_DETAIL', 'OCS_LIS', 'OCS_LIS_DETAIL',
            'IMAGING', 'IMAGE_VIEWER', 'RIS_WORKLIST',
            'LAB', 'LAB_RESULT_VIEW', 'LAB_RESULT_UPLOAD',
            'AI_SUMMARY', 'NURSE_RECEPTION',
            'ADMIN', 'ADMIN_USER', 'ADMIN_USER_DETAIL', 'ADMIN_ROLE', 'ADMIN_MENU_PERMISSION', 'ADMIN_AUDIT_LOG'
        ],
        'DOCTOR': ['DASHBOARD', 'PATIENT_LIST', 'PATIENT_DETAIL', 'PATIENT_CARE', 'ORDER_LIST', 'OCS_ORDER', 'IMAGE_VIEWER', 'RIS_WORKLIST', 'AI_SUMMARY'],
        'NURSE': ['DASHBOARD', 'PATIENT_LIST', 'PATIENT_DETAIL', 'PATIENT_CARE', 'ORDER_LIST', 'IMAGE_VIEWER', 'LAB_RESULT_VIEW', 'NURSE_RECEPTION'],
        'RIS': ['DASHBOARD', 'IMAGE_VIEWER', 'RIS_WORKLIST', 'OCS_RIS', 'OCS_RIS_DETAIL', 'RIS_DASHBOARD'],
        'LIS': ['DASHBOARD', 'LAB_RESULT_VIEW', 'LAB_RESULT_UPLOAD', 'OCS_LIS', 'OCS_LIS_DETAIL', 'LIS_PROCESS_STATUS'],
    }

    for role_code, perm_codes in role_permissions.items():
        try:
            role = Role.objects.get(code=role_code)
            perms = [permission_map[code] for code in perm_codes if code in permission_map]
            role.permissions.set(perms)
            print(f"  {role_code}: {len(perms)}개 권한 설정")
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
    statuses = ['scheduled', 'in-progress', 'completed', 'cancelled']
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

    created_count = 0

    for i in range(target_count):
        days_ago = random.randint(0, 60)
        admission_date = timezone.now() - timedelta(days=days_ago)
        encounter_type = random.choice(encounter_types)

        if days_ago > 30:
            status = random.choice(['completed', 'cancelled'])
        elif days_ago > 7:
            status = random.choice(['in-progress', 'completed'])
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
            )
            created_count += 1
        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 진료 생성: {created_count}건")
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


def create_dummy_lis_orders(num_orders=20, force=False):
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

    # 검사 항목
    test_types = [
        'CBC', 'BMP', 'CMP', 'Lipid Panel', 'LFT', 'RFT',
        'Thyroid Panel', 'Coagulation', 'Urinalysis', 'Tumor Markers'
    ]
    ocs_statuses = ['ORDERED', 'ACCEPTED', 'IN_PROGRESS', 'RESULT_READY', 'CONFIRMED']
    priorities = ['urgent', 'normal']

    created_count = 0

    for i in range(num_orders):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        encounter = random.choice(encounters) if encounters else None
        test_type = random.choice(test_types)

        days_ago = random.randint(0, 60)
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
            else:
                # 일반 검사
                test_results = [
                    {"code": "TEST1", "name": f"{test_type} 항목1", "value": str(round(random.uniform(50, 150), 1)), "unit": "mg/dL", "reference": "50-150", "is_abnormal": False},
                    {"code": "TEST2", "name": f"{test_type} 항목2", "value": str(round(random.uniform(10, 50), 1)), "unit": "U/L", "reference": "10-50", "is_abnormal": False},
                ]

            worker_result = {
                "_template": "LIS",
                "_version": "1.0",
                "_confirmed": ocs_status == 'CONFIRMED',
                "test_results": test_results,
                "summary": "이상 소견 있음" if is_abnormal else "정상 범위",
                "interpretation": "추가 검사 권장" if is_abnormal else "특이 소견 없음",
                "_custom": {}
            }

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
                )
                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] OCS(LIS) 생성: {created_count}건")
    print(f"  현재 전체 OCS(LIS): {OCS.objects.filter(job_role='LIS').count()}건")
    return True


def create_dummy_treatment_plans(num_plans=15, force=False):
    """더미 치료 계획 데이터 생성"""
    print(f"\n[6단계] 치료 계획 데이터 생성 (목표: {num_plans}건)...")

    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = TreatmentPlan.objects.count()
    if existing_count >= num_plans and not force:
        print(f"[SKIP] 이미 {existing_count}건의 치료 계획이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    treatment_types = ['surgery', 'radiation', 'chemotherapy', 'observation', 'combined']
    statuses = ['draft', 'planned', 'active', 'completed', 'cancelled']

    treatment_titles = {
        'surgery': ['뇌종양 절제술', '내시경 수술', '감압술', '조직 검사'],
        'radiation': ['전뇌 방사선 치료', '정위적 방사선 수술', 'IMRT 치료', '양성자 치료'],
        'chemotherapy': ['테모졸로마이드 치료', '베바시주맙 치료', '복합 항암 요법', '면역 항암 치료'],
        'observation': ['정기 MRI 추적', '증상 모니터링', '경과 관찰'],
        'combined': ['수술 후 방사선+항암', '동시 화학방사선 요법', '복합 치료 프로토콜']
    }

    goals_templates = [
        '종양 완전 제거 및 신경학적 기능 보존',
        '종양 성장 억제 및 증상 완화',
        '재발 방지 및 생존율 향상',
        '삶의 질 유지 및 증상 관리',
        '잔존 종양 제거 및 추가 전이 예방'
    ]

    created_count = 0

    for i in range(num_plans):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        treatment_type = random.choice(treatment_types)
        status = random.choice(statuses)

        days_ago = random.randint(0, 180)
        start_date = timezone.now().date() - timedelta(days=days_ago)

        end_date = None
        if status in ['completed', 'cancelled']:
            end_date = start_date + timedelta(days=random.randint(14, 90))
        elif status == 'active':
            end_date = start_date + timedelta(days=random.randint(30, 120))

        try:
            with transaction.atomic():
                plan = TreatmentPlan.objects.create(
                    patient=patient,
                    treatment_type=treatment_type,
                    title=random.choice(treatment_titles[treatment_type]),
                    description=f"{patient.name} 환자의 {treatment_type} 치료 계획",
                    goals=random.choice(goals_templates),
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=doctor,
                    notes=f"담당의: {doctor.username}" if random.random() < 0.3 else ""
                )

                # 치료 세션 생성 (방사선, 항암의 경우)
                if treatment_type in ['radiation', 'chemotherapy'] and status in ['active', 'completed']:
                    num_sessions = random.randint(3, 8)
                    for j in range(num_sessions):
                        session_date = start_date + timedelta(days=j * 7)
                        session_status = 'completed' if session_date < timezone.now().date() else 'scheduled'

                        TreatmentSession.objects.create(
                            plan=plan,
                            session_number=j + 1,
                            scheduled_date=session_date,
                            status=session_status,
                            notes=f"세션 {j + 1}" if random.random() < 0.2 else ""
                        )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 치료 계획 생성: {created_count}건")
    print(f"  현재 전체 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  현재 전체 치료 세션: {TreatmentSession.objects.count()}건")
    return True


def create_dummy_followups(num_followups=25, force=False):
    """더미 경과 추적 데이터 생성"""
    print(f"\n[7단계] 경과 추적 데이터 생성 (목표: {num_followups}건)...")

    from apps.followup.models import FollowUp
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = FollowUp.objects.count()
    if existing_count >= num_followups and not force:
        print(f"[SKIP] 이미 {existing_count}건의 경과 기록이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    followup_types = ['routine', 'imaging', 'lab', 'symptom', 'emergency']
    clinical_statuses = ['stable', 'improved', 'deteriorated', 'recurrence', 'unknown']

    symptoms_list = [
        '두통 호소', '어지러움 증상', '시야 흐림', '손발 저림',
        '특이 증상 없음', '피로감 호소', '기억력 저하', '수면 장애',
        '오심/구토', '경련 증상'
    ]

    assessments = [
        '전반적으로 안정적인 상태 유지',
        '영상 소견상 변화 없음',
        '치료 반응 양호',
        '경미한 증상 악화 관찰',
        '추가 검사 필요',
        '현 치료 계획 유지 권고'
    ]

    plans = [
        '다음 정기 검진 예정',
        'MRI 추적 검사 예정',
        '현 치료 지속',
        '약물 용량 조절 고려',
        '전문과 협진 의뢰',
        '증상 모니터링 지속'
    ]

    created_count = 0

    for i in range(num_followups):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        followup_type = random.choice(followup_types)
        clinical_status = random.choice(clinical_statuses)

        days_ago = random.randint(0, 365)
        followup_date = timezone.now().date() - timedelta(days=days_ago)

        # 다음 방문일 (50% 확률로 설정)
        next_followup = None
        if random.random() < 0.5:
            next_followup = followup_date + timedelta(days=random.randint(30, 90))

        try:
            FollowUp.objects.create(
                patient=patient,
                followup_date=followup_date,
                followup_type=followup_type,
                clinical_status=clinical_status,
                kps_score=random.choice([None, 70, 80, 90, 100]),
                ecog_score=random.choice([None, 0, 1, 2]),
                weight=round(random.uniform(50, 85), 1) if random.random() < 0.6 else None,
                blood_pressure_systolic=random.randint(110, 140) if random.random() < 0.4 else None,
                blood_pressure_diastolic=random.randint(70, 90) if random.random() < 0.4 else None,
                symptoms=random.choice(symptoms_list) if random.random() < 0.7 else "",
                physical_exam="이학적 검사 시행" if random.random() < 0.3 else "",
                assessment=random.choice(assessments),
                plan=random.choice(plans),
                next_followup_date=next_followup,
                recorded_by=doctor
            )
            created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 경과 기록 생성: {created_count}건")
    print(f"  현재 전체 경과 기록: {FollowUp.objects.count()}건")
    return True


def create_dummy_ai_requests(num_requests=10, force=False):
    """더미 AI 추론 요청 데이터 생성"""
    print(f"\n[8단계] AI 추론 요청 데이터 생성 (목표: {num_requests}건)...")

    from apps.ai_inference.models import AIModel, AIInferenceRequest, AIInferenceResult
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = AIInferenceRequest.objects.count()
    if existing_count >= num_requests and not force:
        print(f"[SKIP] 이미 {existing_count}건의 AI 요청이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    ai_models = list(AIModel.objects.filter(is_active=True))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not ai_models:
        print("[WARNING] 활성화된 AI 모델이 없습니다. 먼저 AI 모델을 생성합니다.")
        create_ai_models()
        ai_models = list(AIModel.objects.filter(is_active=True))

    # AIInferenceRequest.Status에 맞춤
    statuses = ['PENDING', 'VALIDATING', 'PROCESSING', 'COMPLETED', 'FAILED']
    priorities = ['low', 'normal', 'high', 'urgent']

    created_count = 0

    for i in range(num_requests):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        model = random.choice(ai_models)
        status = random.choice(statuses)

        days_ago = random.randint(0, 60)
        requested_at = timezone.now() - timedelta(days=days_ago)

        # 시작/완료 시간 설정
        started_at = None
        completed_at = None
        error_message = None

        if status in ['PROCESSING', 'COMPLETED', 'FAILED']:
            started_at = requested_at + timedelta(minutes=random.randint(1, 30))

        if status == 'COMPLETED':
            completed_at = started_at + timedelta(minutes=random.randint(5, 60)) if started_at else None
        elif status == 'FAILED':
            completed_at = started_at + timedelta(minutes=random.randint(1, 10)) if started_at else None
            error_message = random.choice([
                "입력 데이터 검증 실패",
                "모델 처리 중 오류 발생",
                "타임아웃 초과",
                "필수 데이터 누락"
            ])

        try:
            with transaction.atomic():
                ai_request = AIInferenceRequest.objects.create(
                    patient=patient,
                    model=model,
                    requested_by=doctor,
                    status=status,
                    priority=random.choice(priorities),
                    ocs_references=[],
                    input_data={"patient_id": patient.id, "model_code": model.code},
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message=error_message,
                )

                # COMPLETED인 경우 결과도 생성
                if status == 'COMPLETED':
                    tumor_detected = random.random() < 0.7
                    result_data = {
                        "analysis_type": model.code,
                        "tumor_detected": tumor_detected,
                        "tumor_grade": random.choice(['Grade I', 'Grade II', 'Grade III', 'Grade IV']) if tumor_detected else None,
                        "tumor_location": random.choice(["frontal", "temporal", "parietal", "occipital"]) if tumor_detected else None,
                        "recommendations": [
                            "추가 영상 검사 권장" if tumor_detected else "정기 검진 권장",
                            "전문의 상담 권장"
                        ],
                    }

                    review_status = random.choice(['pending', 'approved', 'rejected'])
                    reviewed_by = doctor if review_status != 'pending' else None
                    reviewed_at = completed_at + timedelta(hours=random.randint(1, 48)) if reviewed_by else None

                    AIInferenceResult.objects.create(
                        inference_request=ai_request,
                        result_data=result_data,
                        confidence_score=round(random.uniform(0.75, 0.98), 2),
                        visualization_paths=[],
                        reviewed_by=reviewed_by,
                        review_status=review_status,
                        review_comment="결과 확인함" if reviewed_by else None,
                        reviewed_at=reviewed_at,
                    )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] AI 요청 생성: {created_count}건")
    print(f"  현재 전체 AI 요청: {AIInferenceRequest.objects.count()}건")
    return True


def create_ai_models():
    """AI 모델 시드 데이터 생성"""
    print(f"\n[9단계] AI 모델 데이터 생성...")

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


def print_summary():
    """더미 데이터 요약"""
    print("\n" + "="*60)
    print("더미 데이터 생성 완료!")
    print("="*60)

    from apps.patients.models import Patient
    from apps.encounters.models import Encounter
    from apps.imaging.models import ImagingStudy
    from apps.ocs.models import OCS
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.accounts.models import Permission
    from apps.ai_inference.models import AIModel, AIInferenceRequest
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp

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


def reset_dummy_data():
    """기존 더미 데이터 삭제"""
    print("\n[RESET] 기존 더미 데이터 삭제 중...")

    from apps.ocs.models import OCS, OCSHistory
    from apps.imaging.models import ImagingStudy
    from apps.encounters.models import Encounter
    from apps.patients.models import Patient
    from apps.menus.models import Menu, MenuLabel, MenuPermission
    from apps.ai_inference.models import AIInferenceRequest, AIInferenceResult, AIInferenceLog
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp

    # 삭제 순서: 의존성 역순
    # AI 로그/결과/요청 삭제
    ai_log_count = AIInferenceLog.objects.count()
    AIInferenceLog.objects.all().delete()
    print(f"  AIInferenceLog: {ai_log_count}건 삭제")

    ai_result_count = AIInferenceResult.objects.count()
    AIInferenceResult.objects.all().delete()
    print(f"  AIInferenceResult: {ai_result_count}건 삭제")

    ai_request_count = AIInferenceRequest.objects.count()
    AIInferenceRequest.objects.all().delete()
    print(f"  AIInferenceRequest: {ai_request_count}건 삭제")

    # 치료 세션/계획 삭제
    treatment_session_count = TreatmentSession.objects.count()
    TreatmentSession.objects.all().delete()
    print(f"  TreatmentSession: {treatment_session_count}건 삭제")

    treatment_plan_count = TreatmentPlan.objects.count()
    TreatmentPlan.objects.all().delete()
    print(f"  TreatmentPlan: {treatment_plan_count}건 삭제")

    # 경과 기록 삭제
    followup_count = FollowUp.objects.count()
    FollowUp.objects.all().delete()
    print(f"  FollowUp: {followup_count}건 삭제")

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

    print("[OK] 더미 데이터 삭제 완료")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='기존 데이터 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 더미 데이터 생성")
    print("="*60)

    # 선행 조건 확인
    if not check_prerequisites():
        sys.exit(1)

    # --reset 옵션: 기존 데이터 삭제
    if args.reset:
        confirm = input("\n정말 기존 데이터를 모두 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_dummy_data()
        else:
            print("삭제 취소됨")
            sys.exit(0)

    force = args.reset or args.force  # reset 시에는 force=True

    # 메뉴/권한 시드 데이터 로드
    load_menu_permission_seed()

    # 환자 데이터 생성
    create_dummy_patients(30, force=force)

    # 진료 데이터 생성
    create_dummy_encounters(20, force=force)

    # 영상 검사 데이터 생성 (OCS 통합)
    create_dummy_imaging_with_ocs(30, force=force)

    # 검사 오더 생성 (LIS)
    create_dummy_lis_orders(20, force=force)

    # 치료 계획 데이터 생성
    create_dummy_treatment_plans(15, force=force)

    # 경과 추적 데이터 생성
    create_dummy_followups(25, force=force)

    # AI 모델 시드 데이터 생성
    create_ai_models()

    # AI 요청 데이터 생성
    create_dummy_ai_requests(10, force=force)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()
