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

## 완료된 작업 (2026-01-12)

### ✅ 작업 1: Admin Dashboard API - 완료
- **파일**: `apps/common/views.py` - AdminDashboardStatsView
- **URL**: `/api/dashboard/admin/stats/`
- **상태**: 구현 완료, 프론트엔드 타입과 100% 일치

### ✅ 작업 2: External Dashboard API - 완료
- **파일**: `apps/common/views.py` - ExternalDashboardStatsView
- **URL**: `/api/dashboard/external/stats/`
- **상태**: 구현 완료, 프론트엔드 타입과 100% 일치

### ✅ 작업 3: URL 등록 - 완료
- **파일**: `config/urls.py`
- **상태**: 등록 완료

### ✅ 작업 4~7: 권한, 에러처리, enum, 문서화 - 완료

---

## 긴급 수정 필요

### 🚨 작업 8: IsExternal 권한 클래스 수정 (긴급)

**문제점**: IsExternal이 RIS, LIS를 허용하고 있음 - **잘못됨**

| 역할 | 설명 | 내부/외부 |
|------|------|-----------|
| DOCTOR | 의사 | 내부 |
| NURSE | 간호사 | 내부 |
| LIS | 검사실 담당자 | **내부** |
| RIS | 영상실 담당자 | **내부** |
| ADMIN | 관리자 | 내부 |
| SYSTEMMANAGER | 시스템 관리자 | 내부 |
| EXTERNAL | 외부기관 | **외부** |

**수정 파일**: `apps/common/permission.py`

```python
# 현재 (잘못됨)
class IsExternal(BasePermission):
    def has_permission(self, request, view):
        return request.user.role.code in ['RIS', 'LIS']  # ❌ RIS, LIS는 내부 직원

# 수정 필요
class IsExternal(BasePermission):
    """EXTERNAL 역할(외부기관)만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == 'EXTERNAL'  # ✅
```

**테스트**:
- `external1` 계정으로 `/api/dashboard/external/stats/` 접근 → 200 OK
- `ris1`, `lis1` 계정으로 접근 → 403 Forbidden

---

## 개선 필요 작업 (우선순위순)

### ~~작업 4~7~~ - 완료됨

### 작업 9: 에러 처리 및 로깅 추가 (중간)

**문제점**: try-except 블록이 없음

**수정 파일**: `apps/common/views.py`

```python
import logging

logger = logging.getLogger(__name__)

class AdminDashboardStatsView(APIView):
    def get(self, request):
        try:
            # 기존 코드...
            return Response({...})
        except Exception as e:
            logger.error(f"Admin dashboard stats error: {str(e)}")
            return Response(
                {'error': '통계를 불러오는 중 오류가 발생했습니다.'},
                status=500
            )
```

---

### 작업 6: OCS 상태 enum 사용 (낮음)

**문제점**: 문자열 하드코딩

**수정 위치**: `apps/common/views.py` 라인 84-86

```python
# 변경 전
'pending_count': ocs_all.filter(
    ocs_status__in=['ORDERED', 'ACCEPTED', 'IN_PROGRESS']
).count(),

# 변경 후
from apps.ocs.models import OCS

'pending_count': ocs_all.filter(
    ocs_status__in=[
        OCS.OcsStatus.ORDERED,
        OCS.OcsStatus.ACCEPTED,
        OCS.OcsStatus.IN_PROGRESS
    ]
).count(),
```

---

### 작업 7: API 문서화 (낮음)

**문제점**: @extend_schema 데코레이터 없음

```python
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=["Dashboard"],
    description="관리자용 대시보드 통계를 조회합니다",
    responses={200: ...}
)
class AdminDashboardStatsView(APIView):
    # ...
```

---

## AI 자동 추론 관련 (보류)

> **참고**: AI 자동 추론 시스템은 `apps/ai_inference/` 작업 완료 후 진행
> - `submit_result()` 트리거 연동 필요
> - AI_MODELS.md 참조

---

## 완료 기준

- [x] `apps/common/views.py`에 Dashboard API 추가
- [x] URL 등록
- [x] 테스트: `GET /api/dashboard/admin/stats/` 응답 확인
- [x] 테스트: `GET /api/dashboard/external/stats/` 응답 확인
- [x] 역할 기반 권한 검증 추가
- [x] 에러 처리 추가
- [x] OCS 상태 enum 사용
- [ ] **🚨 IsExternal 수정: EXTERNAL 역할만 허용 (RIS, LIS 제외)**
