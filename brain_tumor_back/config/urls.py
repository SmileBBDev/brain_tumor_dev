from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView
from apps.authorization.views import CustomTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.authorization.urls")), 
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # Refresh 토큰 재발급 API

    # 사용자 관리 API
    path("api/users/", include("apps.accounts.urls")),
]
