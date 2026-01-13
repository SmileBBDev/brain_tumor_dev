# B 에이전트 (Frontend)

## 담당 영역
- `brain_tumor_front/` (React + TypeScript)
- 컴포넌트, 페이지, 서비스, 타입

## 규칙
- API 응답 방어적 처리: `Array.isArray(data) ? data : data?.results || []`
- 타입 정의 필수
- 기존 CSS 패턴 따르기
- **CSS는 시스템 변수 사용**: `var(--card-bg)`, `var(--text-main)` 등 (`variables.css` 참조)

## 참고 문서
- `SHARED.md`: 공용 정보 (비밀번호, 역할, 경로)
- `PROJECT_DOCS.md`: 프로젝트 아키텍처
- `AI_MODELS.md`: AI 모델 정의 (M1, MG, MM)
- `TODO_BACKLOG.md`: 전체 백로그
- `src/assets/style/variables.css`: CSS 변수 정의

## 주의사항
- AI 추론 관련 페이지(`pages/ai-inference/`)는 **다른 작업자가 작업 중** - 건드리지 말 것
- **TypeScript export**: `export type` 사용, import시 `import type { Type }` 분리

---

## 📋 현재 작업 지시서 (2026-01-13)

### 🔴 작업 1: 오탕크 뷰어 복수 화면 버그 수정 (긴급)

**문제**: 복수 화면에서 이전 설정 화면 클릭 시 'Base Series' 선택은 남아있지만 실제 데이터 리셋

**원인**: `PacsSelector.jsx`가 `initialSelection`의 `baseSeriesId`, `baseSeriesName`을 내부 상태로 초기화하지 않음

**수정 파일**: `src/components/PacsSelector.jsx`

**수정 내용**:
```javascript
// 추가: initialSelection 복원 useEffect (기존 useEffect 아래에 추가)
useEffect(() => {
  if (initialSelection?.baseSeriesId) {
    setBaseSeriesId(initialSelection.baseSeriesId);
    setBaseSeriesName(initialSelection.baseSeriesName || "");
  }
  if (initialSelection?.overlaySeriesId) {
    setOverlaySeriesId(initialSelection.overlaySeriesId);
    setOverlaySeriesName(initialSelection.overlaySeriesName || "");
  }
}, [initialSelection?.baseSeriesId, initialSelection?.overlaySeriesId]);
```

**테스트**:
1. V1에서 Series 선택
2. V2 추가 후 Series 선택
3. V1으로 복귀 → 데이터가 유지되는지 확인

---

### 작업 2: OCS 페이지 통합

**목표**: `/ocs/status` + `/ocs/manage` 통합

**작업 내용**:
1. `/ocs/manage` 기능을 `/ocs/status`로 흡수
2. 'OCS 생성버튼' 권한 분기 (DOCTOR, SYSTEMMANAGER만 표시)
3. `/ocs/manage` 페이지 제거 또는 리다이렉트

**수정 파일**:
- `src/pages/ocs/OCSStatusPage.tsx`
- `src/router/routeMap.tsx`
- 메뉴 설정 (A와 협업)

---

### 작업 3: `/ocs/process-status` 신규 생성

**참고**: `/ocs/ris/process-status` 구조 참고

**작업 내용**:
1. `src/pages/ocs/OCSProcessStatusPage.tsx` 생성
2. RIS + LIS 통합 처리 현황 표시
3. 라우트 등록

---

### 작업 4: 진료 페이지 개선 (`/patientsCare`)

**작업 내용**:
1. 금일 예약환자 기능을 `/patientsCare?patientId=12`에서도 사용 가능하게
2. `patientId=null` 처리: "환자 ID 조회필요" 표시
3. "환자 선택하지 않기" 버튼 추가
4. 상세페이지 기능 이전 완료 후 `/patientsCare` = `/patientsCare?patientId=null`

---

### 작업 5: 의사 Dashboard 개선

**작업 내용**:
1. 하드코딩 제거
2. "오늘 진료목록" → "금일 예약환자" (현 시간 기준 5명)
3. `/patientsCare`로 연결
4. API 연동 (A와 협업)

---

### 작업 6: System Dashboard → 외부기관 Dashboard 이동 기능

**작업 내용**:
- SystemManagerDashboard에 외부기관 Dashboard 바로가기 추가

---

### 작업 7: `/ai` 페이지 재구성

**현재**: 하드코딩, 기본 네비게이션

**변경**:
- 드롭다운 형식 네비게이션
- 구성:
  - AI 요청 목록 (`/ai/requests`)
  - AI 처리 현황 (`/ai/process-status`)
  - AI 모델 정보 (`/ai/models`) - M1, MG, MM 설명/성능 표시

---

## CSS 변수 참조 (variables.css)

```css
/* 자주 사용하는 변수 */
--card-bg: #ffffff;
--card-border: #e4e8f5;
--text-main: #1f2937;
--text-sub: #6b7280;
--bg-main: #f4f6f9;
--border: #e5e7eb;
--primary: #5b6fd6;
--primary-dark: #4a5bc4;
--success: #5fb3a2;
--warning: #f2a65a;
--danger: #e56b6f;
--info: #5b8def;
--radius-md: 8px;
--shadow-card: 0 4px 12px rgba(0,0,0,0.08);
```

---

## TypeScript 타입 export 규칙

**올바른 방법**:
```typescript
// dashboard.api.ts
export type AdminStats = { ... }

// AdminDashboard.tsx
import { getAdminStats } from '@/services/dashboard.api';
import type { AdminStats } from '@/services/dashboard.api';
```

---

## 완료 보고 방법

각 작업 완료 후 C 에이전트에게 보고:
- 수정한 파일 목록
- 테스트 결과
- 발생한 이슈 (있는 경우)
