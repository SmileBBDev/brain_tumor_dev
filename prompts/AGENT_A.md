# A 에이전트 (Backend)

## 담당 영역
- `brain_tumor_back/` (Django)
- 모델, 뷰, 시리얼라이저, URL
- 더미 데이터 스크립트

## 규칙
- API 목록은 페이지네이션: `{ count, results: [...] }`
- ViewSet @action 사용
- 시리얼라이저 필드 명시

## 참고 문서
- `SHARED.md`: 공용 정보 (비밀번호, 역할, 경로)
- `PROJECT_DOCS.md`: 프로젝트 아키텍처
- `AI_MODELS.md`: AI 모델 정의 (M1, MG, MM)
- `TODO_BACKLOG.md`: 전체 백로그

## 주의사항
- `apps/ai_inference/`는 **다른 작업자가 작업 중** - 건드리지 말 것

---

## 현재 작업 (2026-01-12)

### 작업 1: Admin Dashboard API

**생성/수정 파일**: `apps/common/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta

from apps.accounts.models import User
from apps.patients.models import Patient
from apps.ocs.models import OCS


class AdminDashboardStatsView(APIView):
    """관리자 대시보드 통계 API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        # 사용자 통계
        users = User.objects.filter(is_active=True)
        user_by_role = dict(
            users.values('role__code')
            .annotate(count=Count('id'))
            .values_list('role__code', 'count')
        )

        # 환자 통계
        patients = Patient.objects.filter(is_deleted=False)

        # OCS 통계
        ocs_all = OCS.objects.filter(is_deleted=False)
        ocs_by_status = dict(
            ocs_all.values('ocs_status')
            .annotate(count=Count('id'))
            .values_list('ocs_status', 'count')
        )

        return Response({
            'users': {
                'total': users.count(),
                'by_role': user_by_role,
                'recent_logins': users.filter(last_login__gte=week_ago).count(),
            },
            'patients': {
                'total': patients.count(),
                'new_this_month': patients.filter(created_at__gte=month_start).count(),
            },
            'ocs': {
                'total': ocs_all.count(),
                'by_status': ocs_by_status,
                'pending_count': ocs_all.filter(
                    ocs_status__in=['ORDERED', 'ACCEPTED', 'IN_PROGRESS']
                ).count(),
            },
        })
```

---

### 작업 2: External Dashboard API

**생성/수정 파일**: `apps/common/views.py`에 추가

```python
class ExternalDashboardStatsView(APIView):
    """외부기관 대시보드 통계 API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # 외부 LIS 업로드 (extr_ prefix)
        lis_external = OCS.objects.filter(
            ocs_id__startswith='extr_',
            job_role='LIS',
            is_deleted=False
        )

        # 외부 RIS 업로드 (risx_ prefix)
        ris_external = OCS.objects.filter(
            ocs_id__startswith='risx_',
            job_role='RIS',
            is_deleted=False
        )

        # 최근 업로드
        from django.db.models import Q
        recent = OCS.objects.filter(
            Q(ocs_id__startswith='extr_') | Q(ocs_id__startswith='risx_'),
            is_deleted=False
        ).select_related('patient').order_by('-created_at')[:10]

        return Response({
            'lis_uploads': {
                'pending': lis_external.filter(ocs_status='RESULT_READY').count(),
                'completed': lis_external.filter(ocs_status='CONFIRMED').count(),
                'total_this_week': lis_external.filter(created_at__gte=week_ago).count(),
            },
            'ris_uploads': {
                'pending': ris_external.filter(ocs_status='RESULT_READY').count(),
                'completed': ris_external.filter(ocs_status='CONFIRMED').count(),
                'total_this_week': ris_external.filter(created_at__gte=week_ago).count(),
            },
            'recent_uploads': [
                {
                    'id': o.id,
                    'ocs_id': o.ocs_id,
                    'job_role': o.job_role,
                    'status': o.ocs_status,
                    'uploaded_at': o.created_at.isoformat(),
                    'patient_name': o.patient.name if o.patient else '-',
                }
                for o in recent
            ],
        })
```

---

### 작업 3: URL 등록

**수정 파일**: `config/urls.py` 또는 `apps/common/urls.py`

```python
from apps.common.views import AdminDashboardStatsView, ExternalDashboardStatsView

urlpatterns += [
    path('api/dashboard/admin/stats/', AdminDashboardStatsView.as_view()),
    path('api/dashboard/external/stats/', ExternalDashboardStatsView.as_view()),
]
```

---

## AI 자동 추론 관련 (보류)

> **참고**: AI 자동 추론 시스템은 `apps/ai_inference/` 작업 완료 후 진행
> - `submit_result()` 트리거 연동 필요
> - AI_MODELS.md 참조

---

## 완료 기준

- [ ] `apps/common/views.py`에 Dashboard API 추가
- [ ] URL 등록
- [ ] 테스트: `GET /api/dashboard/admin/stats/` 응답 확인
- [ ] 테스트: `GET /api/dashboard/external/stats/` 응답 확인
