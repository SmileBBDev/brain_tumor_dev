# Brain Tumor CDSS 앱 기획서

## 프로젝트 개요

**작성일**: 2026-01-07
**수정일**: 2026-01-11
**프로젝트명**: Brain Tumor Clinical Decision Support System (CDSS)
**목적**: 뇌종양 진단 및 치료를 위한 임상 의사결정 지원 시스템

---

## 1. 시스템 개요

### 1.1 기본 방향
- **권한 인증 제외**: 기존 brain_tumor_dev의 인증/권한 시스템 활용
- **외부 시스템 제외**: Redis, OpenEMR, Orthanc, FHIR 서버 연동은 프로젝트 마지막 단계로 연기
- **기본 아키텍처**: Django + MySQL만으로 동작하는 CDSS 핵심 기능 구현
- **확장 가능성**: 추후 외부 시스템 연동을 위한 인터페이스 설계

### 1.2 핵심 기술 스택
```
Backend: Django REST Framework
Database: MySQL (단일 DB)
인증/권한: 기존 accounts 앱 활용 (JWT + RBAC)
Frontend: React (Vite) - 기존 구조 활용
실시간 통신: Django Channels (WebSocket) - 기존 구조 활용
```

---

## 2. CDSS 핵심 기능 정의

### 2.1 환자 관리 (Patient Management) [0107_12:28]
**목적**: 뇌종양 환자의 기본 정보 관리

**주요 기능**:
- 환자 등록/수정/조회/검색
- 환자 기본 정보: 이름, 생년월일, 성별, 연락처, 주민등록번호
- 환자 의료 정보: 혈액형, 알레르기, 기저질환
- 환자 상태 추적: 입원/외래/퇴원
- 환자별 진료 이력 조회

**데이터 모델**:
```python
Patient:
  - id (PK)
  - patient_number (환자번호, Unique)
  - name (이름)
  - birth_date (생년월일)
  - gender (성별: M/F)
  - ssn (주민등록번호, 암호화)
  - phone (연락처)
  - email (이메일)
  - address (주소)
  - blood_type (혈액형: A/B/O/AB, +/-)
  - allergies (알레르기, JSON)
  - chronic_diseases (기저질환, JSON)
  - status (상태: active/inactive/deceased)
  - created_at, updated_at
```

---

### 2.2 진료 관리 (Encounter Management) [0107_]
**목적**: 환자의 진료 세션 관리

**주요 기능**:
- 진료 등록 (외래/입원)
- 진료 상태 관리 (예약/진행중/완료/취소)
- 담당 의사 배정
- 진료 일시 및 장소 기록
- 주 진단명 및 부 진단명 기록

**데이터 모델**:
```python
Encounter:
  - id (PK)
  - patient (FK to Patient)
  - encounter_type (진료 유형: outpatient/inpatient/emergency)
  - status (상태: scheduled/in-progress/completed/cancelled)
  - attending_doctor (FK to User, 담당 의사)
  - department (진료과: neurology/neurosurgery)
  - admission_date (입원일시)
  - discharge_date (퇴원일시)
  - chief_complaint (주 호소)
  - primary_diagnosis (주 진단명)
  - secondary_diagnoses (부 진단명, JSON)
  - created_at, updated_at
```


====
---

### 2.3 영상 검사 관리 (Imaging Study Management)
**목적**: 뇌종양 진단을 위한 영상 검사 오더 및 결과 관리

**✅ 완료 (2026-01-08)**: OCS와 완전 통합됨

**주요 기능**:
- 영상 검사 오더 생성 (CT, MRI, PET 등) → OCS job_role='RIS'로 생성
- 검사 상태 추적 (OCS 상태 워크플로우 사용)
- 검사 이미지 메타데이터 저장 (DICOM은 추후 Orthanc 연동)
- 판독 소견 작성 및 서명 → OCS.worker_result JSON 사용
- RIS 워크리스트 제공 (OCS API 사용)

**데이터 모델 (OCS 통합 후)**:
```python
# ImagingStudy - DICOM 메타데이터만 관리
ImagingStudy:
  - id (PK)
  - ocs (FK to OCS, OneToOne)  # 오더 정보는 OCS에서 관리
  - modality (검사 종류: CT/MRI/PET/X-RAY)
  - body_part (촬영 부위: brain)
  - study_uid (Study Instance UID, Orthanc 연동용)
  - accession_number (Accession Number)
  - series_count (시리즈 수)
  - instance_count (이미지 수)
  - scheduled_at (예약 일시)
  - performed_at (검사 일시)
  - created_at, updated_at

# ImagingReport는 삭제됨 → OCS.worker_result JSON으로 통합
# OCS.worker_result (job_role='RIS') 템플릿:
{
  "_template": "RIS",
  "_version": "1.0",
  "_confirmed": false,  # 서명 완료 여부
  "dicom": {
    "study_uid": "",
    "series": [],
    "accession_number": "",
    "series_count": 0,
    "instance_count": 0
  },
  "findings": "",       # 판독 소견
  "impression": "",     # 판독 결론
  "recommendation": "", # 권고사항
  "tumor": {
    "detected": false,
    "location": {"lobe": "", "hemisphere": ""},
    "size": {"max_diameter_cm": null, "volume_cc": null}
  },
  "work_notes": []      # [{timestamp, author, content}, ...]
}
```

**API 엔드포인트** (하위 호환성 유지):
- 기존 `/api/imaging/studies/`, `/api/imaging/reports/` 엔드포인트 유지
- 내부적으로 OCS 모델 사용

---

### 2.4 AI 추론 관리 (AI Inference Management)
**목적**: OCS 데이터를 입력으로 AI 모델 추론 요청 및 결과 관리

**✅ 설계 완료 (2026-01-09)**: 확장 가능한 모델 정의 구조

**핵심 설계 원칙**:
- **OCS 기반 입력**: AI 추론은 OCS(RIS/LIS)의 `worker_result` JSON을 입력 데이터로 사용
- **Soft 모델 정의**: 모델 추가/변경이 용이하도록 JSON 기반 설정
- **데이터 검증**: 추론 요청 전 필요 데이터 존재 여부 자동 확인

**현재 모델 정의** (확장 가능):

| 모델 코드 | 모델명 | 입력 데이터 | OCS 소스 |
|----------|--------|------------|----------|
| **M1** | MRI 4-Channel | T1, T2, T1C, FLAIR | `ocs_ris` |
| **MG** | Genetic Analysis | RNA_seq | `ocs_lis` |
| **MM** | Multimodal | MRI + 유전 + 단백질 | `ocs_ris` + `ocs_lis` |

**모델 정의 구조** (JSON 기반 확장):
```python
# AIModel 테이블 또는 설정 파일
AI_MODELS = {
    "M1": {
        "code": "M1",
        "name": "MRI 4-Channel Analysis",
        "description": "MRI 4채널(T1, T2, T1C, FLAIR) 기반 뇌종양 분석",
        "ocs_sources": ["RIS"],
        "required_keys": {
            "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"]
        },
        "is_active": True
    },
    "MG": {
        "code": "MG",
        "name": "Genetic Analysis",
        "description": "RNA 시퀀싱 기반 유전자 분석",
        "ocs_sources": ["LIS"],
        "required_keys": {
            "LIS": ["RNA_seq"]  # job_type='GENETIC'인 OCS에서 조회
        },
        "is_active": True
    },
    "MM": {
        "code": "MM",
        "name": "Multimodal Analysis",
        "description": "MRI + 유전 + 단백질 통합 분석",
        "ocs_sources": ["RIS", "LIS"],
        "required_keys": {
            "RIS": ["dicom.T1", "dicom.T2", "dicom.T1C", "dicom.FLAIR"],
            "LIS": ["RNA_seq", "protein"]  # job_type='GENETIC', 'PROTEIN'인 OCS에서 조회
        },
        "is_active": True
    }
}
```

**추론 요청 워크플로우**:
```
1. AI 추론 요청 페이지 진입
       ↓
2. 환자 선택 → 해당 환자의 OCS 목록 조회
       ↓
3. 모델 선택 (M1/MG/MM/...)
       ↓
4. 선택한 모델의 required_keys 기반으로
   환자의 OCS(RIS/LIS) worker_result 검색
       ↓
5. 필요 데이터 충족 여부 표시
   ✅ T1: 있음 (ocs_0012)
   ✅ T2: 있음 (ocs_0012)
   ❌ T1C: 없음
   ❌ FLAIR: 없음
       ↓
6. 모두 충족 시 → "추론 요청" 버튼 활성화
   부족 시 → 부족 항목 안내
       ↓
7. 추론 요청 생성 → AI Worker에서 처리
       ↓
8. 결과 저장 및 의사 검토
```

**데이터 모델**:
```python
# AIModel (모델 정의 - soft 구조)
AIModel:
  - id (PK)
  - code (모델 코드: M1/MG/MM, UNIQUE)
  - name (모델명)
  - description (설명)
  - ocs_sources (JSON: ["RIS"], ["LIS"], ["RIS", "LIS"])
  - required_keys (JSON: 모델별 필요 데이터 키)
  - version (모델 버전)
  - is_active (활성화 여부)
  - created_at, updated_at

# AIInferenceRequest (추론 요청)
AIInferenceRequest:
  - id (PK)
  - request_id (사용자 친화적 ID: ai_req_0001)
  - patient (FK to Patient)
  - model (FK to AIModel)
  - ocs_references (JSON: 사용된 OCS ID 목록)
  - input_data (JSON: worker_result에서 추출한 입력 데이터)
  - status (상태: PENDING/PROCESSING/COMPLETED/FAILED)
  - requested_by (FK to User)
  - priority (우선순위: low/normal/high/urgent)
  - requested_at (요청 일시)
  - started_at (시작 일시)
  - completed_at (완료 일시)
  - error_message (에러 메시지)
  - created_at, updated_at

# AIInferenceResult (추론 결과)
AIInferenceResult:
  - id (PK)
  - inference_request (FK to AIInferenceRequest, OneToOne)
  - result_data (JSON: 모델별 결과 데이터)
  - confidence_score (신뢰도: 0.0~1.0)
  - visualization_paths (JSON: 시각화 파일 경로들)
  - reviewed_by (FK to User, 검토 의사)
  - review_status (검토 상태: pending/approved/rejected)
  - review_comment (검토 의견)
  - reviewed_at (검토 일시)
  - created_at, updated_at

# AIInferenceLog (추론 로그)
AIInferenceLog:
  - id (PK)
  - inference_request (FK to AIInferenceRequest)
  - action (동작: CREATED/STARTED/PROGRESS/COMPLETED/FAILED/REVIEWED)
  - message (로그 메시지)
  - details (JSON: 상세 정보)
  - created_at
```

**API 엔드포인트**:
```
# 모델 관리
GET    /api/ai/models/                    # 활성화된 모델 목록
GET    /api/ai/models/{code}/             # 모델 상세 (필요 데이터 포함)

# 데이터 검증
POST   /api/ai/validate/                  # 환자+모델 조합의 데이터 충족 여부 확인
       Body: { patient_id, model_code }
       Response: { valid: bool, available_keys: [], missing_keys: [] }

# 추론 요청
GET    /api/ai/requests/                  # 추론 요청 목록
POST   /api/ai/requests/                  # 추론 요청 생성
GET    /api/ai/requests/{id}/             # 요청 상세
GET    /api/ai/requests/{id}/status/      # 요청 상태 조회

# 추론 결과
GET    /api/ai/results/                   # 결과 목록
GET    /api/ai/results/{id}/              # 결과 상세
POST   /api/ai/results/{id}/review/       # 의사 검토 (승인/거부)

# 환자별 조회
GET    /api/ai/patients/{id}/requests/    # 환자별 추론 요청 이력
GET    /api/ai/patients/{id}/available-models/  # 환자가 사용 가능한 모델 목록
```

**Orthanc 앱 연동 (추후)**:
- Orthanc 앱은 별도 작업자가 개발 중
- 추후 통합 시 `dicom.*` 키는 Orthanc에서 데이터 조회
- 현재는 OCS.worker_result에서 메타데이터만 사용

---

### 2.5 치료 계획 관리 (Treatment Plan Management)
**목적**: 뇌종양 치료 계획 수립 및 추적

**주요 기능**:
- 치료 계획 수립 (수술/방사선/항암/경과관찰)
- 치료 일정 관리
- 치료 상태 추적
- 다학제 협진 의견 기록

**데이터 모델**:
```python
TreatmentPlan:
  - id (PK)
  - patient (FK to Patient)
  - encounter (FK to Encounter)
  - imaging_study (FK to ImagingStudy, nullable)
  - ai_result (FK to AIAnalysisResult, nullable)
  - treatment_type (치료 유형: surgery/radiation/chemotherapy/observation)
  - treatment_goal (치료 목표: curative/palliative)
  - plan_summary (치료 계획 요약)
  - planned_by (FK to User)
  - status (상태: planned/in-progress/completed/cancelled)
  - start_date (시작 예정일)
  - end_date (종료 예정일)
  - created_at, updated_at

TreatmentSession:
  - id (PK)
  - treatment_plan (FK to TreatmentPlan)
  - session_number (회차)
  - session_date (치료 일시)
  - performed_by (FK to User, 집도/시술 의사)
  - session_note (치료 기록)
  - adverse_events (부작용, JSON)
  - status (상태: scheduled/completed/cancelled)
  - created_at, updated_at
```

---

### 2.6 경과 추적 (Follow-up Management)
**목적**: 치료 후 경과 관찰 관리

**주요 기능**:
- 경과 관찰 일정 등록
- 추적 검사 결과 기록
- 재발 여부 판단
- 환자 상태 변화 추적

**데이터 모델**:
```python
FollowUp:
  - id (PK)
  - patient (FK to Patient)
  - treatment_plan (FK to TreatmentPlan)
  - followup_date (추적 일시)
  - followup_type (유형: routine/symptom-based/post-treatment)
  - imaging_study (FK to ImagingStudy, nullable)
  - clinical_status (임상 상태: stable/improved/deteriorated/recurrence)
  - symptoms (증상, JSON)
  - kps_score (Karnofsky Performance Score: 0~100)
  - next_followup_date (다음 추적 예정일)
  - note (경과 기록)
  - recorded_by (FK to User)
  - created_at, updated_at
```

---

### 2.7 오더 통합 관리 (OCS - Order Communication System)
**목적**: 모든 부서의 오더를 통합 관리하고 진행 상태 및 의견 공유

**✅ 완료 (2026-01-08)**: 단일 테이블 설계로 구현됨

**핵심 설계 원칙**:
- **단일 테이블 설계**: OCS, OCSHistory 두 테이블로 모든 오더 통합 관리
- **JSON 기반 확장성**: `doctor_request`, `worker_result`, `attachments` JSON 필드
- **job_role 구분**: RIS, LIS, TREATMENT, CONSULT 등 역할별 분리
- AI 추론은 별도 `ai_inference` 앱으로 분리 예정

**주요 기능**:
- 오더 통합 조회 (영상검사, 검사실, 치료, 협진)
- 부서별 오더 워크리스트 자동 생성
- 오더별 진행 상태 실시간 추적 (워크플로우 단계별)
- job_role별 worker_result 템플릿으로 유연한 데이터 관리
- 긴급 오더 우선순위 관리
- OCSHistory로 전체 변경 이력 추적

**데이터 모델** (현재 구현):
```python
# OCS (단일 테이블 - 모든 오더 통합)
OCS:
  - id (PK)
  - ocs_id (사용자 친화적 ID: ocs_0001)
  - ocs_status (ORDERED/ACCEPTED/IN_PROGRESS/RESULT_READY/CONFIRMED/CANCELLED)
  - patient (FK to Patient)
  - doctor (FK to User, 처방 의사)
  - worker (FK to User, 작업자)
  - encounter (FK to Encounter)
  - job_role (RIS/LIS/TREATMENT/CONSULT)
  - job_type (RIS: MRI/CT/PET/X-RAY, LIS: BLOOD/GENETIC/PROTEIN/URINE/CSF/BIOPSY, TREATMENT: SURGERY/RADIATION/CHEMOTHERAPY 등)
  - doctor_request (JSON) - 의사 요청 정보
  - worker_result (JSON) - 작업자 결과 정보 (job_role별 템플릿)
  - attachments (JSON) - 첨부파일 정보
  - ocs_result (Boolean) - 결과 정상/비정상
  - priority (urgent/normal/scheduled)
  - cancel_reason (취소 사유)
  - created_at, accepted_at, in_progress_at, result_ready_at, confirmed_at, cancelled_at

# OCSHistory (변경 이력)
OCSHistory:
  - id (PK)
  - ocs (FK to OCS)
  - actor (FK to User)
  - action (CREATED/ACCEPTED/STARTED/RESULT_SAVED/CONFIRMED 등)
  - from_status, to_status
  - from_worker, to_worker
  - reason (취소/변경 사유)
  - snapshot_json (변경 시점 데이터)
  - ip_address (접속 IP)
  - created_at
```

**job_role별 worker_result 템플릿**:
```python
# RIS (영상검사)
{
  "_template": "RIS",
  "findings": "", "impression": "", "recommendation": "",
  "tumor": {"detected": false, "location": {}, "size": {}},
  "dicom": {"study_uid": "", "series_count": 0},
  "work_notes": []
}

# LIS (검사실) - job_type: BLOOD, GENETIC, PROTEIN, URINE, CSF, BIOPSY 등
{
  "_template": "LIS",
  "test_type": "",  # BLOOD, GENETIC, PROTEIN, URINE, CSF, BIOPSY
  "test_results": [],
  "summary": "",
  "interpretation": "",
  # 유전자 검사 (GENETIC)
  "RNA_seq": null,  # RNA 시퀀싱 결과 (파일 경로 또는 데이터)
  "gene_mutations": [],  # 유전자 변이 목록
  # 단백질 검사 (PROTEIN)
  "protein": null,  # 단백질 분석 결과
  "protein_markers": []  # 단백질 마커 목록
}

# TREATMENT (치료)
{
  "_template": "TREATMENT",
  "procedure": "", "duration_minutes": null,
  "anesthesia": "", "outcome": "", "complications": null
}
```

**워크플로우**:
ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED/CANCELLED

**API 엔드포인트**:
- `GET/POST /api/ocs/` - OCS 목록/생성
- `GET/PATCH /api/ocs/{id}/` - OCS 상세/수정
- `POST /api/ocs/{id}/accept/` - 오더 접수
- `POST /api/ocs/{id}/start/` - 작업 시작
- `POST /api/ocs/{id}/submit/` - 결과 제출
- `POST /api/ocs/{id}/confirm/` - 의사 확정
- `GET /api/ocs/worklist/{job_role}/` - 부서별 워크리스트

**저장소 분리**:
- DICOM 영상: Orthanc (worker_result.dicom.study_uid로 연결)
- LIS 결과 파일: GCP Cloud Storage (추후 구현)
- 소견/메타데이터: MySQL (worker_result JSON)

**상세 설계**: [OCS–AI Inference Architecture Speci.md](../OCS–AI Inference Architecture Speci.md) 참조

====
---

## 3. 시스템 아키텍처

### 3.1 레이어드 아키텍처 (7-Layer)

```
┌─────────────────────────────────────┐
│  7. Controllers (API Endpoints)     │  ← views.py
├─────────────────────────────────────┤
│  6. Services (Business Logic)       │  ← services.py
├─────────────────────────────────────┤
│  5. Repositories (Data Access)      │  ← repositories.py (optional)
├─────────────────────────────────────┤
│  4. Clients (External Systems)      │  ← clients/ (추후 확장)
├─────────────────────────────────────┤
│  3. DTOs (Data Transfer Objects)    │  ← serializers.py
├─────────────────────────────────────┤
│  2. Domain (Entities)               │  ← models.py
├─────────────────────────────────────┤
│  1. Main (Integration)              │  ← urls.py
└─────────────────────────────────────┘
```









# 여기 중심으로 작업





### 3.2 Django 앱 구조 ✅ **현재 구현 상태 (2026-01-11)**

```
brain_tumor_back/
├── apps/
│   ├── accounts/          # ✅ 인증/권한 (재사용)
│   ├── audit/             # ✅ 감사 로그 (재사용)
│   ├── authorization/     # ✅ 권한 (재사용)
│   ├── menus/             # ✅ 메뉴 (재사용)
│   ├── common/            # ✅ 공통 유틸
│   │
│   ├── patients/          # ✅ 환자 관리 (완료)
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── encounters/        # ✅ 진료 관리 (완료)
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── ocs/               # ✅ OCS 오더 통합 관리 (완료)
│   │   ├── models.py      # OCS, OCSHistory
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── imaging/           # ✅ 영상 검사 관리 (OCS 통합 완료)
│   │   ├── models.py      # ImagingStudy (OCS FK)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── ai_inference/      # ✅ AI 추론 관리 (API 완료)
│   │   ├── models.py      # AIModel, AIInferenceRequest, AIInferenceResult, AIInferenceLog
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── treatment/         # ✅ 치료 관리 (완료)
│   │   ├── models.py      # TreatmentPlan, TreatmentSession
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── followup/          # ✅ 경과 추적 (완료)
│       ├── models.py      # FollowUp
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
```

---

## 4. 주요 API 엔드포인트 설계

### 4.1 환자 관리 API
```
GET    /api/patients/                    # 환자 목록 조회
POST   /api/patients/                    # 환자 등록
GET    /api/patients/{id}/               # 환자 상세 조회
PUT    /api/patients/{id}/               # 환자 정보 수정
DELETE /api/patients/{id}/               # 환자 삭제 (soft delete)
GET    /api/patients/search/?q={query}   # 환자 검색
GET    /api/patients/{id}/encounters/    # 환자별 진료 이력
GET    /api/patients/{id}/studies/       # 환자별 영상 검사 이력
GET    /api/patients/{id}/ai-results/    # 환자별 AI 분석 결과
```

### 4.2 진료 관리 API
```
GET    /api/encounters/                  # 진료 목록
POST   /api/encounters/                  # 진료 등록
GET    /api/encounters/{id}/             # 진료 상세
PUT    /api/encounters/{id}/             # 진료 수정
PATCH  /api/encounters/{id}/status/      # 진료 상태 변경
GET    /api/encounters/{id}/studies/     # 진료별 영상 검사
GET    /api/encounters/{id}/treatments/  # 진료별 치료 계획
```

### 4.3 영상 검사 관리 API
```
GET    /api/imaging/studies/              # 영상 검사 목록
POST   /api/imaging/studies/              # 검사 오더 생성
GET    /api/imaging/studies/{id}/         # 검사 상세
PATCH  /api/imaging/studies/{id}/status/  # 검사 상태 변경
POST   /api/imaging/reports/              # 판독문 작성
GET    /api/imaging/reports/{id}/         # 판독문 조회
PUT    /api/imaging/reports/{id}/         # 판독문 수정
POST   /api/imaging/reports/{id}/sign/    # 판독문 서명
```

### 4.4 AI 분석 API
```
GET    /api/ai/jobs/                      # AI 작업 목록
POST   /api/ai/jobs/                      # AI 분석 요청
GET    /api/ai/jobs/{id}/                 # 작업 상태 조회
GET    /api/ai/jobs/{id}/result/          # 분석 결과 조회
POST   /api/ai/jobs/{id}/review/          # 결과 검토 (승인/거부)
DELETE /api/ai/jobs/{id}/                 # 작업 취소
GET    /api/ai/models/                    # 사용 가능한 AI 모델 목록
```

### 4.5 치료 계획 API
```
GET    /api/treatment/plans/              # 치료 계획 목록
POST   /api/treatment/plans/              # 치료 계획 수립
GET    /api/treatment/plans/{id}/         # 치료 계획 상세
PUT    /api/treatment/plans/{id}/         # 치료 계획 수정
POST   /api/treatment/sessions/           # 치료 세션 등록
GET    /api/treatment/sessions/{id}/      # 세션 상세
PUT    /api/treatment/sessions/{id}/      # 세션 수정
```

### 4.6 경과 추적 API
```
GET    /api/followup/                     # 경과 목록
POST   /api/followup/                     # 경과 등록
GET    /api/followup/{id}/                # 경과 상세
PUT    /api/followup/{id}/                # 경과 수정
GET    /api/followup/patient/{id}/        # 환자별 경과
```

---

## 5. 데이터 흐름 예시

### 5.1 뇌종양 진단 워크플로우

```
1. 환자 내원 및 등록
   POST /api/patients/
   ↓
2. 진료 등록
   POST /api/encounters/
   ↓
3. 영상 검사 오더
   POST /api/imaging/studies/
   (modality: MRI, body_part: brain)
   ↓
4. 검사 수행 (상태 변경)
   PATCH /api/imaging/studies/{id}/status/
   (status: completed)
   ↓
5. AI 분석 요청
   POST /api/ai/jobs/
   (imaging_study_id, model_type: tumor_detection)
   ↓
6. AI 분석 결과 조회
   GET /api/ai/jobs/{id}/result/
   (tumor_detected: true, confidence: 0.95)
   ↓
7. 판독의 검토 및 판독문 작성
   POST /api/imaging/reports/
   (findings, impression, tumor_location, tumor_size)
   ↓
8. 판독문 서명
   POST /api/imaging/reports/{id}/sign/
   ↓
9. AI 결과 검토 및 승인
   POST /api/ai/jobs/{id}/review/
   (review_status: approved)
   ↓
10. 치료 계획 수립
    POST /api/treatment/plans/
    (treatment_type: surgery, plan_summary)
    ↓
11. 치료 세션 등록 및 수행
    POST /api/treatment/sessions/
    ↓
12. 경과 관찰
    POST /api/followup/
    (clinical_status, kps_score, next_followup_date)
```

---

## 6. 권한 설계 (RBAC)

### 6.1 역할 정의 (기존 시스템 확장)

| Role | 설명 | 주요 권한 |
|------|------|---------|
| admin | 시스템 관리자 | 전체 접근 |
| neurosurgeon | 신경외과 전문의 | 환자 관리, 진료, 수술 계획, AI 결과 검토 |
| neurologist | 신경과 전문의 | 환자 관리, 진료, 치료 계획 |
| radiologist | 영상의학과 전문의 | 영상 검사 판독, 판독문 서명 |
| radiologic_technologist | 방사선사 | 영상 검사 수행, 상태 업데이트 |
| nurse | 간호사 | 환자 조회, 경과 기록 |
| patient | 환자 | 본인 정보 조회 |

### 6.2 권한 매핑

```python
# 신규 권한 정의
PERMISSIONS = {
    # 환자 관리
    'view_patient': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'nurse', 'patient'],
    'add_patient': ['admin', 'neurosurgeon', 'neurologist', 'nurse'],
    'change_patient': ['admin', 'neurosurgeon', 'neurologist'],
    'delete_patient': ['admin'],

    # 진료 관리
    'view_encounter': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'nurse'],
    'add_encounter': ['admin', 'neurosurgeon', 'neurologist'],
    'change_encounter': ['admin', 'neurosurgeon', 'neurologist'],

    # 영상 검사
    'view_imaging_study': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist'],
    'add_imaging_study': ['admin', 'neurosurgeon', 'neurologist', 'radiologist'],
    'change_imaging_study': ['admin', 'radiologist', 'radiologic_technologist'],
    'add_imaging_report': ['admin', 'radiologist'],
    'sign_imaging_report': ['admin', 'radiologist'],

    # AI 분석
    'view_ai_job': ['admin', 'neurosurgeon', 'neurologist', 'radiologist'],
    'add_ai_job': ['admin', 'neurosurgeon', 'neurologist', 'radiologist'],
    'review_ai_result': ['admin', 'neurosurgeon', 'neurologist', 'radiologist'],

    # 치료 계획
    'view_treatment_plan': ['admin', 'neurosurgeon', 'neurologist', 'nurse'],
    'add_treatment_plan': ['admin', 'neurosurgeon', 'neurologist'],
    'change_treatment_plan': ['admin', 'neurosurgeon', 'neurologist'],

    # 경과 추적
    'view_followup': ['admin', 'neurosurgeon', 'neurologist', 'nurse'],
    'add_followup': ['admin', 'neurosurgeon', 'neurologist', 'nurse'],

    # OCS 오더 통합 관리
    'view_order': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist', 'nurse'],
    'add_order': ['admin', 'neurosurgeon', 'neurologist', 'radiologist'],
    'change_order': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist'],
    'cancel_order': ['admin', 'neurosurgeon', 'neurologist'],
    'update_order_progress': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist', 'nurse'],
    'view_order_comment': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist', 'nurse'],
    'add_order_comment': ['admin', 'neurosurgeon', 'neurologist', 'radiologist', 'radiologic_technologist', 'nurse'],
}
```

---

## 7. 오더 통합 관리 시스템 (OCS - Order Communication System)

**⚠️ 설계 변경 (2026-01-08)**:
- AI 추론 기능은 별도 `ai_inference` 앱으로 분리
- RIS/LIS/Treatment/Consultation을 별도 테이블로 분리
- READY는 파생 상태로 조건식 기반 자동 계산

### 7.1 개요
**목적**: 검사/치료 오더를 통합 관리하고 진행 상태 및 의견 공유

**핵심 개념**:
- OCS는 독립적인 Django 앱으로 구현
- RIS/LIS/Treatment/Consultation을 **별도 테이블**로 분리
- AI 추론은 별도 `ai_inference` 앱에서 관리 (OCS와 FK로 연결 가능)
- READY 상태는 **파생 상태** (조건식 기반 캐시)
- GCP 배포 기준 설계 (Cloud SQL, Cloud Storage, Orthanc)

### 7.2 테이블 구조

```
OCS (request_id)
├─ ocs_status (OPEN/BLOCKED/READY/CLOSED) ← 파생 상태
│
├─< RIS_REQUEST (영상검사 - 별도 테이블)
│    ├─ request_id, request_index
│    ├─ modality (CT/MRI/PET/X-RAY)
│    ├─ dicom_study_uid, dicom_series_uid
│    └─ imaging_study_id → ImagingReport로 소견 관리
│
├─< LIS_REQUEST (검사실 - 별도 테이블)
│    ├─ request_id, request_index
│    ├─ result_type (blood/genetic/urine/csf/biopsy)
│    ├─ result_file_uri (GCP Cloud Storage)
│    └─< LIS_COMMENT (소견)
│
├─< TREATMENT_REQUEST (치료 - 별도 테이블)
│    ├─ request_id, request_index
│    ├─ treatment_type (surgery/radiation/chemotherapy/observation)
│    └─< TREATMENT_COMMENT (소견)
│
└─< CONSULTATION_REQUEST (협진 - 별도 테이블)
     ├─ request_id, request_index
     ├─ consult_department
     └─< CONSULTATION_COMMENT (소견)
```

### 7.3 주요 API 엔드포인트

```
# OCS 관리
GET    /api/ocs/                              # OCS 목록
POST   /api/ocs/                              # OCS 생성
GET    /api/ocs/{request_id}/                 # OCS 상세
PATCH  /api/ocs/{request_id}/status/          # OCS 상태 변경
POST   /api/ocs/{request_id}/close/           # OCS 종료

# RIS_REQUEST
GET    /api/ocs/{request_id}/ris/             # RIS 요청 목록
POST   /api/ocs/{request_id}/ris/             # RIS 요청 추가
PATCH  /api/ocs/{request_id}/ris/{index}/     # RIS 요청 수정

# LIS_REQUEST
GET    /api/ocs/{request_id}/lis/             # LIS 요청 목록
POST   /api/ocs/{request_id}/lis/             # LIS 요청 추가
PATCH  /api/ocs/{request_id}/lis/{index}/     # LIS 요청 수정
POST   /api/ocs/{request_id}/lis/{index}/comments/  # LIS 소견 작성

# TREATMENT_REQUEST
GET    /api/ocs/{request_id}/treatment/       # 치료 요청 목록
POST   /api/ocs/{request_id}/treatment/       # 치료 요청 추가
POST   /api/ocs/{request_id}/treatment/{index}/comments/  # 치료 소견

# CONSULTATION_REQUEST
GET    /api/ocs/{request_id}/consultation/    # 협진 요청 목록
POST   /api/ocs/{request_id}/consultation/    # 협진 요청 추가
POST   /api/ocs/{request_id}/consultation/{index}/comments/  # 협진 소견

# 워크리스트
GET    /api/ocs/worklist/ris/                 # RIS 워크리스트
GET    /api/ocs/worklist/lis/                 # LIS 워크리스트
GET    /api/ocs/worklist/treatment/           # 치료 워크리스트
GET    /api/ocs/worklist/consultation/        # 협진 워크리스트

# 통계
GET    /api/ocs/statistics/                   # OCS 통계
GET    /api/ocs/urgent/                       # 긴급 오더 목록
```

### 7.4 READY 상태 계산 규칙

```python
def calculate_ocs_status(ocs):
    """OCS 상태를 조건식으로 계산 (파생 상태)"""

    # 1. 필수 요청 중 FAILED/CANCELLED 존재 → BLOCKED
    failed_count = (
        ocs.ris_requests.filter(is_required=True, request_status__in=['FAILED', 'CANCELLED']).count() +
        ocs.lis_requests.filter(is_required=True, request_status__in=['FAILED', 'CANCELLED']).count() +
        ocs.treatment_requests.filter(is_required=True, request_status__in=['FAILED', 'CANCELLED']).count() +
        ocs.consultation_requests.filter(is_required=True, request_status__in=['FAILED', 'CANCELLED']).count()
    )
    if failed_count > 0:
        return 'BLOCKED'

    # 2. 모든 필수 요청이 COMPLETED → READY
    required_ris = ocs.ris_requests.filter(is_required=True)
    completed_ris = required_ris.filter(request_status='COMPLETED')
    # (LIS, Treatment, Consultation도 동일하게 확인)

    if all_required_completed:
        return 'READY'

    # 3. 그 외 → OPEN
    return 'OPEN'
```

### 7.5 저장소 분리

| 데이터 | 저장소 | 비고 |
|--------|--------|------|
| OCS/요청 메타데이터 | MySQL (Cloud SQL) | Django ORM |
| DICOM 영상 | Orthanc | RIS_REQUEST.dicom_study_uid |
| LIS 결과 파일 | GCP Cloud Storage | `gs://bucket/lis/result.csv` |
| 소견/코멘트 | MySQL | ImagingReport, LIS_COMMENT 등 |

### 7.6 소견(Comment) 관리 방식

| 요청 유형 | 소견 관리 방식 |
|----------|---------------|
| RIS_REQUEST | 기존 `imaging.ImagingReport` 사용 |
| LIS_REQUEST | `ocs.LIS_COMMENT` 테이블 |
| TREATMENT_REQUEST | `ocs.TREATMENT_COMMENT` 테이블 |
| CONSULTATION_REQUEST | `ocs.CONSULTATION_COMMENT` 테이블 |

### 7.7 기존 앱과의 통합

```python
# RIS_REQUEST와 ImagingStudy 연결
RIS_REQUEST:
  - imaging_study_id (FK to ImagingStudy, nullable)

# ai_inference 앱과의 연결 (별도 앱)
AI_REQUEST:
  - request_id (FK to OCS, nullable)
  - ris_request_id (FK to RIS_REQUEST, nullable)
```

**상세 설계**: [OCS–AI Inference Architecture Speci.md](../OCS–AI Inference Architecture Speci.md) 참조

---

## 8. 데이터베이스 설계

### 8.1 ERD 개념

```
User (기존)
  ├─── has many ──> Encounter (담당 의사)
  ├─── has many ──> ImagingStudy (오더 의사)
  ├─── has many ──> ImagingReport (판독의)
  ├─── has many ──> AIAnalysisJob (요청자)
  ├─── has many ──> AIAnalysisResult (검토자)
  ├─── has many ──> TreatmentPlan (계획 의사)
  └─── has many ──> Order (오더 의사)

Patient
  ├─── has many ──> Encounter
  ├─── has many ──> ImagingStudy
  ├─── has many ──> AIAnalysisJob
  ├─── has many ──> TreatmentPlan
  ├─── has many ──> FollowUp
  └─── has many ──> Order

Encounter
  ├─── has many ──> ImagingStudy
  ├─── has many ──> TreatmentPlan
  └─── has many ──> Order

Order (OCS)
  ├─── has many ──> OrderProgress
  ├─── has many ──> OrderComment
  ├─── has many ──> OrderAttachment
  ├─── belongs to ──> Patient
  ├─── belongs to ──> Encounter
  ├─── may reference ──> ImagingStudy (nullable)
  ├─── may reference ──> AIAnalysisJob (nullable)
  └─── may reference ──> TreatmentPlan (nullable)

ImagingStudy
  ├─── has one ──> ImagingReport
  ├─── has many ──> AIAnalysisJob
  ├─── belongs to ──> Encounter
  └─── may belong to ──> Order (nullable)

AIAnalysisJob
  ├─── has one ──> AIAnalysisResult
  ├─── belongs to ──> ImagingStudy
  └─── may belong to ──> Order (nullable)

TreatmentPlan
  ├─── has many ──> TreatmentSession
  ├─── has many ──> FollowUp
  ├─── belongs to ──> Patient
  ├─── belongs to ──> Encounter
  └─── may belong to ──> Order (nullable)

FollowUp
  ├─── belongs to ──> Patient
  ├─── belongs to ──> TreatmentPlan
  └─── may reference ──> ImagingStudy
```

### 8.2 MySQL 설정

```python
# config/dev.py 수정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'brain_tumor_cdss',
        'USER': 'cdss_user',
        'PASSWORD': 'cdss_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}
```

---

## 9. 프론트엔드 메뉴 구조

### 9.1 메뉴 계층

```
대시보드
  └─ 대시보드 홈 (통계, 최근 활동)

환자 관리
  ├─ 환자 목록
  ├─ 환자 등록
  └─ 환자 검색

진료 관리
  ├─ 진료 목록
  ├─ 진료 등록
  └─ 진료 달력

영상 검사
  ├─ 검사 목록
  ├─ 검사 오더 생성
  ├─ 판독 대기 목록
  └─ 판독문 작성

AI 분석
  ├─ AI 작업 목록
  ├─ AI 분석 요청
  ├─ 결과 검토 대기
  └─ AI 모델 관리

치료 관리
  ├─ 치료 계획 목록
  ├─ 치료 계획 수립
  └─ 치료 세션 기록

경과 추적
  ├─ 경과 목록
  ├─ 경과 등록
  └─ 환자별 경과 차트

오더 관리 (OCS)
  ├─ 전체 오더 목록
  ├─ 부서별 워크리스트
  ├─ 내 담당 오더
  └─ 긴급 오더

보고서
  ├─ 환자 통계
  ├─ AI 분석 통계
  └─ 치료 성과 분석
```

### 9.2 메뉴 권한 매핑

```json
[
  {
    "label": "환자 관리",
    "route": "/patients",
    "icon": "users",
    "permission": "view_patient",
    "roles": ["admin", "neurosurgeon", "neurologist", "radiologist", "nurse"]
  },
  {
    "label": "진료 관리",
    "route": "/encounters",
    "icon": "clipboard",
    "permission": "view_encounter",
    "roles": ["admin", "neurosurgeon", "neurologist", "nurse"]
  },
  {
    "label": "영상 검사",
    "route": "/imaging",
    "icon": "scan",
    "permission": "view_imaging_study",
    "roles": ["admin", "neurosurgeon", "neurologist", "radiologist", "radiologic_technologist"]
  },
  {
    "label": "AI 분석",
    "route": "/ai-analysis",
    "icon": "brain",
    "permission": "view_ai_job",
    "roles": ["admin", "neurosurgeon", "neurologist", "radiologist"]
  },
  {
    "label": "치료 관리",
    "route": "/treatment",
    "icon": "activity",
    "permission": "view_treatment_plan",
    "roles": ["admin", "neurosurgeon", "neurologist", "nurse"]
  },
  {
    "label": "경과 추적",
    "route": "/followup",
    "icon": "trending-up",
    "permission": "view_followup",
    "roles": ["admin", "neurosurgeon", "neurologist", "nurse"]
  },
  {
    "label": "오더 관리",
    "route": "/ocs",
    "icon": "clipboard-list",
    "permission": "view_order",
    "roles": ["admin", "neurosurgeon", "neurologist", "radiologist", "radiologic_technologist", "nurse"]
  }
]
```

---

## 10. 개발 단계별 계획

### Phase 1: 기본 환자/진료 관리 ✅ **완료 (2026-01-07)**
- [x] patients 앱 생성 및 모델 정의
- [x] encounters 앱 생성 및 모델 정의
- [x] 기본 CRUD API 구현
- [x] 권한 설정 → IsAuthenticated만 사용 (프론트엔드 라우터 관리)
- [x] 프론트엔드 기본 화면 (목록, 등록, 상세)
- [x] 더미 데이터 생성 스크립트 (환자 30명, 진료 20건)

### Phase 2: 영상 검사 관리 ✅ **완료 (2026-01-07)**
- [x] imaging 앱 생성 및 모델 정의
- [x] ImagingStudy, ImagingReport 모델 구현
- [x] 검사 이미지 메타데이터 API 구현
- [x] 판독문 작성/서명 API 구현
- [x] 프론트엔드 영상 검사 화면 5개 (목록/판독/조회/워크리스트/히스토리)
- [x] **OCS 없이 독립적으로 동작하는 기본 RIS 기능**
- [x] 판독 상태별 필터링, 환자별 히스토리 타임라인
- [x] 더미 데이터 생성 스크립트 (검사 30건, 판독문 20건)

### Phase 3: OCS 오더 통합 관리 ✅ **완료 (2026-01-08 ~ 2026-01-09)**

**설계 결정 (2026-01-08)**:
- 단일 테이블 설계 (OCS + OCSHistory)
- JSON 기반 worker_result로 job_role별 데이터 관리
- AI 추론 기능은 별도 `ai_inference` 앱으로 분리 예정

#### 백엔드 구현 ✅
- [x] ocs 앱 생성 및 모델 정의
  - [x] OCS (단일 테이블, job_role로 구분)
  - [x] OCSHistory (변경 이력)
- [x] OCS 상태 워크플로우 (ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED)
- [x] OCS 기본 CRUD API 구현
- [x] 상태 변경 API (accept, start, save_result, submit_result, confirm, cancel)
- [x] 워크리스트 API (job_role별 필터링)
- [x] WebSocket 실시간 알림 (상태 변경 시 관련 사용자에게 알림)
- [x] 더미 데이터 생성 스크립트 (RIS 30건, LIS 20건)
- [x] LIS 기능 강화 (GENETIC, PROTEIN 검사 유형 지원)

#### 프론트엔드 통합 ✅
- [x] 의사 오더 페이지 (DoctorOrderPage)
- [x] RIS 워크리스트 (RISWorklistPage) - OCS API 통합
- [x] RIS 상세/판독 페이지 (RISStudyDetailPage)
- [x] RIS 대시보드 (RISDashboardPage) - 통계 및 지연 알림
- [x] LIS 워크리스트 (LISWorklistPage)
- [x] LIS 상세/결과 입력 페이지 (LISStudyDetailPage)
- [x] LIS 처리 상태 페이지 (LISProcessStatusPage)
- [x] 간호사 접수 페이지 (NurseReceptionPage)
- [x] WebSocket 알림 토스트 (OCSNotificationToast)

#### AI 추론 앱 (별도 Phase로 분리)
- [ ] ai_inference 앱 생성 (Phase 4로 이동)
- [ ] AI_REQUEST, AI_JOB, AI_JOB_LOG 모델
- [ ] Redis Queue + Worker 기본 구현

### Phase 4: AI 분석 관리 ✅ **API 완료 (2026-01-11)**
- [x] ai_inference 앱 생성 및 모델 정의
- [x] AIModel, AIInferenceRequest, AIInferenceResult, AIInferenceLog 모델
- [x] AI 모델 목록/상세 API 구현
- [x] AI 추론 요청 생성/조회 API 구현
- [x] 데이터 검증 API 구현 (required_keys 확인)
- [x] 환자별 사용 가능 모델 조회 API
- [x] AI 결과 검토 API 구현
- [ ] 프론트엔드 AI 분석 화면 (진행 예정)
- [ ] Redis Queue + Worker (추후 구현)

### Phase 5: 치료 및 경과 관리 + OCS 고도화 ✅ **완료 (2026-01-09)**
- [x] treatment 앱 생성 및 모델 정의
- [x] followup 앱 생성 및 모델 정의
- [x] 치료 계획/세션 API 구현
- [x] 경과 추적 API 구현
- [ ] 프론트엔드 치료/경과 화면 (진행 예정)
- [ ] **OCS 첨부파일 기능 추가** (추후)
- [ ] **부서별 고급 워크리스트 필터 및 통계** (추후)
- [ ] **오더 타임라인 시각화 개선** (추후)

### Phase 6: 통합 및 최적화 (1주)
- [ ] 전체 워크플로우 통합 테스트 (OCS 포함)
- [ ] 실시간 알림 (WebSocket) 구현 - OCS 오더 상태 변경 알림
- [ ] 대시보드 통계 화면 구현 (OCS 통계 포함)
- [ ] 성능 최적화 (쿼리 최적화, 인덱싱)
- [ ] 문서화 및 배포 준비

### Phase 7: 외부 시스템 연동 준비 (추후)
- [ ] Redis 연동 (캐싱)
- [ ] Orthanc 연동 (DICOM 저장/조회)
- [ ] FastAPI AI Core 연동 (실제 AI 추론)
- [ ] OpenEMR 연동 (Database Router)
- [ ] FHIR 서버 연동 (표준 변환)

---

## 11. 품질 관리

### 11.1 코드 품질
- **Layered Architecture**: Controller → Service → Repository 분리
- **DRY 원칙**: 중복 코드 최소화
- **Type Hints**: Python 3.10+ 타입 힌트 사용
- **Docstrings**: 모든 함수/클래스에 설명 추가

### 11.2 데이터 검증
- **Serializer 검증**: 필수 필드, 타입, 형식 검증
- **Business Logic 검증**: Service Layer에서 비즈니스 규칙 검증
- **DB Constraints**: UNIQUE, CHECK, FK 제약 조건 설정

### 11.3 에러 핸들링
```python
# 표준 에러 응답 형식
{
  "error": {
    "code": "ERR_404",
    "message": "환자를 찾을 수 없습니다.",
    "detail": "Patient with ID=12345 not found",
    "field": "patient_id",
    "timestamp": "2026-01-07T10:30:00Z"
  }
}
```

### 11.4 감사 로그
- **모든 중요 작업 기록**: 환자 등록, 진단, 치료 계획, AI 분석 등
- **기존 audit 앱 활용**: AuditLog 모델 사용
- **로그 항목**: user, action, resource_type, resource_id, ip_address, details

---

## 12. 보안 고려사항

### 12.1 개인정보 보호
- **SSN 암호화**: 주민등록번호는 암호화하여 저장
- **접근 로그**: 모든 환자 정보 접근 기록
- **권한 기반 접근**: RBAC으로 최소 권한 원칙 적용

### 12.2 데이터 무결성
- **Soft Delete**: 실제 삭제 대신 상태 변경 (is_deleted=True)
- **Version Control**: 중요 데이터는 버전 관리
- **Audit Trail**: 모든 변경 이력 추적

### 12.3 API 보안
- **JWT 인증**: 기존 시스템의 JWT 토큰 사용
- **Rate Limiting**: API 호출 횟수 제한 (추후 구현)
- **Input Validation**: 모든 입력 데이터 검증

---

## 13. 향후 확장 계획

### 13.1 외부 시스템 연동
1. **Orthanc PACS**: DICOM 영상 저장 및 조회
2. **Redis**: 세션 캐싱 및 메시지 브로커
3. **FastAPI AI Core**: 실제 AI 모델 추론 서버
4. **OpenEMR**: 전자의무기록 연동
5. **HAPI FHIR**: HL7 FHIR 표준 변환

### 13.2 고급 기능
1. **OHIF Viewer**: 의료 영상 뷰어 통합
2. **3D Visualization**: 3D 종양 시각화
3. **Multi-Modal Fusion**: 여러 영상 검사 융합 분석
4. **Clinical Pathways**: 진료 프로토콜 자동화
5. **Predictive Analytics**: 예후 예측 모델

### 13.3 성능 최적화
1. **Query Optimization**: select_related, prefetch_related 활용
2. **Database Indexing**: 자주 조회하는 필드 인덱싱
3. **Caching Strategy**: Redis 캐싱 전략 수립
4. **Async Processing**: Celery 비동기 작업 처리

---

## 14. 참고 자료

### 14.1 기술 문서
- Django REST Framework: https://www.django-rest-framework.org/
- Django Channels: https://channels.readthedocs.io/
- MySQL 8.0 Reference: https://dev.mysql.com/doc/

### 14.2 의료 표준
- HL7 FHIR: https://www.hl7.org/fhir/
- DICOM Standard: https://www.dicomstandard.org/
- ICD-10 (질병분류): https://www.who.int/classifications/icd/

### 14.3 프로젝트 문서
- ONBOARDING_CORE_ARCHITECTURE.md: 전체 아키텍처 참고
- brain_tumor_dev README.md: 기존 시스템 구조

---

## 15. 결론

본 기획서는 brain_tumor_dev 프로젝트에 CDSS 핵심 기능을 추가하는 로드맵을 제시합니다.

**핵심 원칙**:
1. **점진적 개발**: Phase별로 단계적 구현
2. **기존 시스템 활용**: 인증/권한/감사 로그 재사용
3. **확장 가능성**: 외부 시스템 연동을 위한 인터페이스 설계
4. **품질 우선**: 코드 품질, 보안, 데이터 무결성 중시

**성공 기준**:
- [ ] 환자-진료-검사-AI-치료-경과-OCS 전체 워크플로우 동작
- [ ] OCS를 통한 부서 간 원활한 오더 통합 관리 및 협업
- [ ] 역할별 권한 기반 접근 제어
- [ ] 모든 중요 작업 감사 로그 기록
- [ ] API 문서화 (Swagger/OpenAPI)
- [ ] 단위 테스트 커버리지 80% 이상

이 기획서를 기반으로 개발을 진행하며, 각 Phase 완료 후 검토 및 피드백을 통해 지속적으로 개선해 나갑니다.

**OCS 통합으로 인한 주요 개선사항**:
- 모든 오더(영상검사, 검사실, 치료, AI 분석)를 단일 시스템에서 통합 관리
- 부서별 워크리스트 자동 생성으로 업무 효율성 향상
- 워크플로우 기반 진행 상태 관리로 투명성 확보
- 부서 간 실시간 코멘트 시스템으로 협업 강화










---


