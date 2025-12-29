from .models import Menu, MenuPermission
from apps.accounts.services.permission_service import get_user_permission

def get_user_menus(user):
    user_permission = get_user_permission(user)
    
    menu_ids = MenuPermission.objects.filter(
        permission__code__in = user_permission
    ).values_list("menu_id", flat = True).distinct()
    
    menus = Menu.objects.filter(
        id__in = menu_ids,
        is_active = True,
    ).order_by("order").prefetch_related("labels", "roles", "children")
    
    return menus