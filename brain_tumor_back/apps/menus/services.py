from .models import Menu, MenuPermission
from apps.accounts.services.permission_service import get_user_permission

# 특정 유저가 접근 가능한 메뉴를 반환하는 함수.
def get_user_menus(user):
    role = user.role
    permissions = role.permissions.all()

    # 메뉴 조회 로직 
    # 1. 권한이 있는 메뉴 ID들 (실제 페이지)
    allowed_menu_codes = set(
        MenuPermission.objects
        .filter(permission__in=permissions)
        .values_list("menu__code", flat=True)
    )

    # 2. 부모 메뉴까지 재귀적으로 포함
    def include_parent_codes(menu_code, result):
        try:
            menu = Menu.objects.get(code=menu_code)
            if menu.parent:
                result.add(menu.parent.code)
                include_parent_codes(menu.parent.code, result)
        except Menu.DoesNotExist:
            pass

    visible_menu_codes = set(allowed_menu_codes)

    for code in allowed_menu_codes:
        include_parent_codes(code, visible_menu_codes)


    # 3. 메뉴 조회
    menus = (
        Menu.objects.filter(
            is_active=True,
            code__in=visible_menu_codes
        )
        .select_related("parent")
        .prefetch_related("children", "labels")
        .order_by("order")
    )
    return menus

# 주어진 권한 코드로 접근 가능한 메뉴를 반환하는 함수.
def get_accessible_menus(permission_codes: list[str]):
    """
    permission_codes:
      ['VIEW_DASHBOARD', 'VIEW_PATIENT_LIST', ...]
    """

    menus = (
        Menu.objects
        .filter(
            is_active=True,
            menupermission__permission__code__in=permission_codes
        )
        .distinct()
        .select_related("parent")
        .prefetch_related("children")
        .order_by("order")
    )

    return menus