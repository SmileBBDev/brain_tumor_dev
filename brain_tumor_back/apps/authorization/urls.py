from django.urls import path
from .views import LoginView, MeView
from apps.menus.views import UserMenuView   # ✅ menus 앱에서 가져오기

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"), # 로그인
    path("me/", MeView.as_view(), name="me"), # 로그인 사용자 정보 조회 
    path("menu/", UserMenuView.as_view(), name="user-menu"),  # 사용자 메뉴 조회

    
]
