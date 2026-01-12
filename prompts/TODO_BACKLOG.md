# Brain Tumor CDSS - 미완료 작업 백로그

> **최종 업데이트**: 2026-01-12
> **현재 상태**: Phase 4 완료, Phase 5 준비 중

---

## 최근 완료 작업 (2026-01-12)

### Process Status 기간 필터 추가 ✅
- [x] RIS/LIS ProcessStatusPage에 기간 필터 드롭다운 추가
- [x] 필터 옵션: 전체/1주일/1개월/6개월
- [x] 통계, 차트, 지연테이블 모두 필터 반영

### LIS 더미데이터 확장 ✅
- [x] LIS OCS 20건 → 30건 (+10개)
- [x] 날짜 분포: 0~180일 (6개월)
- [x] 상태별 타임스탬프 설정

### RIS/LIS Process Status 페이지 통일 ✅
- [x] RISDashboardPage → RISProcessStatusPage 리네이밍
- [x] 컬럼 용어 통일: 담당자→작업자, 처방의사→요청의사

---

## 1. 백엔드 작업 (A)

### 1.1 worker_result 필드 확장 (RIS)

**우선순위**: 높음

**작업 내용**:
- `apps/ocs/models.py`: RIS 템플릿에 series_id, series_type 추가
- `apps/orthancproxy/views.py`: Orthanc API에서 시리즈 정보 추출
- SeriesDescription에서 유형 파싱 (T1, T2, T1C, FLAIR)

### 1.2 AI 추론 자동 요청 시스템

**우선순위**: 중간

- RIS 확정 시 → M1 모델 자동 추론
- LIS 확정 시 → MG 모델 자동 추론

---

## 2. 프론트엔드 작업 (B)

### 2.1 DICOM 페이지 Ellipsis 처리

**우선순위**: 중간 / 부분 완료

- `PacsSelector.css`: select 옵션 텍스트 말줄임
- `PacsSelector.jsx`: 긴 텍스트 JavaScript 처리

### 2.2 AI 추론 수동 요청 버튼

**우선순위**: 중간

- `PatientDetailPage.tsx`: 'AI 추론 요청' 버튼 추가

---

## 3. Phase 5 계획 - 치료 및 경과 관리

### 백엔드
- [ ] `treatment` 앱: TreatmentPlan, TreatmentSession 모델
- [ ] `followup` 앱: FollowUp 모델

### 프론트엔드
- [ ] 치료 계획 목록/상세 페이지
- [ ] 경과 추적 페이지

---

## 4. 인프라 준비

- [ ] Orthanc PACS 서버 설치
- [ ] Redis + Celery 도입
- [ ] AI 추론 비동기 처리

---

## 참고

- AI 모델: M1 (MRI), MG (유전자), MM (멀티모달)
- 프로젝트 구조는 `PROJECT_DOCS.md` 참조
