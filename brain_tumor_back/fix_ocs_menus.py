#!/usr/bin/env python
"""
OCS 메뉴 위치 수정 스크립트
- OCS_RIS: ORDER → IMAGING 그룹으로 이동
- OCS_LIS: ORDER 그룹 유지
- OCS_ORDER: ORDER 그룹 유지
"""
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.menus.models import Menu


def fix_ocs_menus():
    """OCS 메뉴 위치 수정"""
    print("="*60)
    print("OCS 메뉴 위치 수정 스크립트")
    print("="*60)

    # IMAGING 그룹 메뉴 찾기
    try:
        imaging_menu = Menu.objects.get(code='IMAGING')
        print(f"[OK] IMAGING 메뉴 찾음 (id={imaging_menu.id})")
    except Menu.DoesNotExist:
        print("[ERROR] IMAGING 메뉴가 없습니다.")
        return

    # OCS_RIS를 IMAGING 그룹으로 이동
    try:
        ocs_ris = Menu.objects.get(code='OCS_RIS')
        old_parent = ocs_ris.parent
        ocs_ris.parent = imaging_menu
        ocs_ris.order = 3  # IMAGING 하위에서 순서
        ocs_ris.save()
        print(f"[OK] OCS_RIS 이동: {old_parent.code if old_parent else 'None'} → IMAGING")
    except Menu.DoesNotExist:
        print("[ERROR] OCS_RIS 메뉴가 없습니다.")
        return

    # 결과 확인
    print("\n[IMAGING 하위 메뉴]")
    for menu in Menu.objects.filter(parent=imaging_menu).order_by('order'):
        print(f"  - {menu.code}: {menu.path} (order={menu.order})")

    print("\n[ORDER 하위 메뉴]")
    order_menu = Menu.objects.get(code='ORDER')
    for menu in Menu.objects.filter(parent=order_menu).order_by('order'):
        print(f"  - {menu.code}: {menu.path} (order={menu.order})")

    print("\n" + "="*60)
    print("[완료] OCS_RIS를 IMAGING 그룹으로 이동 완료")
    print("="*60)


if __name__ == '__main__':
    fix_ocs_menus()
