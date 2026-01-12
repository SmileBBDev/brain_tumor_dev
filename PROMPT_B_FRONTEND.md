# B (Frontend) 작업 지시

## 목표
API 응답 형식 처리 개선 및 경로 일관성 확인

## 현재 상태
다음 파일들은 이미 수정됨 (참고용):
- `TodayAppointmentCard.tsx` - 배열/객체 양쪽 처리
- `SummaryTab.tsx` - 배열/객체 양쪽 처리, 경로 `/patientsCare`로 변경

---

## 작업 1: 경로 일관성 확인

### 1.1 `/patientsCare` 경로 사용 확인
**중요**: `/patients/care` → `/patientsCare`로 변경됨

다음 파일들에서 경로 확인 및 수정:

```bash
# 검색 명령
grep -r "patients/care" src/
grep -r "/patients/care" src/
```

### 1.2 확인할 파일 목록
- `src/pages/patient/PatientListTable.tsx` - 진료 버튼 경로
- `src/pages/patient/PatientListPage.tsx` - 네비게이션
- 기타 `navigate()` 또는 `<Link>` 사용하는 곳

### 1.3 수정 예시
```typescript
// 수정 전
navigate(`/patients/care?patientId=${patient.id}`)

// 수정 후
navigate(`/patientsCare?patientId=${patient.id}`)
```

---

## 작업 2: API 함수 타입 개선 (선택사항)

### 2.1 encounter.api.ts 개선
**파일**: `src/services/encounter.api.ts`

API 함수에서 응답 형식을 처리하도록 개선:

```typescript
// 기존
export const getTodayEncounters = async (): Promise<Encounter[]> => {
  const response = await api.get<Encounter[]>('/encounters/today/');
  return response.data;
};

// 개선 (응답 형식 자동 처리)
export const getTodayEncounters = async (): Promise<Encounter[]> => {
  const response = await api.get('/encounters/today/');
  const data = response.data;
  return Array.isArray(data) ? data : data?.results || [];
};

export const getPatientEncounters = async (patientId: number): Promise<Encounter[]> => {
  const response = await api.get(`/encounters/patient/${patientId}/`);
  const data = response.data;
  return Array.isArray(data) ? data : data?.results || [];
};
```

### 2.2 ocs.api.ts 확인
**파일**: `src/services/ocs.api.ts`

`getOCSByPatient()` 함수가 있는지 확인하고 동일하게 처리

### 2.3 ai.api.ts 확인
**파일**: `src/services/ai.api.ts`

`getPatientAIRequests()` 함수가 있는지 확인하고 동일하게 처리

---

## 작업 3: 콘솔 에러 확인

### 3.1 테스트 시나리오
1. `doctor1 / doctor1001` 로그인
2. `/patientsCare` 접속 → 콘솔 에러 없음 확인
3. `/patients` → 환자 클릭 → 요약 탭 → 콘솔 에러 없음 확인

### 3.2 확인할 에러
```
TypeError: xxx.slice is not a function
TypeError: xxx is not iterable
Cannot read properties of undefined
```

---

## 완료 기준 체크리스트

- [ ] 모든 `/patients/care` 경로가 `/patientsCare`로 변경됨
- [ ] TodayAppointmentCard에서 금일 예약 환자 목록 정상 표시
- [ ] SummaryTab에서 진료이력, OCS, AI 추론 이력 정상 표시
- [ ] 콘솔에 에러 없음

---

## 이미 수정된 파일 (건드리지 말 것)

### TodayAppointmentCard.tsx
```typescript
const response = await getTodayEncounters();
const data = Array.isArray(response) ? response : (response as any)?.results || [];
setAppointments(data);
```

### SummaryTab.tsx
```typescript
const encounterData = Array.isArray(encounterRes) ? encounterRes : (encounterRes as any)?.results || [];
const ocsData = Array.isArray(ocsRes) ? ocsRes : (ocsRes as any)?.results || [];
const aiData = Array.isArray(aiRes) ? aiRes : (aiRes as any)?.results || [];
```

경로도 이미 수정됨:
```typescript
onClick={() => navigate(`/patientsCare?patientId=${patientId}&encounterId=${enc.id}`)}
```

---

## 주의사항

1. **이미 수정된 파일은 다시 수정하지 않음**
2. 경로 변경 시 `Link`, `navigate()`, `useNavigate()` 모두 확인
3. 백엔드 API가 배열을 반환하도록 수정되면, 프론트엔드 처리 로직은 양쪽 모두 호환됨
