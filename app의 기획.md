# Brain Tumor CDSS 앱 기획서

## 프로젝트 개요

**작성일**: 2026-01-07
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

**⚠️ 중요**: Phase 2에서 기본 RIS 기능을 먼저 구현하고, Phase 3에서 **OCS(섹션 2.7)와 통합**됩니다.

**주요 기능**:
- 영상 검사 오더 생성 (CT, MRI, PET 등)
- 검사 상태 추적 (예약/검사중/완료/판독중/판독완료)
- 검사 이미지 메타데이터 저장 (실제 DICOM은 추후 Orthanc 연동)
- 판독 소견 작성 및 서명
- 검사 결과 조회
- RIS 워크리스트 제공 (Phase 3 이후 OCS 워크리스트로 통합)

**데이터 모델**:
```python
ImagingStudy:
  - id (PK)
  - encounter (FK to Encounter)
  - patient (FK to Patient)
  - order (FK to Order, nullable)  # OCS 통합
  - modality (검사 종류: CT/MRI/PET/X-RAY)
  - body_part (촬영 부위: brain)
  - status (상태: ordered/scheduled/in-progress/completed/reported)
  - ordered_by (FK to User, 오더 의사)
  - ordered_at (오더 일시)
  - scheduled_at (예약 일시)
  - performed_at (검사 일시)
  - radiologist (FK to User, 판독의)
  - study_uid (Study Instance UID, Orthanc 연동용)
  - series_count (시리즈 수)
  - instance_count (이미지 수)
  - created_at, updated_at

ImagingReport:
  - id (PK)
  - imaging_study (FK to ImagingStudy)
  - radiologist (FK to User)
  - findings (판독 소견, Text)
  - impression (판독 결론, Text)
  - tumor_detected (종양 발견 여부: Boolean)
  - tumor_location (종양 위치, JSON)
  - tumor_size (종양 크기, JSON: width/height/depth)
  - status (상태: draft/signed/amended)
  - signed_at (서명 일시)
  - created_at, updated_at
```

---

### 2.4 AI 분석 관리 (AI Analysis Management)
**목적**: AI 기반 뇌종양 분석 작업 관리

**주요 기능**:
- AI 분석 작업 생성 및 실행
- 분석 상태 추적 (대기/실행중/완료/실패)
- AI 분석 결과 저장 및 조회
- 의사의 AI 결과 검토 및 승인/거부
- 분석 결과 시각화 메타데이터 저장

**데이터 모델**:
```python
AIAnalysisJob:
  - id (PK)
  - imaging_study (FK to ImagingStudy)
  - patient (FK to Patient)
  - requested_by (FK to User)
  - model_type (모델 종류: tumor_detection/classification/segmentation)
  - model_version (모델 버전)
  - status (상태: pending/running/completed/failed/reviewed)
  - priority (우선순위: low/normal/high/urgent)
  - requested_at (요청 일시)
  - started_at (시작 일시)
  - completed_at (완료 일시)
  - error_message (에러 메시지)
  - created_at, updated_at

AIAnalysisResult:
  - id (PK)
  - analysis_job (FK to AIAnalysisJob)
  - tumor_detected (종양 검출 여부)
  - tumor_type (종양 유형: glioma/meningioma/pituitary/no_tumor)
  - confidence_score (신뢰도: 0.0~1.0)
  - tumor_location (종양 위치, JSON: x/y/z coordinates)
  - tumor_volume (종양 부피, mm³)
  - segmentation_mask_path (세그멘테이션 마스크 경로)
  - visualization_path (시각화 이미지 경로)
  - additional_findings (추가 소견, JSON)
  - reviewed_by (FK to User, 검토 의사)
  - review_status (검토 상태: pending/approved/rejected)
  - review_comment (검토 의견)
  - reviewed_at (검토 일시)
  - created_at, updated_at
```

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

**주요 기능**:
- 오더 통합 조회 (영상검사, 검사실, 치료, AI 분석 등)
- 부서별 오더 워크리스트 자동 생성
- 오더별 진행 상태 실시간 추적 (워크플로우 단계별)
- 부서 간 의견 교환 (코멘트 시스템)
- 오더 이력 관리 및 타임라인 시각화
- 긴급 오더 우선순위 관리

**데이터 모델**:
```python
Order:
  - id (PK)
  - order_number (오더번호, Unique, 자동 생성)
  - patient (FK to Patient)
  - encounter (FK to Encounter)
  - order_type (오더 유형: imaging/lab/treatment/ai_analysis)
  - order_category (세부 분류: CT/MRI/혈액검사/수술 등)
  - priority (우선순위: routine/urgent/stat)
  - status (상태: ordered/accepted/in-progress/completed/cancelled)
  - ordered_by (FK to User)
  - target_department (목표 부서)
  - clinical_info (임상 정보, Text)

  # 연결된 실제 오더 (Polymorphic)
  - imaging_study (FK to ImagingStudy, nullable)
  - treatment_plan (FK to TreatmentPlan, nullable)
  - ai_analysis_job (FK to AIAnalysisJob, nullable)

  - created_at, updated_at

OrderProgress:
  - id (PK)
  - order (FK to Order)
  - workflow_stage (워크플로우 단계: RIS/LIS/AI별 상이)
  - performed_by (FK to User)
  - timestamp (상태 변경 일시)
  - note (진행 메모)

OrderComment:
  - id (PK)
  - order (FK to Order)
  - comment_type (유형: question/answer/note/instruction)
  - content (내용)
  - author (FK to User)
  - parent_comment (FK to OrderComment, nullable, 답글)
  - is_read (읽음 여부)
  - created_at, updated_at
```

**워크플로우 예시**:
- **RIS**: ordered → scheduled → performing → performed → reading → reported
- **LIS**: ordered → collected → processing → analyzed → reported
- **AI**: ordered → queued → analyzing → analyzed → reviewing → reviewed
- **Treatment**: ordered → scheduled → preparing → performing → completed

**통합 특징**:
- 부서 간 실시간 협업 (의사-방사선사-검사실-AI)
- 워크플로우 기반 상태 관리 (숫자 진행률 대신 업무 단계)
- Polymorphic 연결로 하나의 Order가 여러 타입 오더와 연결
- 상세 내용은 [섹션 7. OCS 시스템](#7-오더-통합-관리-시스템-ocs---order-communication-system) 참조

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





### 3.2 Django 앱 구조

```
brain_tumor_back/
├── apps/
│   ├── accounts/          # 기존 인증/권한 (재사용)
│   ├── audit/             # 기존 감사 로그 (재사용)
│   ├── authorization/     # 기존 권한 (재사용)
│   ├── menus/             # 기존 메뉴 (재사용)
│   │
│   ├── patients/          # 신규: 환자 관리 [0107_12:28]
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── encounters/        # 신규: 진료 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── imaging/           # 신규: 영상 검사 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── ai_analysis/       # 신규: AI 분석 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── treatment/         # 신규: 치료 관리
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   ├── followup/          # 신규: 경과 추적
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   │
│   └── ocs/               # 신규: 오더 통합 관리 (Order Communication System)
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── views.py
│       ├── urls.py
│       └── tests.py
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

### 7.1 개요
**목적**: 모든 부서의 오더를 통합 관리하고 진행 상태 및 의견 공유

**핵심 개념**:
- OCS는 독립적인 Django 앱으로 구현
- 영상검사(RIS), 검사실(LIS), AI 분석, 치료 등 모든 오더를 통합 관리
- 부서 간 실시간 의견 교환 및 협업 지원
- 오더별 진행 상태를 워크플로우 단계로 추적

### 7.2 주요 기능
- 오더 통합 조회 (영상검사, 검사실, 치료 등)
- 부서별 오더 워크리스트
- 오더별 진행 상태 실시간 추적 (RIS/LIS/AI 분석 단계별)
- 부서 간 의견 교환 (텍스트 코멘트)
- 오더 이력 관리 및 타임라인

### 7.3 데이터 모델

```python
Order:
  - id (PK)
  - order_number (오더번호, Unique, 자동 생성: ORD-YYYYMMDD-NNNN)
  - patient (FK to Patient)
  - encounter (FK to Encounter)
  - order_type (오더 유형: imaging/lab/treatment/consultation/ai_analysis)
  - order_category (세부 분류: CT/MRI/PET/혈액검사/수술 등)
  - priority (우선순위: routine/urgent/stat)
  - status (상태: ordered/accepted/in-progress/completed/cancelled)
  - ordered_by (FK to User, 오더 의사)
  - ordered_at (오더 일시)
  - target_department (목표 부서: radiology/lab/surgery/neurology/ai)
  - scheduled_datetime (예약 일시)
  - completed_at (완료 일시)
  - clinical_info (임상 정보, Text)
  - special_instruction (특별 지시사항, Text)

  # 연결된 실제 오더 (Polymorphic 관계)
  - imaging_study (FK to ImagingStudy, nullable)
  - treatment_plan (FK to TreatmentPlan, nullable)
  - ai_analysis_job (FK to AIAnalysisJob, nullable)
  # 추후 확장: lab_order, consultation_order 등

  - created_at, updated_at
  - is_deleted (Soft Delete)

OrderProgress:
  - id (PK)
  - order (FK to Order)
  - workflow_stage (워크플로우 단계)
    # RIS: ordered → scheduled → performing → performed → reading → reported
    # LIS: ordered → collected → processing → analyzed → reported
    # AI: ordered → queued → analyzing → analyzed → reviewed
    # Treatment: ordered → scheduled → preparing → performing → completed
  - status_detail (상세 상태 설명, Text)
  - performed_by (FK to User, 수행자)
  - department (수행 부서)
  - timestamp (상태 변경 일시)
  - note (진행 메모, Text)
  - created_at

OrderComment:
  - id (PK)
  - order (FK to Order)
  - comment_type (코멘트 유형: question/answer/note/instruction/alert)
  - content (내용, Text)
  - author (FK to User, 작성자)
  - department (작성자 소속 부서)
  - parent_comment (FK to OrderComment, nullable, 답글 기능)
  - is_read (읽음 여부, Boolean)
  - is_important (중요 표시, Boolean)
  - created_at
  - updated_at

OrderAttachment:
  - id (PK)
  - order (FK to Order)
  - file_path (파일 경로)
  - file_name (파일명)
  - file_type (파일 유형: document/image/report)
  - uploaded_by (FK to User)
  - created_at
```

### 7.4 워크플로우 단계 정의

```python
# RIS (Radiology Information System) 워크플로우
RIS_WORKFLOW = [
    'ordered',       # 오더 생성
    'scheduled',     # 검사 예약
    'performing',    # 검사 수행 중
    'performed',     # 검사 완료
    'reading',       # 판독 중
    'reported',      # 판독 완료
]

# LIS (Laboratory Information System) 워크플로우
LIS_WORKFLOW = [
    'ordered',       # 오더 생성
    'collected',     # 검체 채취
    'processing',    # 검체 처리 중
    'analyzing',     # 분석 중
    'analyzed',      # 분석 완료
    'reported',      # 결과 보고
]

# AI Analysis 워크플로우
AI_WORKFLOW = [
    'ordered',       # AI 분석 요청
    'queued',        # 대기열 등록
    'analyzing',     # 분석 중
    'analyzed',      # 분석 완료
    'reviewing',     # 의사 검토 중
    'reviewed',      # 검토 완료
]

# Treatment 워크플로우
TREATMENT_WORKFLOW = [
    'ordered',       # 치료 계획 수립
    'scheduled',     # 치료 예약
    'preparing',     # 치료 준비
    'performing',    # 치료 수행 중
    'completed',     # 치료 완료
    'followup',      # 경과 관찰
]
```

### 7.5 주요 API 엔드포인트

```
# 오더 관리
GET    /api/ocs/orders/                      # 오더 목록 (필터: 부서, 상태, 우선순위, 날짜)
POST   /api/ocs/orders/                      # 오더 생성
GET    /api/ocs/orders/{id}/                 # 오더 상세
PATCH  /api/ocs/orders/{id}/status/          # 오더 상태 변경
DELETE /api/ocs/orders/{id}/                 # 오더 취소 (Soft Delete)

# 오더 진행 상태
GET    /api/ocs/orders/{id}/progress/        # 진행 상태 조회 (전체 타임라인)
POST   /api/ocs/orders/{id}/progress/        # 진행 상태 업데이트 (다음 단계로 이동)
GET    /api/ocs/orders/{id}/timeline/        # 오더 타임라인 (시각화용)
GET    /api/ocs/orders/{id}/current-stage/   # 현재 워크플로우 단계

# 오더 코멘트
GET    /api/ocs/orders/{id}/comments/        # 코멘트 목록
POST   /api/ocs/orders/{id}/comments/        # 코멘트 작성
PUT    /api/ocs/orders/{id}/comments/{cid}/  # 코멘트 수정
DELETE /api/ocs/orders/{id}/comments/{cid}/  # 코멘트 삭제
PATCH  /api/ocs/orders/{id}/comments/{cid}/read/  # 읽음 처리
GET    /api/ocs/orders/{id}/comments/unread/ # 안 읽은 코멘트 수

# 오더 첨부파일
GET    /api/ocs/orders/{id}/attachments/     # 첨부파일 목록
POST   /api/ocs/orders/{id}/attachments/     # 첨부파일 업로드
DELETE /api/ocs/orders/{id}/attachments/{aid}/ # 첨부파일 삭제

# 부서별 워크리스트
GET    /api/ocs/worklist/radiology/          # 영상의학과 워크리스트
GET    /api/ocs/worklist/lab/                # 검사실 워크리스트
GET    /api/ocs/worklist/surgery/            # 수술실 워크리스트
GET    /api/ocs/worklist/ai/                 # AI 분석 워크리스트
GET    /api/ocs/worklist/my-tasks/           # 내 담당 오더 목록
GET    /api/ocs/worklist/{dept}/pending/     # 부서별 대기 오더

# 통계 및 대시보드
GET    /api/ocs/statistics/                  # 전체 오더 통계
GET    /api/ocs/statistics/department/       # 부서별 통계
GET    /api/ocs/statistics/turnaround-time/  # TAT (소요 시간) 통계
GET    /api/ocs/pending-orders/              # 대기 중인 오더
GET    /api/ocs/urgent-orders/               # 긴급 오더 목록
```

### 7.6 워크플로우 예시 (영상검사 오더)

```
1. 의사가 영상검사 오더 생성
   POST /api/ocs/orders/
   {
     "order_type": "imaging",
     "order_category": "MRI",
     "target_department": "radiology",
     "priority": "routine",
     "clinical_info": "두통, 구토 증상. 뇌종양 의심"
   }
   → Order 생성, ImagingStudy 자동 연결
   → OrderProgress: workflow_stage = "ordered"
   ↓

2. 영상의학과에서 오더 확인 및 수락
   PATCH /api/ocs/orders/{id}/status/
   {"status": "accepted"}
   ↓

3. 방사선사가 검사 예약
   POST /api/ocs/orders/{id}/progress/
   {
     "workflow_stage": "scheduled",
     "note": "검사 예약 완료: 2026-01-08 14:00"
   }
   ↓

4. 방사선사가 질문 코멘트
   POST /api/ocs/orders/{id}/comments/
   {
     "comment_type": "question",
     "content": "조영제 사용 가능한가요? 신기능 검사 결과 필요합니다.",
     "is_important": true
   }
   ↓

5. 의사가 답변
   POST /api/ocs/orders/{id}/comments/
   {
     "comment_type": "answer",
     "parent_comment": {comment_id},
     "content": "네, 조영제 사용 가능합니다. 신기능 정상입니다."
   }
   ↓

6. 검사 수행 시작
   POST /api/ocs/orders/{id}/progress/
   {
     "workflow_stage": "performing",
     "note": "검사 시작"
   }
   ↓

7. 검사 완료
   POST /api/ocs/orders/{id}/progress/
   {
     "workflow_stage": "performed",
     "note": "검사 완료. DICOM 영상 320장 전송 완료"
   }
   ↓

8. 판독의 판독 시작
   POST /api/ocs/orders/{id}/progress/
   {
     "workflow_stage": "reading",
     "performed_by": {radiologist_id}
   }
   ↓

9. 판독 완료 및 보고
   POST /api/ocs/orders/{id}/progress/
   {
     "workflow_stage": "reported",
     "note": "판독 완료. 좌측 측두엽 종양 의심 소견"
   }

   PATCH /api/ocs/orders/{id}/status/
   {"status": "completed"}
```

### 7.7 통합 특징

1. **부서 간 협업**: 의사-방사선사-검사실-AI 시스템 간 실시간 의견 교환
2. **진행 상태 투명성**: 환자와 의료진 모두 오더 진행 상태 확인 가능
3. **우선순위 관리**: STAT(응급), Urgent(긴급), Routine(일반) 오더 구분
4. **통합 워크리스트**: 각 부서별 업무 목록 자동 생성
5. **이력 추적**: 모든 오더 변경 사항 타임라인으로 기록
6. **워크플로우 기반**: 숫자 진행률이 아닌 업무 단계별 상태 관리
7. **Polymorphic 연결**: 하나의 Order가 여러 타입의 실제 오더와 연결

### 7.8 기존 앱과의 통합

```python
# ImagingStudy와 Order 연결
ImagingStudy:
  - order (FK to Order, nullable)  # 추가 필드

# AIAnalysisJob과 Order 연결
AIAnalysisJob:
  - order (FK to Order, nullable)  # 추가 필드

# TreatmentPlan과 Order 연결
TreatmentPlan:
  - order (FK to Order, nullable)  # 추가 필드
```

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

### Phase 1: 기본 환자/진료 관리 (1주)
- [ ] patients 앱 생성 및 모델 정의
- [ ] encounters 앱 생성 및 모델 정의
- [ ] 기본 CRUD API 구현
- [ ] 권한 설정 및 테스트
- [ ] 프론트엔드 기본 화면 (목록, 등록, 상세)

### Phase 2: 영상 검사 관리 (1주)
- [ ] imaging 앱 생성 및 모델 정의
- [ ] ImagingStudy, ImagingReport 모델 구현
- [ ] 검사 이미지 메타데이터 API 구현
- [ ] 판독문 작성/서명 API 구현
- [ ] 프론트엔드 영상 검사 화면 (IMAGE_VIEWER)
- [ ] **OCS 없이 독립적으로 동작하는 기본 RIS 기능**

### Phase 3: OCS 오더 통합 관리 (1주)
**⚠️ 중요: imaging 앱이 먼저 구현되어야 실제 통합 테스트 가능**
- [ ] ocs 앱 생성 및 모델 정의 (Order, OrderProgress, OrderComment, OrderAttachment)
- [ ] 워크플로우 정의 및 상수 설정 (RIS/LIS/AI/Treatment)
- [ ] **ImagingStudy와 Order 연결 (기존 imaging에 통합)**
- [ ] 오더 생성/조회 기본 API 구현
- [ ] 오더 진행 상태 업데이트 API 구현
- [ ] 오더 코멘트 API 구현 (첨부파일은 Phase 5로 연기)
- [ ] 프론트엔드 `/orders` 화면 연동 (OrderListPage, OrderCreate)
- [ ] RIS 워크리스트 화면 연동 (OCS API 활용)
- [ ] 기본 워크리스트 API (부서별 필터링)

### Phase 4: AI 분석 관리 (1주)
- [ ] ai_analysis 앱 생성 및 모델 정의
- [ ] **AIAnalysisJob과 Order 연결 (OCS 통합)**
- [ ] AI 작업 생성/조회 API 구현
- [ ] AI 결과 저장 API 구현 (Mock 데이터)
- [ ] AI 결과 검토 API 구현
- [ ] 프론트엔드 AI 분석 화면

### Phase 5: 치료 및 경과 관리 + OCS 고도화 (1주)
- [ ] treatment 앱 생성 및 모델 정의
- [ ] followup 앱 생성 및 모델 정의
- [ ] **TreatmentPlan과 Order 연결 (OCS 통합)**
- [ ] 치료 계획/세션 API 구현
- [ ] 경과 추적 API 구현
- [ ] 프론트엔드 치료/경과 화면
- [ ] **OCS 첨부파일 기능 추가**
- [ ] **부서별 고급 워크리스트 필터 및 통계**
- [ ] **오더 타임라인 시각화 개선**

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


