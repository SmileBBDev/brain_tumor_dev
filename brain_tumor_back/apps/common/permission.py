from rest_framework.permissions import BasePermission
from apps.accounts.services.services import get_user_permission

# API 권한 체크용 Permission 클래스
class HasPermission(BasePermission):
    required_permission = None
    
    def has_permission(self, request, view):
        if not self.required_permission:
            return True

        user_permission = get_user_permission(request.user)
        return self.required_permission in user_permission