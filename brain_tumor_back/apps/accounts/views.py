# 비즈니스 로직 (권한 변경 처리)
# apps/accounts/views.py → 요청을 받아서 서비스 함수를 호출
# apps/accounts/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer, UserCreateUpdateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.db.models import BooleanField, Case, When, Value


# 1. 사용자 목록 조회 & 추가 API(관리자 전용 view)
# 검색, 필터, 생성, 온라인 상태
class UserListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
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
    
    def get_queryset(self):
        qs = User.objects.select_related("role")

        online_threshold = timezone.now() - timedelta(seconds=60)

        qs = qs.annotate(
            is_online=Case(
                When(last_seen__gte=online_threshold, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return qs
    
    # 사용자 생성
    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateUpdateSerializer
        return UserSerializer

# 2. 사용자 상세 조회(GET) & 수정(PUT) & 삭제(DELETE) API
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

# 4. 사용자 계정 잠금 해제
class UnlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        user.is_locked = False
        user.failed_login_count = 0
        user.locked_at = None
        user.save()

        return Response({"detail": "계정 잠금 해제 완료"})

