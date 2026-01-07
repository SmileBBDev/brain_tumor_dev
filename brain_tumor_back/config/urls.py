from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView
from apps.authorization.views import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.authorization.urls")), 
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # Refresh 토큰 재발급 API

    # 사용자 관리 API
    path("api/users/", include("apps.accounts.urls")),

    # 환자 관리 API
    path("api/patients/", include("apps.patients.urls")),

    # 진료 관리 API
    path("api/encounters/", include("apps.encounters.urls")),

    # API 문서화 엔드포인트
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # path("api/emr/", include("apps.emr.urls")),
    # path("api/ris/", include("apps.ris.urls")),
    # path("api/ocs/", include("apps.ocs.urls")),
    # path("api/lis/", include("apps.lis.urls")),
    # path("api/fhir/", include("apps.fhir.urls")),
]
