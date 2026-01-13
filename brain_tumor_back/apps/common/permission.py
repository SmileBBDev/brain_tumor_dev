from rest_framework.permissions import BasePermission
from apps.accounts.services.permission_service import get_user_permission

# API 권한 체크용 Permission 클래스
class HasPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if not self.required_permission:
            return True

        user_permission = get_user_permission(request.user)
        return self.required_permission in user_permission


class IsAdmin(BasePermission):
    """ADMIN 또는 SYSTEMMANAGER 역할만 접근 가능"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.role:
            return False
        return request.user.role.code in ['ADMIN', 'SYSTEMMANAGER']


class IsExternal(BasePermission):
    """EXTERNAL 역할(외부기관)만 접근 가능"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.role:
            return False
        return request.user.role.code == 'EXTERNAL'