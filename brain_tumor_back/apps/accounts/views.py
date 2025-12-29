# 비즈니스 로직 (권한 변경 처리)
# apps/accounts/views.py → 요청을 받아서 서비스 함수를 호출
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.permissions import update_user_permissions
from .models import Permission

class UserPermissionUpdateView(APIView):
    def post(self, request, user_id):
        user = User.objects.get(id=user_id)
        permissions = Permission.objects.filter(code__in=request.data.get("permissions", []))
        update_user_permissions(user, permissions)
        return Response({"status": "ok"})