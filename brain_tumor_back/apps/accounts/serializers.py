from rest_framework import serializers
from apps.authorization.serializers import RoleSerializer;
from .models import User

# Serialzer는 데이터 변환
# 사용자 모델을 JSON 타입의 데이터로 변환
class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id"
            , "login_id"
            , "name"
            , "email"
            , "role"
            , "is_active"
            , "is_staff"
            , "is_superuser"
            , "last_login"
            , "created_at"
            , "updated_at"
            , "is_locked"
            , "failed_login_count"
            , "last_login_ip"
            , "is_online"
        ]
    def get_role(self, obj):
        if not obj.role:
            return None
        return {
            "code": obj.role.code,
            "name": obj.role.name,
    }

# 사용자 생성/수정 시리얼라이저
class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)       
   
    class Meta:
        model = User
        fields = [
            "login_id"
            , "password"
            , "name"
            , "email"
            , "role"
            , "is_active"
            , "is_staff"
            , "is_superuser"
            , "is_locked"
        ]
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user