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

## 완료된 작업 (2026-01-12)

### ✅ 페이지 UI 개선 - 완료
- `/patients` 페이지: filter-bar 레이아웃 통합, CSS 변수 적용
- `/encounters` 페이지: 불필요한 `<h1>진료 목록</h1>` 삭제
- `/ocs/manage` 페이지: CSS 변수 적용, 테이블 스타일 추가
- `/nurse/reception` 페이지: 의사선택 탭 CSS 수정 (흰글씨 문제)
- 환자진료 캘린더: CSS 변수 적용 (흰글씨 문제)

### ✅ Dashboard 구현 - 완료
- AdminDashboard, ExternalDashboard, SystemManagerDashboard
- DashboardRouter 수정

### ✅ ClinicPage 개선 - 완료
- ExaminationTab CSS 분리
- ClinicPage.css 변수 통일
- AI 수동 요청 버튼 추가

---

## 최근 수정 파일

| 파일 | 내용 |
|------|------|
| `src/pages/patient/PatientListPage.tsx` | filter-bar 구조 개선 |
| `src/assets/style/patientListView.css` | CSS 변수 적용 |
| `src/pages/encounter/EncounterListPage.tsx` | h1 제거 |
| `src/pages/ocs/OCSManagePage.css` | CSS 변수, 테이블 스타일 |
| `src/pages/nurse/NurseReceptionPage.css` | doctor-tab 색상 수정 |
| `src/pages/clinic/components/CalendarCard.tsx` | CSS 변수 적용 |

---

## CSS 변수 참조 (variables.css)

```css
/* 자주 사용하는 변수 */
--card-bg: #ffffff;           /* 카드 배경 */
--card-border: #e4e8f5;       /* 카드 테두리 */
--text-main: #1f2937;         /* 주 텍스트 */
--text-sub: #6b7280;          /* 부 텍스트 */
--bg-main: #f4f6f9;           /* 메인 배경 */
--border: #e5e7eb;            /* 일반 테두리 */
--primary: #5b6fd6;           /* 주 색상 */
--primary-dark: #4a5bc4;      /* 주 색상 (어두움) */
--success: #5fb3a2;           /* 성공 */
--warning: #f2a65a;           /* 경고 */
--danger: #e56b6f;            /* 위험 */
--info: #5b8def;              /* 정보 */
--radius-md: 8px;             /* 보더 반경 */
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

**틀린 방법** (Vite 에러 발생):
```typescript
// dashboard.api.ts
export interface AdminStats { ... }  // ❌

// AdminDashboard.tsx
import { getAdminStats, AdminStats } from '@/services/dashboard.api';  // ❌
```

---

## 완료 기준

- [x] ExaminationTab.tsx에 AI 추론 요청 섹션 추가
- [x] dashboard.api.ts 생성
- [x] AdminDashboard 컴포넌트 생성 (tsx + css)
- [x] ExternalDashboard 컴포넌트 생성 (tsx + css)
- [x] DashboardRouter에 ADMIN/EXTERNAL 케이스 추가
- [x] CSS 시스템 변수 사용
- [x] ExaminationTab CSS 분리
- [x] ClinicPage.css 변수 통일
- [x] SystemManagerDashboard 기능 구현
- [x] 페이지별 UI 개선 (/patients, /encounters, /ocs/manage, /nurse/reception)
