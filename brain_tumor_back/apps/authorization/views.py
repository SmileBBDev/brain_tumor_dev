from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.services import create_audit_log # # Audit Log 기록 유틸
from apps.accounts.services.permission_service import get_user_permission # 사용자 권한 조회 로직

from .serializers import LoginSerializer, MeSerializer, CustomTokenObtainPairSerializer

# JWT 토큰 발급 View
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            create_audit_log(request, "LOGIN_SUCCESS", user)  # 오탈자 수정

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        else:
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