#!/usr/bin/env python
"""
OCS 메뉴 및 권한 추가 스크립트
- OCS_ORDER: 의사용 검사 오더
- OCS_RIS: RIS 작업자용 영상 워크리스트
- OCS_LIS: LIS 작업자용 검사 워크리스트
"""
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.menus.models import Menu, MenuPermission, MenuLabel
from apps.accounts.models import Permission, Role


def add_ocs_menus():
    """OCS 메뉴 추가"""
    print("="*60)
    print("OCS 메뉴 추가 스크립트")
    print("="*60)

    # ORDER 그룹 메뉴 찾기 (parent)
    try:
        order_menu = Menu.objects.get(code='ORDER')
        print(f"[OK] ORDER 메뉴 찾음 (id={order_menu.id})")
    except Menu.DoesNotExist:
        print("[ERROR] ORDER 메뉴가 없습니다. seed 데이터를 먼저 로드하세요.")
        return

    # OCS 메뉴 정의
    ocs_menus = [
        {
            'code': 'OCS_ORDER',
            'path': '/ocs/order',
            'icon': 'file-medical',
            'order': 3,
            'label': '검사 오더',
            'permission_name': '검사 오더',
            'permission_desc': '의사용 검사 오더 생성/관리',
            'roles': ['SYSTEMMANAGER', 'ADMIN', 'DOCTOR'],
        },
        {
            'code': 'OCS_RIS',
            'path': '/ocs/ris',
            'icon': 'x-ray',
            'order': 4,
            'label': '영상 워크리스트',
            'permission_name': '영상 워크리스트',
            'permission_desc': 'RIS 작업자용 영상 오더 처리',
            'roles': ['SYSTEMMANAGER', 'ADMIN', 'RIS'],
        },
        {
            'code': 'OCS_LIS',
            'path': '/ocs/lis',
            'icon': 'flask',
            'order': 5,
            'label': '검사 워크리스트',
            'permission_name': '검사 워크리스트',
            'permission_desc': 'LIS 작업자용 검사 오더 처리',
            'roles': ['SYSTEMMANAGER', 'ADMIN', 'LIS'],
        },
    ]

    for menu_data in ocs_menus:
        code = menu_data['code']

        # 1. 메뉴 생성/업데이트
        menu, created = Menu.objects.update_or_create(
            code=code,
            defaults={
                'path': menu_data['path'],
                'icon': menu_data['icon'],
                'order': menu_data['order'],
                'is_active': True,
                'breadcrumb_only': False,
                'parent': order_menu,
            }
        )
        print(f"[{'CREATE' if created else 'UPDATE'}] Menu: {code}")

        # 2. 권한 생성/업데이트
        permission, created = Permission.objects.update_or_create(
            code=code,
            defaults={
                'name': menu_data['permission_name'],
                'description': menu_data['permission_desc'],
            }
        )
        print(f"[{'CREATE' if created else 'UPDATE'}] Permission: {code}")

        # 3. 메뉴-권한 연결
        MenuPermission.objects.get_or_create(menu=menu, permission=permission)
        print(f"[OK] MenuPermission: {code}")

        # 4. 역할-권한 연결
        for role_code in menu_data['roles']:
            try:
                role = Role.objects.get(code=role_code)
                role.permissions.add(permission)
                print(f"  - Role '{role_code}' <- Permission '{code}'")
            except Role.DoesNotExist:
                print(f"  - [SKIP] Role '{role_code}' 없음")

        # 5. 메뉴 라벨 추가
        MenuLabel.objects.get_or_create(
            menu=menu,
            role='DEFAULT',
            defaults={'text': menu_data['label']}
        )
        print(f"[OK] MenuLabel: {code}")
        print()

    print("="*60)
    print("[완료] OCS 메뉴 추가 완료")
    print("="*60)

    # 결과 확인
    print("\n[메뉴 목록]")
    for menu in Menu.objects.filter(code__startswith='OCS_'):
        print(f"  - {menu.code}: {menu.path}")

    print("\n[권한 목록]")
    for perm in Permission.objects.filter(code__startswith='OCS_'):
        print(f"  - {perm.code}: {perm.name}")


if __name__ == '__main__':
    add_ocs_menus()
