from django.contrib.auth import authenticate
from rest_framework import serializers
from apps.accounts.models import User
from apps.accounts.models.role import Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "description", "created_at"]

# 로그인 관련 데이터를 JSON 타입의 데이터로 변환
class LoginSerializer(serializers.Serializer):
    login_id = serializers.CharField()
    password = serializers.CharField(write_only = True)
    
    def validate(self, data):
        login_id = data.get("login_id")
        password = data.get("password")

        user = authenticate(login_id = login_id, password = password)
        
        if not user :
            raise serializers.ValidationError("아이디 또는 비밀번호가 올바르지 않습니다.")
        
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")
        
        data["user"] = user
        return data

# 현재 사용자 정보(내 정보 조회) 데이터
class MeSerializer(serializers.ModelSerializer) :
    role = RoleSerializer(read_only=True)  # Role 전체 객체 직렬화

    class Meta :
        model = User
        fields = (
            "id",
            "login_id",
            "name",
            "email",
            "is_active",
            "is_staff",
            "role",
        )

# 로그인 성공 시 last_login 갱신을 위한 커스텀 시리얼라이저
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # 로그인 성공 → last_login 갱신
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])

        return data