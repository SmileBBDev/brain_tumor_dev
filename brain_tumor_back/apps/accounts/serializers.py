from rest_framework import serializers;
from .models import User

# Serialzer는 데이터 변환
class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    
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
        ]
    def get_role(self, obj):
        if not obj.role:
            return None
        return {
            "code": obj.role.code,
            "name": obj.role.name,
    }