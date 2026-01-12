# Brain Tumor CDSS - 미완료 작업 백로그

> **최종 업데이트**: 2026-01-12
> **현재 상태**: Phase 4 완료, Phase 5 준비 중

---

## 1. 백엔드 작업 (A)

### 1.1 worker_result 필드 확장 (RIS)

**우선순위**: 높음

**배경**: DICOM 영상 업로드 시 Orthanc에서 시리즈 정보를 읽어와 저장 필요

**작업 내용**:
- `apps/ocs/models.py`: RIS 템플릿에 series_id, series_type 추가
- `apps/orthancproxy/views.py`: Orthanc API에서 시리즈 정보 추출
- SeriesDescription에서 유형 파싱 (T1, T2, T1C, FLAIR)

**수정할 series 구조**:
```python
"series": [
    {
        "series_id": "",        # Orthanc Series ID
        "series_uid": "",       # DICOM SeriesInstanceUID
        "series_type": "",      # T1, T2, T1C, FLAIR 등
        "modality": "",
        "description": "",
        "instance_count": 0
    }
]
```

### 1.2 AI 추론 자동 요청 시스템

**우선순위**: 중간

**요구사항**:
- RIS 확정 시 → M1 (MRI) 모델 자동 추론 요청
- LIS 확정 시 → MG (Genetic) 모델 자동 추론 요청

**구현 위치**:
- `apps/ocs/signals.py`: OCS 확정 시 자동 트리거
- `apps/ai_inference/tasks.py`: Celery 비동기 태스크

### 1.3 attachments/doctor_request 용도 명확화

**우선순위**: 낮음

- `doctor_request`: 의사 전용 (오더 생성 시)
- `attachments`: 작업자 첨부파일
- 혼용 여부 확인 및 분리 필요 시 수정

---

## 2. 프론트엔드 작업 (B)

### 2.1 DICOM 페이지 Ellipsis 처리

**우선순위**: 중간
**상태**: 부분 완료

**확인 필요**:
- `PacsSelector.css`: select 옵션 텍스트 말줄임
- `DicomViewerPopup.css`: 시리즈 이름 말줄임 (완료)
- `PacsSelector.jsx`: 긴 텍스트 JavaScript 처리

### 2.2 AI 추론 수동 요청 버튼

**우선순위**: 중간

- `PatientDetailPage.tsx`: 'AI 추론 요청' 버튼 추가
- 클릭 시 `/ai/request?patientId={id}`로 이동

### 2.3 Dashboard AI 현황 패널

**우선순위**: 낮음

- `DoctorDashboard.tsx`: AIInferenceStatusPanel 추가
  - 최근 AI 추론 요청 상태
  - 대기/처리 중/완료 개수
  - 검토 필요한 결과 알림

---

## 3. Phase 5 계획 - 치료 및 경과 관리

### 백엔드
- [ ] `treatment` 앱: TreatmentPlan, TreatmentSession 모델
- [ ] `followup` 앱: FollowUp 모델
- [ ] OCS 연결 (job_role='TREATMENT')

### 프론트엔드
- [ ] 치료 계획 목록/상세 페이지
- [ ] 치료 세션 기록 페이지
- [ ] 경과 추적 페이지

---

## 4. 인프라 준비

### Orthanc PACS
- [ ] Orthanc 서버 설치
- [ ] DICOMweb 플러그인 설정
- [ ] Django 연동 클라이언트

### Redis + Worker
- [ ] Redis 서버 설정
- [ ] Celery 또는 Django-Q 도입
- [ ] AI 추론 비동기 처리

---

## 5. 메타데이터 기반 확장

### 환자별 영상 히스토리
- [ ] `PatientImagingHistoryPage.tsx`
- [ ] 날짜순 타임라인 뷰
- [ ] 동일 부위 이전 Study 비교

### 판독 리포트 연계
- [ ] Key Findings 키워드 강조
- [ ] Study ↔ Report 빠른 이동

---

## 참고

- AI 모델: M1 (MRI 4채널), MG (유전자), MM (멀티모달)
- OCS worker_result에서 AI 입력 데이터 추출
- 프로젝트 전체 구조는 `PROJECT_DOCS.md` 참조
