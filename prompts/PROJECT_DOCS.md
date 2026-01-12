# NeuroNova CDSS - 프로젝트 통합 문서

> **프로젝트**: Brain Tumor Clinical Decision Support System
> **최종 업데이트**: 2026-01-12
> **현재 Phase**: Phase 4 준비중 (AI 추론 프론트엔드)

---

## 1. 프로젝트 개요

### 1.1 목적
뇌종양 진단 및 치료를 위한 임상 의사결정 지원 시스템 (CDSS)

### 1.2 기술 스택
```
Backend:  Django REST Framework + MySQL
Frontend: React + TypeScript + Vite + MUI
Auth:     JWT + RBAC (Role-Based Access Control)
Realtime: Django Channels (WebSocket)
```

### 1.3 핵심 원칙
- **7-Layer Architecture**: Controller(views) → Service → Repository/Client
- **단일 진실 소스**: OCS 테이블로 모든 오더 통합 관리
- **JSON 확장성**: worker_result 필드로 유연한 데이터 구조

---

## 2. 시스템 구조

### 2.1 백엔드 앱 구조 (현재)
```
apps/
├── accounts/      ✅ 인증/권한 (JWT, Role)
├── audit/         ✅ 감사 로그
├── authorization/ ✅ 권한 관리
├── menus/         ✅ 동적 메뉴
├── common/        ✅ 공통 유틸
├── patients/      ✅ 환자 관리
├── encounters/    ✅ 진료 관리
├── ocs/           ✅ OCS 오더 통합 (RIS/LIS/TREATMENT)
├── imaging/       ✅ 영상 검사 (OCS 연동)
├── ai_inference/  ✅ AI 추론 (API 완료)
├── treatment/     ✅ 치료 관리
├── followup/      ✅ 경과 추적
└── orthancproxy/  ✅ Orthanc PACS 프록시
```

### 2.2 프론트엔드 구조
```
src/
├── pages/
│   ├── auth/        로그인/권한
│   ├── dashboard/   대시보드 (역할별)
│   ├── patient/     환자 관리
│   ├── encounter/   진료 관리
│   ├── imaging/     영상 관리
│   ├── ocs/         OCS 워크리스트
│   ├── ai/          AI 분석 (구현 예정)
│   └── admin/       관리자
├── router/          라우팅
├── api/             API 호출
└── stores/          Zustand 상태
```

---

## 3. OCS (Order Communication System)

### 3.1 핵심 설계
```
OCS (단일 테이블)
├─ ocs_id           사용자 친화적 ID (ocs_0001)
├─ ocs_status       ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED
├─ job_role         RIS / LIS / TREATMENT / CONSULT
├─ job_type         MRI / CT / BLOOD / GENETIC / SURGERY 등
├─ doctor_request   JSON (의사 요청 정보)
├─ worker_result    JSON (작업자 결과 - job_role별 템플릿)
└─ attachments      JSON (첨부파일)

OCSHistory (변경 이력)
├─ action           CREATED / ACCEPTED / STARTED / CONFIRMED 등
├─ from_status → to_status
└─ snapshot_json
```

### 3.2 worker_result 템플릿

**RIS (영상검사)**:
```json
{
  "_template": "RIS",
  "_confirmed": false,
  "findings": "",
  "impression": "",
  "tumor": { "detected": false, "location": {}, "size": {} },
  "dicom": { "study_uid": "", "series_count": 0 },
  "work_notes": []
}
```

**LIS (검사실)**:
```json
{
  "_template": "LIS",
  "test_type": "BLOOD|GENETIC|PROTEIN",
  "test_results": [],
  "RNA_seq": null,
  "gene_mutations": [],
  "protein_markers": []
}
```

---

## 4. AI 추론 시스템

### 4.1 모델 정의

| 코드 | 모델명 | 입력 요구사항 | OCS 소스 |
|------|--------|---------------|----------|
| **M1** | MRI 4-Channel | T1, T2, T1C, FLAIR | RIS |
| **MG** | Genetic Analysis | RNA_seq | LIS (GENETIC) |
| **MM** | Multimodal | MRI + 유전 + 단백질 | RIS + LIS |

### 4.2 추론 워크플로우
```
1. 환자 선택 → OCS 목록 조회
2. 모델 선택 (M1/MG/MM)
3. required_keys 기반 데이터 충족 확인
4. 모두 충족 → 추론 요청 생성
5. AI Worker 처리 (TODO: Redis Queue)
6. 결과 저장 → 의사 검토
```

### 4.3 API
```
GET  /api/ai/models/                        모델 목록
GET  /api/ai/requests/                      추론 요청 목록
POST /api/ai/requests/validate/             데이터 검증
GET  /api/ai/patients/{id}/available-models/ 환자별 사용 가능 모델
POST /api/ai/results/{id}/review/           결과 검토
```

---

## 5. Orthanc Proxy (DICOM 관리)

### 5.1 개요
Orthanc PACS 서버와의 통신을 프록시하여 DICOM 영상 관리 기능 제공

**기술 스택**: Django REST Framework + pydicom + requests

### 5.2 핵심 기능

| 기능 | 설명 |
|------|------|
| **DICOM 계층 조회** | Patient → Study → Series → Instance 계층 탐색 |
| **폴더 기반 업로드** | 여러 DICOM 파일 일괄 업로드, series_path로 Series 그룹화 |
| **자동 정리** | 빈 Series/Study/Patient 자동 삭제 |
| **DICOM 태그 수정** | PatientID, StudyInstanceUID, SeriesInstanceUID 자동 설정 |

### 5.3 설정
```python
# settings.py
ORTHANC_BASE_URL = "http://localhost:8042"
ORTHANC_DEBUG_LOG = True  # 선택
```

### 5.4 응답 구조 예시

**환자 목록**:
```json
{
  "orthancId": "abc123...",
  "patientId": "P2026-0001",
  "patientName": "홍길동",
  "studiesCount": 3
}
```

**Instance 메타데이터**:
```json
{
  "orthancId": "instance-id",
  "instanceNumber": "1",
  "sopInstanceUID": "1.2.840.xxx",
  "rows": "512", "columns": "512",
  "sliceThickness": "1.0",
  "sliceLocation": "-50.0"
}
```

### 5.5 주의사항
- Orthanc 서버 필수 (localhost:8042)
- 일부 API는 AllowAny 권한 (프로덕션 수정 필요)
- API 호출 타임아웃: 10-30초

---

## 6. 라우팅 & 메뉴 시스템

### 6.1 핵심 원칙
```
menu.code === permission.code === routeMap 키
```

### 6.2 메뉴 유형

| 유형 | 조건 | 용도 |
|------|------|------|
| **그룹 메뉴** | `path = NULL` | 펼침/접힘 부모 (PATIENT, ORDER, IMAGING) |
| **화면 메뉴** | `path 있음, breadcrumb_only = 0` | 사이드바 표시 + 클릭 이동 |
| **숨김 메뉴** | `breadcrumb_only = 1` | 사이드바 미표시 (상세 페이지용) |

### 6.3 현재 메뉴 구조
```
DASHBOARD
PATIENT (그룹)
├── PATIENT_LIST
├── PATIENT_DETAIL (breadcrumb_only)
└── PATIENT_CARE

ORDER (그룹)
├── ORDER_LIST
├── ORDER_CREATE (breadcrumb_only)
└── OCS_ORDER

IMAGING (그룹)
├── IMAGE_VIEWER
├── RIS_WORKLIST
├── OCS_RIS
├── OCS_RIS_DETAIL (breadcrumb_only)
└── RIS_DASHBOARD

LAB (그룹)
├── LAB_RESULT_VIEW
├── OCS_LIS
├── OCS_LIS_DETAIL (breadcrumb_only)
└── LIS_PROCESS_STATUS

AI_SUMMARY
NURSE_RECEPTION
ADMIN (그룹)
```

### 6.4 새 메뉴 추가 절차

**Step 1: DB**
```sql
-- 1. menus_menu
INSERT INTO menus_menu (code, path, icon, parent_id, breadcrumb_only, `order`, is_active)
VALUES ('NEW_MENU', '/new-path', 'icon-name', {parent_id}, 0, 1, 1);

-- 2. accounts_permission
INSERT INTO accounts_permission (code, name, description)
VALUES ('NEW_MENU', '새 메뉴', '설명');

-- 3. menus_menupermission 연결
INSERT INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.code = 'NEW_MENU';

-- 4. 역할에 권한 부여
INSERT INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM accounts_role r
JOIN accounts_permission p ON p.code = 'NEW_MENU'
WHERE r.code IN ('SYSTEMMANAGER', 'ADMIN');

-- 5. 메뉴 라벨
INSERT INTO menus_menulabel (role, text, menu_id)
VALUES ('DEFAULT', '새 메뉴', {menu_id});
```

**Step 2: Frontend**
```tsx
// src/router/routeMap.tsx
import NewMenuPage from '@/pages/new/NewMenuPage';

export const routeMap: Record<string, ComponentType> = {
  // ...
  NEW_MENU: NewMenuPage,
};
```

---

## 7. 역할별 권한

| 역할 | 접근 가능 |
|------|----------|
| **SYSTEMMANAGER** | 모든 메뉴 |
| **ADMIN** | 대시보드, 환자, 오더, 영상, 검사, AI, 관리자(시스템 모니터링 제외) |
| **DOCTOR** | 대시보드, 환자, 오더, 영상 뷰어, RIS Worklist |
| **NURSE** | 대시보드, 환자, 오더, 영상 뷰어, 검사 결과 |
| **RIS** | 대시보드, 영상 뷰어, RIS Worklist |
| **LIS** | 대시보드, 검사 결과 조회/업로드 |

---

## 8. 개발 Phase

### Phase 1-3: 완료 ✅
- 환자/진료 관리
- OCS 통합 (RIS/LIS)
- Imaging-OCS 연동
- AI Inference API
- Treatment/FollowUp

### Phase 4: 현재 진행
- [ ] AI 추론 프론트엔드
  - [ ] AI 요청 페이지
  - [ ] 데이터 충족 여부 UI
  - [ ] 결과 검토 페이지
- [ ] 치료/경과 프론트엔드
- [ ] 환자 진료 페이지 (Clinic)

### Phase 5+: 예정
- [ ] Orthanc PACS 연동
- [ ] DICOM 뷰어 (Cornerstone.js/OHIF)
- [ ] Redis Queue + AI Worker
- [ ] AI Overlay/Heatmap

---

## 9. 주요 API 엔드포인트

### 인증
```
POST /api/acct/login/
POST /api/acct/logout/
GET  /api/acct/me/
POST /api/acct/token/refresh/
```

### 환자/진료
```
GET/POST /api/patients/
GET/PATCH/DELETE /api/patients/{id}/
GET/POST /api/encounters/
GET/PATCH/DELETE /api/encounters/{id}/
```

### OCS
```
GET/POST /api/ocs/
GET/PATCH /api/ocs/{id}/
POST /api/ocs/{id}/accept/
POST /api/ocs/{id}/start/
POST /api/ocs/{id}/submit/
POST /api/ocs/{id}/confirm/
GET /api/ocs/worklist/{job_role}/
```

### 영상
```
GET/POST /api/imaging/studies/
GET/PATCH /api/imaging/studies/{id}/
POST /api/imaging/studies/{id}/complete/
GET /api/imaging/studies/worklist/
```

### AI
```
GET /api/ai/models/
GET/POST /api/ai/requests/
POST /api/ai/requests/validate/
GET /api/ai/results/
POST /api/ai/results/{id}/review/
```

### Orthanc Proxy (DICOM)
```
GET  /api/orthanc/patients/              전체 환자 목록
GET  /api/orthanc/studies/               환자별 Study 목록 (?patient_id=)
GET  /api/orthanc/series/                Study별 Series 목록 (?study_id=)
GET  /api/orthanc/instances/             Series별 Instance 목록 (?series_id=)
GET  /api/orthanc/instances/{id}/file/   DICOM 파일 다운로드
POST /api/orthanc/upload-patient/        DICOM 폴더 업로드
DELETE /api/orthanc/patients/{id}/       환자 삭제
DELETE /api/orthanc/studies/{id}/        Study 삭제
DELETE /api/orthanc/series/{id}/         Series 삭제
DELETE /api/orthanc/instances/{id}/      Instance 삭제
```

---

## 10. 데이터 현황 (2026-01-12)

| 테이블 | 레코드 수 |
|--------|----------|
| Patient | 30 |
| Encounter | 20 |
| OCS | 63 (RIS 33, LIS 30) |
| ImagingStudy | 33 |
| AIModel | 3 (M1, MG, MM) |
| AIInferenceRequest | 10 |
| AIInferenceResult | 1 |

---

## 11. 알려진 이슈

### 현재
- **권한 체크 비활성화** (의도적): `apps/menus/services.py`에서 모든 메뉴 반환
- **AI Worker 미구현**: Redis Queue 연동 필요

### 해결됨
- ✅ OCS 마이그레이션 (2026-01-11)
- ✅ Imaging-OCS FK 연결 (2026-01-11)
- ✅ AI Inference API (2026-01-11)

---

## 12. 참고 문서

| 문서 | 용도 |
|------|------|
| `다음 작업_*.md` | 현재 작업 현황 |
| `AGENT_COLLABORATION_PROMPTS.md` | A/B/C 에이전트 협업 규칙 |
| `ONBOARDING_CORE_ARCHITECTURE.md` | 전체 아키텍처 참조 (상위 폴더) |

---

**작성자**: Claude (C 역할)
**버전**: 1.0
