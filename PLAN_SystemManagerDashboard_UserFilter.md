# SystemManagerDashboard 사용자별 필터 기능 계획서

## 1. 개요

### 1.1 목적
SystemManagerDashboard의 각 권한별 탭에 **사용자 ID 선택 드롭다운**을 추가하여,
관리자가 특정 사용자 관점에서 대시보드를 모니터링할 수 있도록 한다.

### 1.2 현재 구조
```
SystemManagerDashboard
├── OVERVIEW (시스템 전체 현황)
├── DOCTOR (의사 대시보드 - 집계)
├── NURSE (간호사 대시보드 - 집계)
├── LIS (검사실 대시보드 - 집계)
├── RIS (영상실 대시보드 - 집계)
├── PATIENT (환자 대시보드 - 집계)
└── EXTERNAL (외부기관 대시보드 - 집계)
```

### 1.3 변경 후 구조
```
SystemManagerDashboard
├── OVERVIEW (시스템 전체 현황) - 변경 없음
├── DOCTOR 탭
│   ├── [드롭다운: 전체 현황 / 김철수 / 이영희 / ...]
│   └── 선택에 따른 대시보드 렌더링
├── NURSE 탭
│   ├── [드롭다운: 전체 현황 / 홍수진 / 김미영 / ...]
│   └── ...
├── LIS 탭
│   ├── [드롭다운: 전체 현황 / 윤서연 / 정다은 / ...]
│   └── ...
├── RIS 탭
│   ├── [드롭다운: 전체 현황 / 강민호 / 이준혁 / ...]
│   └── ...
├── EXTERNAL 탭
│   ├── [드롭다운: 전체 현황 / 서울대병원 / 아산병원 / ...]
│   └── ...
└── PATIENT 탭
    ├── [드롭다운: 전체 현황 / 환자1 / 환자2 / ...]
    └── ...
```

---

## 2. 구현 범위

### 2.1 백엔드 수정

#### 2.1.1 역할별 사용자 목록 API 추가
- **파일**: `apps/accounts/views.py`
- **엔드포인트**: `GET /api/users/by-role/{role_code}/`
- **응답**: 해당 역할의 활성 사용자 목록

```python
# 기존 ExternalInstitutionListView를 일반화
class UsersByRoleListView(APIView):
    """역할별 사용자 목록 조회"""
    permission_classes = [IsAuthenticated]

    def get(self, request, role_code):
        users = User.objects.filter(
            role__code=role_code.upper(),
            is_active=True
        ).select_related('role').order_by('name')

        return Response([
            {'id': u.id, 'name': u.name, 'code': u.login_id}
            for u in users
        ])
```

#### 2.1.2 대시보드 통계 API에 user_id 필터 추가

| API | 수정 내용 |
|-----|----------|
| `GET /api/dashboard/doctor-stats/` | `?doctor_id=N` 파라미터 추가 |
| `GET /api/dashboard/nurse-stats/` | `?nurse_id=N` 파라미터 추가 (신규) |
| `GET /api/dashboard/lis-stats/` | `?user_id=N` 파라미터 추가 (신규) |
| `GET /api/dashboard/ris-stats/` | `?user_id=N` 파라미터 추가 (신규) |
| `GET /api/dashboard/external-stats/` | `?institution_id=N` 파라미터 추가 |
| `GET /api/dashboard/patient-stats/` | `?patient_id=N` 파라미터 추가 (신규) |

### 2.2 프론트엔드 수정

#### 2.2.1 역할별 사용자 목록 API 함수 추가
- **파일**: `src/services/users.api.ts`

```typescript
// 역할별 사용자 목록 조회
export const fetchUsersByRole = async (roleCode: string): Promise<UserOption[]> => {
  const res = await api.get<UserOption[]>(`/users/by-role/${roleCode}/`);
  return res.data;
};
```

#### 2.2.2 SystemManagerDashboard 수정
- **파일**: `src/pages/dashboard/systemManager/SystemManagerDashboard.tsx`

**변경 사항**:
1. 각 탭별 사용자 목록 state 추가
2. 선택된 사용자 ID state 추가
3. 드롭다운 UI 컴포넌트 추가
4. 조건부 렌더링 로직 수정

#### 2.2.3 각 권한별 대시보드 컴포넌트 수정
- `userId` props 추가하여 필터링 지원

| 컴포넌트 | 수정 내용 |
|----------|----------|
| `DoctorDashboard` | `doctorId?: number` props 추가 |
| `NurseDashboard` | `nurseId?: number` props 추가 |
| `LISDashboard` | `userId?: number` props 추가 |
| `RISDashboard` | `userId?: number` props 추가 |
| `ExternalDashboard` | `institutionId?: number` props 추가 |
| `PatientDashboardPreview` | `patientId?: number` props 추가 |

---

## 3. 상세 설계

### 3.1 UI 설계

```
┌─────────────────────────────────────────────────────────┐
│ 시스템 현황 대시보드                                      │
├─────────────────────────────────────────────────────────┤
│ [OVERVIEW] [DOCTOR] [NURSE] [LIS] [RIS] [EXTERNAL] [PT] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  사용자 선택: [▼ 전체 현황        ]                      │
│               ┌─────────────────┐                       │
│               │ 전체 현황        │ ← 집계 뷰 (기존)      │
│               │ 김철수 (doctor1) │                       │
│               │ 이영희 (doctor2) │                       │
│               │ 박민수 (doctor3) │                       │
│               └─────────────────┘                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  │   선택된 사용자의 대시보드 또는 전체 집계 뷰      │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 데이터 흐름

```
탭 전환
  ↓
fetchUsersByRole(roleCode) 호출
  ↓
사용자 목록 드롭다운 렌더링
  ↓
사용자 선택 (또는 "전체 현황")
  ↓
[전체 현황] → 기존 집계 대시보드 렌더링
[특정 사용자] → 해당 userId로 대시보드 렌더링 (API에 userId 전달)
```

### 3.3 컴포넌트 Props 설계

```typescript
// 각 대시보드 공통 props
interface DashboardFilterProps {
  userId?: number;        // 특정 사용자 필터 (없으면 전체)
  isPreview?: boolean;    // SystemManager에서 미리보기 모드인지
}

// 예: DoctorDashboard
interface DoctorDashboardProps extends DashboardFilterProps {
  // 기존 props...
}
```

---

## 4. 파일별 수정 내역

### 4.1 백엔드

| 파일 | 작업 |
|------|------|
| `apps/accounts/views.py` | `UsersByRoleListView` 추가 |
| `apps/accounts/urls.py` | URL 패턴 추가 |
| `apps/dashboard/views.py` | 각 stats API에 user_id 필터 추가 |

### 4.2 프론트엔드

| 파일 | 작업 |
|------|------|
| `src/services/users.api.ts` | `fetchUsersByRole()` 추가 |
| `src/services/dashboard.api.ts` | 각 stats 함수에 userId 파라미터 추가 |
| `src/pages/dashboard/systemManager/SystemManagerDashboard.tsx` | 드롭다운 UI + state 추가 |
| `src/pages/dashboard/systemManager/SystemManagerDashboard.css` | 드롭다운 스타일 추가 |
| `src/pages/dashboard/doctor/DoctorDashboard.tsx` | `doctorId` props 지원 |
| `src/pages/dashboard/nurse/NurseDashboard.tsx` | `nurseId` props 지원 |
| `src/pages/dashboard/lis/LISDashboard.tsx` | `userId` props 지원 |
| `src/pages/dashboard/ris/RISDashboard.tsx` | `userId` props 지원 |
| `src/pages/dashboard/external/ExternalDashboard.tsx` | `institutionId` props 지원 |

---

## 5. 구현 순서

### Phase 1: 백엔드 API
1. `UsersByRoleListView` 추가 및 URL 연결
2. 각 대시보드 stats API에 user_id 필터 파라미터 추가

### Phase 2: 프론트엔드 API
1. `fetchUsersByRole()` 함수 추가
2. 대시보드 API 함수들에 userId 파라미터 추가

### Phase 3: SystemManagerDashboard UI
1. 드롭다운 컴포넌트 추가
2. 탭별 사용자 목록 로드 로직 추가
3. 선택된 사용자에 따른 조건부 렌더링

### Phase 4: 각 대시보드 컴포넌트 수정
1. props에 userId 추가
2. API 호출 시 userId 전달
3. 데이터 필터링 로직 적용

---

## 6. 예상 소요 작업량

| 단계 | 예상 파일 수 | 비고 |
|------|-------------|------|
| Phase 1 | 3개 | 백엔드 API |
| Phase 2 | 2개 | 프론트엔드 API |
| Phase 3 | 2개 | SystemManagerDashboard |
| Phase 4 | 6개 | 각 권한별 대시보드 |
| **합계** | **13개** | |

---

## 7. 기존 대시보드 처리 방안

### 7.1 "전체 현황" 옵션
- 드롭다운 첫 번째 항목: "전체 현황"
- 선택 시 기존 집계 대시보드 렌더링 (변경 없음)

### 7.2 특정 사용자 선택 시
- 해당 사용자 ID로 API 호출
- 해당 사용자 관점의 대시보드 렌더링

### 7.3 하위 호환성
- 기존 대시보드 컴포넌트들은 userId 없이도 동작 (기본값: 전체)
- 점진적 마이그레이션 가능

---

## 8. 참고 사항

### 8.1 이미 구현된 부분
- `fetchExternalInstitutions()` - EXTERNAL 역할 사용자 목록 API (완료)
- EXTERNAL 역할 및 더미 데이터 (완료)

### 8.2 추가 고려 사항
- PATIENT 탭의 경우 환자 수가 많을 수 있음 → 검색 기능 추가 고려
- 캐싱 전략: 사용자 목록은 탭 전환 시마다 로드 vs 최초 1회 로드

---

**작성일**: 2026-01-14
**작성자**: Claude Code
