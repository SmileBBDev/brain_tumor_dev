# 비즈니스 로직 (권한 변경 처리)
# apps/accounts/views.py → 요청을 받아서 서비스 함수를 호출
# apps/accounts/views.py
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend


# 1. 사용자 목록 조회 & 추가
class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
    ]

    # /api/users/?search=doctor01 → ID 검색
    # /api/users/?search=홍길동 → 이름 검색
    # /api/users/?role=DOCTOR → 역할 필터링
    # /api/users/?is_active=true → 활성 사용자만 조회
    search_fields = ["login_id", "name"] # 검색 필드 설정
    filterset_fields = ["role", "is_active"] # 필터링 필드 설정

# 2. 사용자 상세 조회 & 수정 & 삭제
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# 3. 사용자 활성/비활성 토글
class UserToggleActiveView(APIView):
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = not user.is_active
        user.save()
        return Response({"id": user.id, "is_active": user.is_active})