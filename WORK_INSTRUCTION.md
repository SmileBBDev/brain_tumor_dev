# 작업 지시서: API 응답 형식 통일 및 버그 수정

## 1. 현재 문제 현황

### 1.1 API 응답 형식 불일치 문제
프론트엔드에서 API 응답을 배열로 기대하지만, 백엔드가 페이지네이션 객체(`{count, results}`)를 반환하여 에러 발생

**에러 예시:**
```
TypeError: encounterData.slice is not a function
TypeError: appointments is not iterable
```

### 1.2 영향받는 API 엔드포인트
| API | 현재 응답 형식 | 프론트엔드 기대 형식 |
|-----|---------------|---------------------|
| `GET /api/encounters/today/` | `{count, date, results}` | `Encounter[]` |
| `GET /api/encounters/patient/{id}/` | `{count, results}` | `Encounter[]` |
| `GET /api/ocs/patient/{id}/` | 확인 필요 | `OCSListItem[]` |
| `GET /api/ai/requests/patient/{id}/` | 확인 필요 | `AIInferenceRequest[]` |

---

## 2. 백엔드 (A = brain_tumor_back) 작업

### 2.1 API 응답 형식 통일
**원칙**: 단일 목록 반환 API는 배열을 직접 반환, 페이지네이션이 필요한 API만 `{count, results}` 형식 사용

### 2.2 수정할 엔드포인트

#### (1) `/api/encounters/today/` 수정
**파일**: `apps/encounters/views.py`

```python
@action(detail=False, methods=['get'])
def today(self, request):
    """금일 예약된 진료 목록 조회 - 배열 직접 반환"""
    today = timezone.now().date()
    queryset = self.get_queryset().filter(
        admission_date__date=today
    )

    status_filter = request.query_params.get('status', 'scheduled')
    if status_filter and status_filter != 'all':
        queryset = queryset.filter(status=status_filter)

    queryset = queryset.order_by('admission_date')
    serializer = EncounterListSerializer(queryset, many=True)

    # 배열 직접 반환 (기존: {count, date, results})
    return Response(serializer.data)
```

#### (2) `/api/encounters/patient/{patient_id}/` 수정
**파일**: `apps/encounters/views.py`

```python
@action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>\\d+)')
def by_patient(self, request, patient_id=None):
    """특정 환자의 진료 이력 조회 - 배열 직접 반환"""
    queryset = self.get_queryset().filter(
        patient_id=patient_id
    ).order_by('-admission_date')

    serializer = EncounterListSerializer(queryset, many=True)

    # 배열 직접 반환
    return Response(serializer.data)
```

#### (3) `/api/ocs/patient/{patient_id}/` 확인 및 수정
**파일**: `apps/ocs/views.py`

```python
@action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>\\d+)')
def by_patient(self, request, patient_id=None):
    """특정 환자의 OCS 이력 조회 - 배열 직접 반환"""
    queryset = self.get_queryset().filter(
        patient_id=patient_id
    ).order_by('-created_at')

    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)
```

#### (4) `/api/ai/requests/patient/{patient_id}/` 확인 및 수정
**파일**: `apps/ai_inference/views.py`

```python
@action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>\\d+)')
def by_patient(self, request, patient_id=None):
    """특정 환자의 AI 추론 이력 조회 - 배열 직접 반환"""
    queryset = self.get_queryset().filter(
        patient_id=patient_id
    ).order_by('-requested_at')

    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)
```

### 2.3 더미 데이터 확인
**파일**: `setup_dummy_data/setup_dummy_data_1_base.py`

오늘 날짜의 `scheduled` 상태 Encounter가 있는지 확인:
```python
# create_dummy_encounters 함수에서
# 일부 진료를 오늘 날짜 + scheduled 상태로 생성
from django.utils import timezone

# 오늘 예약 진료 생성 (테스트용)
for i in range(3):
    Encounter.objects.create(
        patient=random.choice(patients),
        attending_doctor=random.choice(doctors),
        admission_date=timezone.now(),
        status='scheduled',
        encounter_type='outpatient',
        department='neurology',
        chief_complaint='정기 진료'
    )
```

---

## 3. 프론트엔드 (B = brain_tumor_front) 작업

### 3.1 이미 수정된 파일 (참고용)
다음 파일들은 이미 배열/객체 양쪽 응답을 처리하도록 수정됨:

#### TodayAppointmentCard.tsx
```typescript
const response = await getTodayEncounters();
const data = Array.isArray(response) ? response : (response as any)?.results || [];
setAppointments(data);
```

#### SummaryTab.tsx
```typescript
const encounterData = Array.isArray(encounterRes) ? encounterRes : (encounterRes as any)?.results || [];
const ocsData = Array.isArray(ocsRes) ? ocsRes : (ocsRes as any)?.results || [];
const aiData = Array.isArray(aiRes) ? aiRes : (aiRes as any)?.results || [];
```

### 3.2 경로 통일 확인
**중요**: `/patients/care` → `/patientsCare`로 변경됨

확인할 파일들:
- `src/pages/patient/tabs/SummaryTab.tsx` - 진료 클릭 시 이동 경로 ✅ 수정됨
- `src/pages/clinic/components/TodayAppointmentCard.tsx` - 환자 선택 시 이동 경로 ✅ 수정됨
- `src/pages/patient/PatientListTable.tsx` - 진료 버튼 경로 확인 필요

### 3.3 API 함수 타입 정의 개선 (선택사항)
**파일**: `src/services/encounter.api.ts`

```typescript
// 응답 타입을 더 유연하게 정의
type ListResponse<T> = T[] | { results: T[]; count?: number };

export const getTodayEncounters = async (): Promise<Encounter[]> => {
  const response = await api.get<ListResponse<Encounter>>('/encounters/today/');
  const data = response.data;
  return Array.isArray(data) ? data : data.results || [];
};

export const getPatientEncounters = async (patientId: number): Promise<Encounter[]> => {
  const response = await api.get<ListResponse<Encounter>>(`/encounters/patient/${patientId}/`);
  const data = response.data;
  return Array.isArray(data) ? data : data.results || [];
};
```

---

## 4. 작업 순서

### Phase 1: 백엔드 API 응답 형식 수정 (A)
1. `apps/encounters/views.py` - `today()`, `by_patient()` 배열 반환으로 수정
2. `apps/ocs/views.py` - `by_patient()` 확인 및 수정
3. `apps/ai_inference/views.py` - `by_patient()` 확인 및 수정
4. 더미 데이터에 오늘 날짜 예약 추가

### Phase 2: 프론트엔드 경로 및 호출 확인 (B)
1. `/patientsCare` 경로 사용 일관성 확인
2. API 호출 함수에서 응답 형식 처리 확인
3. 에러 발생 시 빈 배열 반환 처리 확인

---

## 5. 테스트 시나리오

### 5.1 금일 예약 환자 목록
```bash
# API 직접 테스트
curl http://localhost:8000/api/encounters/today/ -H "Authorization: Bearer {token}"

# 기대 응답: 배열
[
  {"id": 1, "patient_name": "홍길동", "status": "scheduled", ...},
  {"id": 2, "patient_name": "김철수", "status": "scheduled", ...}
]
```

### 5.2 환자별 진료 이력
```bash
curl http://localhost:8000/api/encounters/patient/1/ -H "Authorization: Bearer {token}"

# 기대 응답: 배열
[
  {"id": 5, "admission_date": "2026-01-10", "status": "completed", ...},
  {"id": 3, "admission_date": "2026-01-05", "status": "completed", ...}
]
```

### 5.3 UI 테스트
1. `doctor1 / doctor1001` 로그인
2. `/patientsCare` 접속 → 금일 예약 환자 카드에 목록 표시 확인
3. `/patients` → 환자 클릭 → `/patients/{id}?tab=summary` → 진료 이력 표시 확인

---

## 6. 파일 목록

### Backend (A)
```
apps/
├── encounters/
│   └── views.py          # today(), by_patient() 수정
├── ocs/
│   └── views.py          # by_patient() 확인/수정
├── ai_inference/
│   └── views.py          # by_patient() 확인/수정
└── setup_dummy_data/
    └── setup_dummy_data_1_base.py  # 오늘 예약 데이터 추가
```

### Frontend (B)
```
src/
├── pages/
│   ├── clinic/
│   │   └── components/
│   │       └── TodayAppointmentCard.tsx  # ✅ 이미 수정됨
│   └── patient/
│       ├── PatientListTable.tsx          # 경로 확인
│       └── tabs/
│           └── SummaryTab.tsx            # ✅ 이미 수정됨
└── services/
    ├── encounter.api.ts  # 타입 개선 (선택)
    ├── ocs.api.ts        # 타입 개선 (선택)
    └── ai.api.ts         # 타입 개선 (선택)
```

---

## 7. 완료 기준

### A (백엔드) 완료 조건
- [ ] `/api/encounters/today/` 가 배열을 직접 반환
- [ ] `/api/encounters/patient/{id}/` 가 배열을 직접 반환
- [ ] `/api/ocs/patient/{id}/` 가 배열을 직접 반환
- [ ] `/api/ai/requests/patient/{id}/` 가 배열을 직접 반환
- [ ] 오늘 날짜의 scheduled 상태 Encounter 데이터 존재

### B (프론트엔드) 완료 조건
- [ ] TodayAppointmentCard에서 금일 예약 환자 목록 정상 표시
- [ ] SummaryTab에서 진료이력, OCS, AI 추론 이력 정상 표시
- [ ] 모든 `/patientsCare` 경로 사용 일관성 확인
- [ ] 콘솔 에러 없음
