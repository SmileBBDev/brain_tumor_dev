from .models import Menu, MenuPermission
from apps.accounts.services.permission_service import get_user_permission

# 특정 유저가 접근 가능한 메뉴를 반환하는 함수.
def get_user_menus(user):
    # 유저가 가진 권한 코드 리스트
    # user_permission = get_user_permission(user)

    # MenuPermission 테이블에서 해당 권한 코드에 매핑된 메뉴 id 추출
    # menu_ids = MenuPermission.objects.filter(
    #     permission__code__in = user_permission
    # ).values_list("menu_id", flat = True).distinct()

    role = user.role
    permissions = role.permissions.all()

    # 메뉴 조회 로직 
    # 1. 권한이 있는 메뉴 ID들 (실제 페이지)
    allowed_menu_ids = set(
        MenuPermission.objects
        .filter(permission__in=permissions)
        .values_list("menu_id", flat=True)
    )

    # 2. 부모 메뉴까지 재귀적으로 포함
    def include_parents(menu_id, result):
        try:
            menu = Menu.objects.get(menu_id=menu_id)
            if menu.parent_id:
                result.add(menu.parent_id)
                include_parents(menu.parent_id, result)
        except Menu.DoesNotExist:
            pass

    visible_menu_ids = set(allowed_menu_ids)

    for menu_id in allowed_menu_ids:
        include_parents(menu_id, visible_menu_ids)

    # 3. 메뉴 조회
    menus =(
        Menu.objects.filter(
            # menu_id__in = menu_ids,
            # menupermission__permission__in=permissions,
            is_active = True,
            menu_id__in=visible_menu_ids
        )
        .select_related("parent")
        .prefetch_related("children", "labels")
        .order_by("order")
        # .distinct()
    ) 
    # ).order_by("order").prefetch_related("labels", "roles", "children")
    
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