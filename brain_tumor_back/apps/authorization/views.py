from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from django.utils import timezone
from apps.accounts.models.user import User
from apps.common.utils import get_client_ip
from apps.audit.services import create_audit_log # # Audit Log 기록 유틸
from apps.accounts.services.permission_service import get_user_permission # 사용자 권한 조회 로직

from .serializers import LoginSerializer, MeSerializer, CustomTokenObtainPairSerializer

# JWT 토큰 발급 View
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(
            data = request.data,
            context = {"request": request},
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            
            # 로그인 성공 처리
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            # 로그인 성공 시 실패 횟수 & 잠금 해제
            user.failed_login_count = 0
            user.is_locked = False
            user.locked_at = None
            
            # 변경된 필드만 업데이트
            user.save(update_fields=[
                "last_login",
                "last_login_ip",
                "failed_login_count",
                "is_locked",
                "locked_at",
            ])

            refresh = RefreshToken.for_user(user)

            create_audit_log(request, "LOGIN_SUCCESS", user) 

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        # 로그인 잠금으로 인한 실패 처리
        login_locked = serializer.validated_data.get(
            "login_locked",
            False
        )

        # 잠금이 아닌 경우만 LOGIN_FAIL 기록
        if not login_locked:
            create_audit_log(request, "LOGIN_FAIL")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 내 정보 조회 view
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(
            MeSerializer(request.user).data
        )
 
 
# 로그인 성공시 last_login 갱신 커스텀 토큰 뷰
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            user = User.objects.get(login_id=request.data["login_id"])
            user.last_seen = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=["last_seen", "last_login_ip"])

        return response