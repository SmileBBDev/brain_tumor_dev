from django.contrib.auth import authenticate
from rest_framework import serializers
from apps.accounts.models import User

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
            raise serializers.ValidatonError("비활성화된 계정입니다.")
        
        data["user"] = user
        return data

# 현재 사용자 정보(내 정보 조회) 데이터
class MeSerializer(serializers.ModelSerializer) :
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