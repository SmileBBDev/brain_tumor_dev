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

## 완료된 작업 (2026-01-13)

### ✅ 상세 페이지 라우팅 수정 - 완료
- **문제점**: `breadcrumb_only=True`인 메뉴(상세 페이지)가 API 응답에서 제외되어 라우팅 실패
- **수정 파일**: `apps/menus/services.py`
- **해결**: `breadcrumb_only` 필터 제거 → 모든 메뉴 반환, 사이드바 표시는 프론트엔드에서 처리
- **영향받는 페이지**:
  - `/patients/:patientId` (PATIENT_DETAIL)
  - `/admin/users/:id` (ADMIN_USER_DETAIL)
  - `/ocs/create` (OCS_CREATE)
  - `/ocs/ris/:ocsId` (OCS_RIS_DETAIL)
  - `/ocs/lis/:ocsId` (OCS_LIS_DETAIL)
  - `/ai/requests/create` (AI_REQUEST_CREATE)
  - `/ai/requests/:id` (AI_REQUEST_DETAIL)

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

---

## 📋 현재 작업 지시서 (2026-01-13)

### 작업 1: OCS 페이지 통합 - 메뉴 설정 (B와 협업)

**목표**: `/ocs/manage` → `/ocs/status`로 통합

**작업 내용**:
1. 메뉴 DB에서 `OCS_MANAGE` 항목 제거 또는 비활성화
2. `OCS_STATUS` 메뉴 권한에 DOCTOR, SYSTEMMANAGER 추가 (OCS 생성 버튼용)

**수정 파일**: `setup_dummy_data/` 메뉴 설정 또는 DB 직접 수정

---

### 작업 2: `/ocs/process-status` API 생성

**참고**: `/ocs/ris/process-status` 구조 참고

**작업 내용**:
1. `apps/ocs/views.py`에 OCSProcessStatusView 추가
2. RIS + LIS 통합 처리 현황 API
3. URL 등록: `/api/ocs/process-status/`

**응답 형식**:
```python
{
    'ris': {
        'pending': ...,
        'in_progress': ...,
        'completed': ...,
        'total_today': ...
    },
    'lis': {
        'pending': ...,
        'in_progress': ...,
        'completed': ...,
        'total_today': ...
    },
    'combined': {
        'total_pending': ...,
        'total_completed': ...
    }
}
```

---

### 작업 3: 의사 Dashboard API - 금일 예약환자 (B와 협업)

**목표**: 의사 대시보드에서 금일 예약환자 5명 표시

**작업 내용**:
1. `apps/common/views.py`에 DoctorDashboardStatsView 추가
2. 금일 예약환자 API (현 시간 기준 가까운 5명)

**URL**: `/api/dashboard/doctor/stats/`

**응답 형식**:
```python
{
    'today_appointments': [
        {
            'patient_id': ...,
            'patient_name': ...,
            'appointment_time': ...,
            'reason': ...
        },
        # 최대 5명
    ],
    'total_today': ...,
    'remaining': ...
}
```

---

### 작업 4: AI 페이지 관련 API 확인

**B가 필요로 하는 API**:
1. `GET /api/ai/requests/` - AI 요청 목록 (✅ 이미 존재)
2. `GET /api/ai/process-status/` - AI 처리 현황 (신규 필요 시)
3. `GET /api/ai/models/` - AI 모델 정보 (신규 필요 시)

**AI 모델 정보 API** (필요 시):
```python
# URL: /api/ai/models/
{
    'models': [
        {
            'code': 'M1',
            'name': 'MRI 4-Channel Analysis',
            'description': 'MRI 영상 기반 뇌종양 분석',
            'input_type': 'T1, T2, T1C, FLAIR',
            'accuracy': 0.95
        },
        # MG, MM...
    ]
}
```

---

## 완료된 작업 기록

### ✅ 작업 8: IsExternal 권한 클래스 수정 - 완료 (2026-01-13)

| 역할 | 설명 | 내부/외부 |
|------|------|-----------|
| DOCTOR | 의사 | 내부 |
| NURSE | 간호사 | 내부 |
| LIS | 검사실 담당자 | **내부** |
| RIS | 영상실 담당자 | **내부** |
| ADMIN | 관리자 | 내부 |
| SYSTEMMANAGER | 시스템 관리자 | 내부 |
| EXTERNAL | 외부기관 | **외부** |

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
- [x] **✅ IsExternal 수정: EXTERNAL 역할만 허용 (RIS, LIS 제외)** - 완료됨
