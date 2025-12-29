from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from apps.audit.services import create_audit_log # # Audit Log 기록 유틸
from apps.accounts.services.permission_service import get_user_permission # 사용자 권한 조회 로직

from .serializers import LoginSerializer, MeSerializer

# JWT 토큰 발급 View
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        try : 
            serializer.is_valid(raise_exception = True)
        
            user = serializer.validated_data["user"]
            
            refresh = RefreshToken.for_user(user)
            
            create_audit_log(request, "LOGIN_SUCESS", user) # 로그인 성공 로그 남기기
            
            return Response(
                {
                    "access" : str(refresh.access_token),
                    "refresh" : str(refresh),
                },
                status = status.HTTP_200_OK,
            )
        except Exception :
            create_audit_log(request, "LOGIN_FAIL") # 로그인 실패 로그 남기기
            raise
        

# 내 정보 조회 view
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        permissions = get_user_permission(request.user)
        return Response(
            {
                "id": request.user.id
                ,"login_id" : request.user.login_id
                ,"name": request.user.name
                ,"email": request.user.email
                ,"is_active": request.user.is_active
                ,"is_staff": request.user.is_staff
                ,"permission" : permissions
            }
        )
        