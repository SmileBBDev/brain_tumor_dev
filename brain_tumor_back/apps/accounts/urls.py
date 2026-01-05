from django.urls import path
from .views import UnlockUserView, UserListView, UserDetailView, UserToggleActiveView

# 사용자 관리 API 엔드포인트 정의
urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),  # 사용자 목록 조회 및 생성(GET)
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),  # 특정 사용자 상세 조회, 수정, 삭제(GET, PUT, DELETE)
    path("<int:pk>/toggle-active/", UserToggleActiveView.as_view(), name="user_toggle_active"),
    path("<int:pk>/unlock/", UnlockUserView.as_view()),
]
