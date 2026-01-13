from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorScheduleViewSet

app_name = 'schedules'

router = DefaultRouter()
router.register(r'', DoctorScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]

# =============================================================================
# 생성된 URL 패턴:
# =============================================================================
# GET    /api/schedules/                - 일정 목록 조회
# POST   /api/schedules/                - 일정 생성
# GET    /api/schedules/{id}/           - 일정 상세 조회
# PATCH  /api/schedules/{id}/           - 일정 수정
# DELETE /api/schedules/{id}/           - 일정 삭제 (Soft Delete)
#
# GET    /api/schedules/calendar/?year=&month=  - 캘린더용 월별 일정
# GET    /api/schedules/today/                   - 오늘 일정
# GET    /api/schedules/this-week/               - 이번 주 일정
# =============================================================================
