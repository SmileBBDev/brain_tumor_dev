# 프로젝트 현황 (Project Status)

**최종 업데이트**: 2026-01-11
**현재 버전**: Phase 3 OCS 통합 완료, Phase 4 준비중

---

## 📊 전체 진행 상황

| 모듈 | 상태 | 완료율 | 비고 |
|------|------|--------|------|
| **인증/권한 시스템** | ✅ 완료 | 100% | JWT, Role 기반, WebSocket 실시간 업데이트 |
| **환자 관리 (patients)** | ✅ 완료 | 100% | CRUD, 검색, 페이지네이션 |
| **진료 관리 (encounters)** | ✅ 완료 | 100% | CRUD, 고급 필터링, 통계 |
| **OCS (오더 통합 관리)** | ✅ 완료 | 100% | 단일 테이블 설계, API/마이그레이션 완료 |
| **영상 관리 (imaging)** | ✅ 완료 | 100% | OCS 통합 완료, ImagingStudy-OCS FK 연결 |
| **검사실 (LIS)** | ✅ 완료 | 100% | OCS job_role='LIS', GENETIC/PROTEIN 지원 |
| **AI 추론 (ai_inference)** | ✅ 완료 | 100% | 모델 3개(M1/MG/MM), API 완료, 결과 검토 |
| **치료 관리 (treatment)** | ✅ 완료 | 100% | 치료 계획/세션 CRUD |
| **경과 추적 (followup)** | ✅ 완료 | 100% | 경과 기록 CRUD |
| **관리자** | 🚧 부분 구현 | 60% | 사용자/권한/감사로그 일부 구현 |

---

## 🎯 완료된 모듈 상세

### 1. 인증/권한 시스템 ✅
**완료일**: 2025-12-XX
**담당**: 초기 구현

#### 주요 기능
- ✅ JWT 기반 로그인/로그아웃
- ✅ Role 기반 권한 관리 (DOCTOR, NURSE, RIS, LIS, SYSTEMMANAGER, ADMIN)
- ✅ 메뉴별 권한 설정
- ✅ WebSocket을 통한 실시간 권한 업데이트
- ✅ 세션 관리 (30분 타임아웃, 연장 모달)
- ✅ 비밀번호 변경 강제 기능

#### 기술 스택
- **Backend**: Django REST Framework, Simple JWT
- **Frontend**: React Context API, Axios
- **WebSocket**: Django Channels (Daphne)

#### 특이사항
- **2026-01-07**: 권한 체크 로직 비활성화 (`apps/menus/services.py`)
- 현재 모든 사용자가 모든 메뉴에 접근 가능

---

### 2. 환자 관리 (Patient Management) ✅
**완료일**: 2025-12-XX
**담당**: 초기 구현

#### 주요 기능
- ✅ 환자 CRUD (Create, Read, Update, Delete)
- ✅ Soft Delete 패턴
- ✅ 페이지네이션 (20건/페이지)
- ✅ 검색 기능 (이름, 환자번호)
- ✅ 환자 상세 정보 조회

#### API 엔드포인트
- `GET /api/patients/` - 목록
- `GET /api/patients/{id}/` - 상세
- `POST /api/patients/` - 생성
- `PUT /api/patients/{id}/` - 수정
- `DELETE /api/patients/{id}/` - 삭제

#### 더미 데이터
- 스크립트 위치: `dummy_data/create_dummy_patients.py`
- 30명의 환자 데이터 (P2026-0001 ~ P2026-0030)
- 📖 자세한 사용법: [dummy_data/README.md](brain_tumor_back/dummy_data/README.md)

---

### 3. 진료 관리 (Encounter Management) ✅
**완료일**: 2026-01-XX
**담당**: 초기 구현

#### 주요 기능
- ✅ 진료 CRUD
- ✅ Soft Delete 패턴
- ✅ 페이지네이션 (20건/페이지)
- ✅ 고급 검색 및 필터링
  - 환자명, 환자번호, 주호소 검색
  - 진료 유형, 상태, 진료과, 담당의사 필터
  - 날짜 범위 검색
- ✅ 진료 완료/취소 처리
- ✅ 진료 통계 API
- ✅ 입원중 환자 표시
- ✅ 검색 가능한 Select (환자/의사)

#### API 엔드포인트
- `GET /api/encounters/` - 목록
- `GET /api/encounters/{id}/` - 상세
- `POST /api/encounters/` - 생성
- `PATCH /api/encounters/{id}/` - 수정
- `DELETE /api/encounters/{id}/` - 삭제
- `POST /api/encounters/{id}/complete/` - 완료
- `POST /api/encounters/{id}/cancel/` - 취소
- `GET /api/encounters/statistics/` - 통계

#### 더미 데이터
- 스크립트 위치: `dummy_data/create_dummy_encounters.py`
- 20건의 진료 데이터
- 📖 자세한 사용법: [dummy_data/README.md](brain_tumor_back/dummy_data/README.md)

---

### 4. OCS (오더 통합 관리) ✅
**완료일**: 2026-01-11
**담당**: Phase 3 구현

#### 핵심 설계 특징
- ✅ **단일 테이블 설계**: OCS, OCSHistory 두 테이블로 모든 오더 통합 관리
- ✅ **JSON 기반 확장성**: `doctor_request`, `worker_result`, `attachments` JSON 필드
- ✅ **job_role 구분**: RIS, LIS, TREATMENT, CONSULT 등 역할별 분리
- ✅ **상태 워크플로우**: ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED
- ✅ **마이그레이션 적용 완료**: 5개 마이그레이션 모두 적용
- ✅ **API 테스트 완료**: 목록/상세/필터링/상태변경 모두 정상 동작

#### 현재 데이터
- OCS 레코드: 54건 (RIS 33건, LIS 21건)
- OCSHistory 레코드: 8건

#### 데이터 구조
```
OCS (단일 테이블)
├─ ocs_id (사용자 친화적 ID: ocs_0001)
├─ ocs_status (ORDERED/ACCEPTED/IN_PROGRESS/RESULT_READY/CONFIRMED/CANCELLED)
├─ job_role (RIS/LIS/TREATMENT/CONSULT)
├─ job_type (MRI/CT/BLOOD/SURGERY 등)
├─ doctor_request (JSON) - 의사 요청 정보
├─ worker_result (JSON) - 작업자 결과 정보
└─ attachments (JSON) - 첨부파일 정보

OCSHistory (변경 이력)
├─ action (CREATED/ACCEPTED/STARTED/RESULT_SAVED/CONFIRMED 등)
├─ from_status, to_status
├─ from_worker, to_worker
└─ snapshot_json (변경 시점 데이터)
```

#### job_role별 worker_result 템플릿
- **RIS**: findings, impression, tumor(detected/location/size), dicom, work_notes
- **LIS**: test_results, summary, interpretation
- **TREATMENT**: procedure, duration_minutes, anesthesia, outcome, complications

#### API 엔드포인트
- `GET /api/ocs/` - OCS 목록
- `GET /api/ocs/{id}/` - OCS 상세
- `POST /api/ocs/` - OCS 생성
- `PATCH /api/ocs/{id}/` - OCS 수정
- `POST /api/ocs/{id}/accept/` - 오더 접수
- `POST /api/ocs/{id}/start/` - 작업 시작
- `POST /api/ocs/{id}/submit/` - 결과 제출
- `POST /api/ocs/{id}/confirm/` - 의사 확정
- `POST /api/ocs/{id}/cancel/` - 취소
- `GET /api/ocs/worklist/{job_role}/` - 부서별 워크리스트

---

### 5. 영상 관리 (Imaging) ✅
**완료일**: 2026-01-11
**담당**: Phase 3 OCS 통합

#### ⚠️ 중요 변경사항 (2026-01-08)
- **ImagingStudy**: DICOM 메타데이터만 유지, 오더 정보는 OCS에서 관리
- **ImagingReport 삭제**: OCS.worker_result JSON으로 통합
- **API 하위 호환성 유지**: 기존 `/api/imaging/` 엔드포인트 그대로 사용

#### OCS 통합 완료 (2026-01-11)
- ✅ ImagingStudy → OCS 1:1 FK 연결 정상 작동
- ✅ 33건의 ImagingStudy 레코드 (모두 OCS와 연결됨)
- ✅ 판독 정보 OCS.worker_result에서 정상 조회

#### 현재 구조
```
ImagingStudy (DICOM 메타데이터)
├─ ocs (FK) - OCS 오더와 1:1 연결
├─ modality, body_part
├─ study_uid, accession_number
├─ series_count, instance_count
└─ scheduled_at, performed_at

판독 정보 (OCS.worker_result JSON)
├─ findings (판독 소견)
├─ impression (판독 결론)
├─ tumor.detected (종양 발견 여부)
├─ tumor.location (종양 위치)
├─ tumor.size (종양 크기)
├─ _confirmed (서명 완료 여부)
└─ work_notes (작업 노트 배열)
```

#### API 엔드포인트 (하위 호환)
**ImagingStudy** (내부적으로 OCS 사용):
- `GET /api/imaging/studies/` - 목록
- `GET /api/imaging/studies/{id}/` - 상세
- `POST /api/imaging/studies/` - 생성 (OCS job_role='RIS' 생성)
- `PATCH /api/imaging/studies/{id}/` - 수정
- `DELETE /api/imaging/studies/{id}/` - 삭제
- `POST /api/imaging/studies/{id}/complete/` - 검사 완료
- `POST /api/imaging/studies/{id}/cancel/` - 검사 취소
- `GET /api/imaging/studies/worklist/` - RIS 워크리스트
- `GET /api/imaging/studies/patient-history/` - 환자 히스토리

**ImagingReport** (내부적으로 OCS.worker_result 사용):
- `GET /api/imaging/reports/` - 목록
- `GET /api/imaging/reports/{id}/` - 상세
- `POST /api/imaging/reports/` - 생성
- `PATCH /api/imaging/reports/{id}/` - 수정
- `DELETE /api/imaging/reports/{id}/` - 삭제
- `POST /api/imaging/reports/{id}/sign/` - 서명

#### 프론트엔드 페이지
1. **ImagingListPage** (`/imaging/studies`) - 영상 검사 목록
2. **ImagingReportPage** (`/imaging/reports`) - 판독 전용 페이지
3. **ImagingPage** (`/imaging`) - 영상 조회 (미구현)
4. **ImagingWorklistPage** (`/ris/worklist`) - RIS 워크리스트
5. **PatientImagingHistoryPage** (`/imaging/patient-history`) - 환자 히스토리

#### 더미 데이터
- 스크립트 위치: `dummy_data/create_dummy_imaging.py`
- ⚠️ OCS 통합 후 업데이트 필요

#### 향후 계획
- **Phase 4**: Orthanc PACS 연동, DICOM 뷰어 (Cornerstone.js)
- **Phase 5+**: OHIF Viewer, AI Overlay, 3D

상세: [apps/imaging/README.md](brain_tumor_back/apps/imaging/README.md), [app_확장계획.md](app_확장계획.md)

---

### 6. 검사실 (LIS) ✅
**완료일**: 2026-01-11
**담당**: Phase 3 OCS 통합

#### 주요 기능
- ✅ OCS job_role='LIS'로 통합 관리
- ✅ 21건의 LIS 오더 정상 동작
- ✅ BLOOD, GENETIC, PROTEIN, URINE, CSF, BIOPSY 등 다양한 검사 유형 지원
- ✅ gene_mutations, protein_markers, RNA_seq 필드 지원

#### job_type 목록
- CBC, BMP, CMP, LFT, RFT, Lipid Panel, Thyroid Panel
- Coagulation, Urinalysis, Tumor Markers
- GENETIC, PROTEIN (AI 추론용)

---

### 7. AI 추론 (ai_inference) ✅
**완료일**: 2026-01-11
**담당**: Phase 3-4 구현

#### 완료된 기능
- ✅ `apps/ai_inference/` 앱 생성 및 URL 등록 (`/api/ai/`)
- ✅ AIModel 모델: M1(MRI), MG(Genetic), MM(Multimodal) 3개 정의
- ✅ AIInferenceRequest 모델: 추론 요청 관리
- ✅ AIInferenceResult 모델: 추론 결과 및 검토
- ✅ AIInferenceLog 모델: 추론 과정 로깅
- ✅ 마이그레이션 적용 완료
- ✅ API Views/Serializers 구현 완료
- ✅ 데이터 검증 API (`/api/ai/requests/validate/`)
- ✅ 환자별 사용 가능 모델 조회 (`/api/ai/patients/{id}/available-models/`)

#### 현재 데이터
- AIModel: 3건 (M1, MG, MM)
- AIInferenceRequest: 10건
- AIInferenceResult: 1건

#### API 엔드포인트
- `GET /api/ai/models/` - 모델 목록
- `GET /api/ai/requests/` - 추론 요청 목록
- `GET /api/ai/requests/{id}/` - 요청 상세 (결과 포함)
- `POST /api/ai/requests/validate/` - 데이터 검증
- `GET /api/ai/results/` - 결과 목록
- `GET /api/ai/patients/{id}/available-models/` - 환자별 사용 가능 모델

#### 남은 작업 (Phase 4+)
- [ ] AI 추론 요청 프론트엔드 페이지
- [ ] Redis Queue + Worker 기본 구현
- [ ] 실제 AI 모델 연동

---

### 8. 치료 관리 (treatment) ✅
**완료일**: 2026-01-09
**담당**: Phase 3 구현

#### 주요 기능
- ✅ 치료 계획 CRUD (TreatmentPlan)
- ✅ 치료 세션 CRUD (TreatmentSession)
- ✅ 치료 유형: surgery, radiation, chemotherapy, observation

---

### 9. 경과 추적 (followup) ✅
**완료일**: 2026-01-09
**담당**: Phase 3 구현

#### 주요 기능
- ✅ 경과 기록 CRUD (FollowUp)
- ✅ 환자별 경과 조회
- ✅ KPS Score 기록

---

## 🚧 부분 구현된 모듈

### 1. 관리자 (Admin)
**진행률**: 60%

#### 완료된 기능
- ✅ 사용자 목록 (UserList)
- ✅ 사용자 상세 (UserDetailPage)
- ✅ 메뉴 권한 관리 (MenuPermissionPage)
- ✅ 감사 로그 (AuditLog)
- ✅ 시스템 모니터 (SystemMonitorPage)

#### 미완성/필요한 기능
- ❌ 역할 관리 (ADMIN_ROLE) - Coming Soon
- ❌ 사용자 생성/수정 UI 개선
- ❌ 권한 매트릭스 시각화

---

## 🔧 최근 변경 사항 (Changelog)

### 2026-01-09
#### AI Inference 앱 구현
- ✅ **AI Inference 앱 생성**
  - `apps/ai_inference/` 앱 생성
  - AIModel 모델: 확장 가능한 AI 모델 정의 (M1, MG, MM)
  - AIInferenceRequest 모델: 추론 요청 관리
  - AIInferenceResult 모델: 추론 결과 및 의사 검토
  - AIInferenceLog 모델: 추론 과정 로깅

- ✅ **AI 모델 시드 데이터 추가**
  - `setup_dummy_data.py`에 `create_ai_models()` 함수 추가
  - M1: MRI 4-Channel Analysis (T1, T2, T1C, FLAIR)
  - MG: Genetic Analysis (RNA_seq)
  - MM: Multimodal Analysis (MRI + 유전 + 단백질)

- ✅ **LIS job_type 확장**
  - `apps/ocs/models.py` job_type 도움말에 GENETIC, PROTEIN 추가
  - `app의 기획.md` LIS worker_result 템플릿에 RNA_seq, gene_mutations, protein, protein_markers 추가

#### 결과 보고서 첨부파일 표시
- ✅ `OCSResultReportPage.tsx`에 첨부파일 섹션 추가
- ✅ `OCSResultReportPage.css`에 첨부파일 스타일 추가

#### LIS Alert 페이지 삭제
- ❌ **LISAlertPage 삭제**
  - `brain_tumor_front/src/pages/ocs/LISAlertPage.tsx` 파일 삭제
  - `routeMap.tsx`에서 LIS_ALERT 매핑 제거
  - `pages/ocs/index.ts`에서 export 제거
  - `setup_dummy_data.py`에서 LIS_ALERT 메뉴/권한 생성 코드 제거
  - 사유: 불필요한 기능으로 판단

---

### 2026-01-08
#### OCS-Imaging 통합 완료
- ✅ **OCS 모델 구현**
  - OCS 단일 테이블 (job_role: RIS/LIS/TREATMENT/CONSULT)
  - OCSHistory 변경 이력 테이블
  - JSON 기반 확장 구조 (doctor_request, worker_result, attachments)
  - job_role별 worker_result 템플릿 (RIS 종양 정보 포함)

- ✅ **Imaging-OCS 통합**
  - ImagingStudy → OCS 1:1 FK 연결
  - ImagingReport 모델 삭제 → OCS.worker_result JSON으로 통합
  - 마이그레이션 작성 (0004_ocs_integration.py)
  - Serializers/Views 재작성 (하위 호환성 유지)

- ✅ **프론트엔드 업데이트**
  - imaging.ts 타입 업데이트 (work_notes 배열, ocs_id 추가)
  - ImagingEditModal work_notes 배열 지원
  - PatientImagingHistoryPage encounter 접근 방식 수정

- ✅ **Admin 업데이트**
  - ImagingStudyAdmin OCS 연동으로 수정
  - ImagingReportAdmin 삭제

---

### 2026-01-07
#### 영상 관리 모듈 (Imaging)
- ✅ **권한 시스템 비활성화**
  - `apps/menus/services.py`: 모든 활성화된 메뉴 반환
  - 모든 역할이 모든 메뉴에 접근 가능

- ✅ **URL 라우팅 수정**
  - `config/urls.py`: imaging API 경로 추가 (`/api/imaging/`)
  - `config/settings.py`: INSTALLED_APPS에 imaging 추가

- ✅ **판독 페이지 분리**
  - `ImagingReportPage.tsx`: 판독 전용 페이지 신규 생성
  - 영상 목록과 판독 페이지 명확히 구분
  - 완료된 검사만 판독 대상으로 표시

- ✅ **사이드바 메뉴 활성화 수정**
  - `SidebarItem.tsx`: NavLink에 `end` prop 추가
  - 경로 정확히 일치할 때만 active 상태 적용
  - 부모 경로 포함 시 활성화되는 문제 해결

- ✅ **더미 데이터 스크립트 통합 관리**
  - 모든 더미 데이터 스크립트를 `dummy_data/` 폴더로 통합

---

## 📁 프로젝트 구조

### 백엔드 (brain_tumor_back)
```
brain_tumor_back/
├── config/                           # Django 설정
│   ├── settings.py                   # 공통 설정
│   ├── urls.py                       # URL 라우팅
│   └── asgi.py                       # WebSocket 설정
├── apps/
│   ├── accounts/                     # 사용자 관리 ✅
│   ├── authorization/                # 인증/권한 ✅
│   ├── menus/                        # 메뉴 관리 ✅
│   ├── audit/                        # 감사 로그 ✅
│   ├── common/                       # 공통 유틸
│   ├── patients/                     # 환자 관리 ✅
│   ├── encounters/                   # 진료 관리 ✅
│   ├── ocs/                          # OCS 오더 통합 관리 ✅
│   ├── imaging/                      # 영상 관리 (OCS 통합) ✅
│   ├── ai_inference/                 # AI 추론 관리 ✅ (신규)
│   ├── treatment/                    # 치료 관리 ✅ (신규)
│   └── followup/                     # 경과 추적 ✅ (신규)
├── dummy_data/                       # 더미 데이터 생성 스크립트
│   ├── create_dummy_patients.py      # 환자 데이터
│   ├── create_dummy_encounters.py    # 진료 데이터
│   ├── create_dummy_imaging.py       # 영상 데이터
│   └── README.md                     # 📖 사용법 문서
└── manage.py
```

### 프론트엔드 (brain_tumor_front)
```
brain_tumor_front/
├── src/
│   ├── pages/
│   │   ├── auth/                     # 로그인/권한
│   │   ├── dashboard/                # 대시보드
│   │   ├── patient/                  # 환자 관리 ✅
│   │   ├── encounter/                # 진료 관리 ✅
│   │   ├── imaging/                  # 영상 관리 ✅
│   │   ├── ris/                      # RIS (부분)
│   │   ├── admin/                    # 관리자 (부분)
│   │   └── common/                   # 공통 컴포넌트
│   ├── router/                       # 라우팅
│   ├── services/                     # API 호출
│   ├── socket/                       # WebSocket
│   ├── types/                        # TypeScript 타입
│   └── assets/                       # 스타일/이미지
└── vite.config.ts
```

---

## 🔑 주요 기술 스택

### 백엔드
- **Framework**: Django 5.0 + Django REST Framework
- **Database**: MySQL
- **Authentication**: Simple JWT
- **WebSocket**: Django Channels (Daphne)
- **Pagination**: PageNumberPagination (20건/페이지)

### 프론트엔드
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **WebSocket**: Native WebSocket API
- **State Management**: React Context API

### 개발 도구
- **Version Control**: Git
- **Code Editor**: VSCode
- **API Testing**: Django REST Framework Browsable API

---

## 📝 코딩 컨벤션

### 백엔드
- **모델**: PascalCase (예: `ImagingStudy`, `OCS`)
- **Serializer**: PascalCase + Serializer (예: `ImagingStudySerializer`)
- **ViewSet**: PascalCase + ViewSet (예: `ImagingStudyViewSet`)
- **API URL**: kebab-case (예: `/api/imaging/studies/`)
- **Soft Delete**: `is_deleted` 필드 사용

### 프론트엔드
- **컴포넌트**: PascalCase (예: `ImagingListPage`)
- **함수/변수**: camelCase (예: `fetchStudies`)
- **타입**: PascalCase (예: `ImagingStudy`)
- **CSS 클래스**: kebab-case (예: `menu-link`)

---

## 🐛 알려진 이슈

### 현재 이슈
1. **권한 체크 비활성화** (의도적)
   - `apps/menus/services.py`에서 권한 체크 로직 제거됨
   - 모든 사용자가 모든 메뉴 접근 가능
   - 필요시 권한 체크 재활성화 필요

### 해결된 이슈
1. ✅ **영상 목록 404 에러** (2026-01-07 해결)
2. ✅ **사이드바 메뉴 활성화 중복** (2026-01-07 해결)
3. ✅ **ImagingReport import 에러** (2026-01-08 해결)
4. ✅ **OCS 마이그레이션 미적용** (2026-01-11 해결) - 5개 마이그레이션 모두 적용 완료
5. ✅ **Imaging-OCS 통합 에러** (2026-01-11 해결) - FK 연결 및 API 정상 동작

---

## 🚀 다음 할 일 (TODO)

### 완료됨 ✅ (2026-01-11)
1. ✅ **OCS 마이그레이션 적용 및 테스트**
   - ✅ OCS 모델/Serializer/View 정상 동작
   - ✅ OCS API 엔드포인트 테스트 완료
   - ✅ 5개 마이그레이션 모두 적용

2. ✅ **Imaging-OCS 통합 테스트**
   - ✅ ImagingStudy-OCS FK 연결 정상
   - ✅ OCS.worker_result 판독 정보 조회 정상
   - ✅ API 하위 호환성 유지

3. ✅ **ai_inference 앱 API 구현**
   - ✅ Views/Serializers 구현 완료
   - ✅ 데이터 검증 API
   - ✅ 환자별 사용 가능 모델 조회

### 단기 (Phase 4)
1. [ ] **AI 추론 프론트엔드**
   - [ ] AI 추론 요청 페이지
   - [ ] 데이터 충족 여부 UI 표시
   - [ ] 결과 검토 페이지

2. [ ] **권한 시스템 재활성화**
   - [ ] 메뉴별 권한 체크
   - [ ] 역할별 접근 제어

### 중기 (Phase 4-5)
1. [ ] **영상 뷰어 고도화**
   - [ ] Orthanc PACS 연동
   - [ ] DICOM 뷰어 (Cornerstone.js)
   - [ ] OHIF Viewer 통합

2. [ ] **AI 추론 워커**
   - [ ] Redis Queue + Worker 구현
   - [ ] 실제 AI 모델 연동

### 장기 (Phase 5+)
1. [ ] AI Overlay 및 Heatmap
2. [ ] Multi-Modality Fusion
3. [ ] 3D Visualization

---

## 📞 문의 및 이슈 보고

이슈 발견 시 GitHub Issues에 등록하거나 팀에 문의해주세요.

---

**작성자**: Claude
**최종 업데이트**: 2026-01-11
