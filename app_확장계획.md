# Brain Tumor CDSS - 의료 영상 Viewer/Reading 확장 계획

**작성일**: 2026-01-07
**수정일**: 2026-01-11
**현재 Phase**: Phase 3 OCS 통합 완료, Phase 4 AI 프론트엔드 준비중

---

## 1. 현재 구현 상태 (Phase 3 완료 - 2026-01-11)

### 1.1 백엔드 앱 구조 ✅
```
apps/
├── accounts/          # ✅ 인증/권한
├── audit/             # ✅ 감사 로그
├── authorization/     # ✅ 권한
├── menus/             # ✅ 메뉴
├── common/            # ✅ 공통 유틸
├── patients/          # ✅ 환자 관리
├── encounters/        # ✅ 진료 관리
├── ocs/               # ✅ OCS 오더 통합 관리
├── imaging/           # ✅ 영상 검사 관리 (OCS 통합)
├── ai_inference/      # ✅ AI 추론 관리 (API 완료)
├── treatment/         # ✅ 치료 관리
└── followup/          # ✅ 경과 추적
```

### 1.2 구현 완료된 기능
- ✅ **OCS 통합**: 단일 테이블 설계, job_role로 RIS/LIS/TREATMENT/CONSULT 구분
- ✅ **ImagingStudy**: OCS FK 연결, 메타데이터 관리
- ✅ **ImagingReport**: OCS.worker_result JSON으로 통합
- ✅ **AI Inference**: 3개 모델(M1/MG/MM), 추론 요청/결과/검토 API
- ✅ **LIS**: GENETIC, PROTEIN 포함 다양한 검사 유형 지원
- ✅ **Treatment/FollowUp**: 치료 계획 및 경과 추적

### 1.3 현재 데이터 현황
| 테이블 | 레코드 수 |
|--------|----------|
| OCS | 54건 (RIS 33건, LIS 21건) |
| OCSHistory | 8건 |
| ImagingStudy | 33건 |
| AIModel | 3건 (M1, MG, MM) |
| AIInferenceRequest | 10건 |
| AIInferenceResult | 1건 |

### 1.4 현재 제한사항
- ❌ **DICOM 파일 저장 없음**: 메타데이터만 DB에 저장
- ❌ **실제 영상 뷰어 없음**: 영상을 볼 수 없음
- ❌ **Orthanc/PACS 연동 없음**: 외부 DICOM 서버 미연동
- ❌ **영상 조작 도구 없음**: Zoom, Pan, Window/Level 없음
- ❌ **AI 추론 프론트엔드 없음**: API만 완료, UI 구현 필요
- ❌ **Redis Queue/Worker 없음**: AI 추론 비동기 처리 미구현

---

## 2. 요구사항 분석 및 분류

### 2.1 즉시 구현 가능 (Phase 2.5 - 현재 시스템 확장)

#### A. 환자별 영상 히스토리 조회
**난이도**: ⭐ (쉬움)
**소요 시간**: 1-2시간
**필요 작업**:
- 환자 ID로 ImagingStudy 필터링 API 추가
- 프론트엔드 PatientImagingHistory 컴포넌트 생성
- Study Date 기준 타임라인 뷰

**구현 방법**:
```python
# Backend API
GET /api/imaging/studies/?patient_id={id}&ordering=-study_date

# Frontend
PatientImagingHistoryPage.tsx
- 환자 정보 패널 (name, age, gender, patient_number)
- Study 목록 (날짜, Modality, Body Part, Status)
- 각 Study 클릭 시 상세 정보 표시
```

#### B. Study 메타데이터 계층 구조 표시
**난이도**: ⭐⭐ (중간)
**소요 시간**: 2-3시간
**필요 작업**:
- Study 상세 페이지에 트리 구조 추가
- Series/Instance 정보는 현재 count만 표시
- 추후 Orthanc 연동 시 실제 데이터로 대체

**구현 방법**:
```typescript
// Frontend Component
StudyDetailTree.tsx
├─ Patient Info
├─ Study Info
│   ├─ Study Date, Modality, Body Part
│   ├─ Series Count: {series_count}
│   └─ Instance Count: {instance_count}
└─ Report Info (if exists)
    ├─ Findings
    ├─ Impression
    └─ Tumor Detection
```

#### C. 판독 상태별 필터링 강화
**난이도**: ⭐ (쉬움)
**소요 시간**: 1시간
**필요 작업**:
- ImagingListPage 필터에 판독 상태 추가
- "미판독", "판독중", "판독완료" 탭 추가

**구현 방법**:
```typescript
// 현재 status 필터 외 report 상태 필터 추가
GET /api/imaging/studies/?has_report=false  // 미판독
GET /api/imaging/studies/?report_status=draft  // 판독중
GET /api/imaging/studies/?report_status=signed  // 판독완료
```

#### D. 판독 리포트 연계 강화
**난이도**: ⭐⭐ (중간)
**소요 시간**: 2시간
**필요 작업**:
- ImagingStudy 상세에서 Report로 빠른 이동
- Report에서 Study로 역참조
- Key Findings 강조 표시

**구현 방법**:
```typescript
// StudyDetailPage에 "판독문 보기" 버튼
// ReportModal에 "영상 보기" 버튼
// Findings에서 중요 키워드 하이라이트 (종양, 출혈, 부종 등)
```

---

### 2.2 단기 구현 가능 (Phase 3 - 기본 뷰어 추가)

#### A. 정적 영상 썸네일 표시
**난이도**: ⭐⭐⭐ (중간-높음)
**소요 시간**: 1-2일
**필요 작업**:
- ImagingStudy에 `thumbnail_path` 필드 추가
- 파일 업로드 API 추가 (단순 이미지 파일)
- Study 목록에 썸네일 표시

**제한사항**:
- DICOM 파일이 아닌 PNG/JPG 썸네일만 지원
- 실제 DICOM → PNG 변환은 Orthanc 연동 필요

#### B. Series 모델 추가 (메타데이터만)
**난이도**: ⭐⭐⭐ (중간-높음)
**소요 시간**: 1일
**필요 작업**:
- ImagingSeries 모델 생성
- Study와 OneToMany 관계 설정
- Series Description, Orientation, Slice Count 저장

**데이터 모델**:
```python
class ImagingSeries(models.Model):
    imaging_study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name='series')
    series_uid = models.CharField(max_length=255, unique=True)
    series_number = models.IntegerField()
    series_description = models.CharField(max_length=255, blank=True)
    modality = models.CharField(max_length=20)
    orientation = models.CharField(max_length=20)  # AX/SAG/COR
    slice_count = models.IntegerField(default=0)
    thumbnail_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### C. 기본 영상 뷰어 (이미지만)
**난이도**: ⭐⭐⭐⭐ (높음)
**소요 시간**: 2-3일
**필요 작업**:
- React 이미지 뷰어 라이브러리 사용 (react-image-viewer 등)
- 단순 이미지 로딩 및 표시
- 기본 Zoom/Pan 기능 (라이브러리 제공)

**제한사항**:
- DICOM 특화 기능 없음 (Window/Level 등)
- Slice 스크롤 없음 (단일 이미지만)
- Annotation 없음

---

### 2.3 중기 확장 필요 (Phase 4 - DICOM 기본 지원)

#### A. Orthanc PACS 연동
**난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**소요 시간**: 1-2주
**필요 사항**:
- Orthanc 서버 설치 및 설정
- DICOM C-STORE SCP 설정
- REST API 연동 (Study/Series/Instance 조회)
- WADO-URI를 통한 이미지 다운로드

**구현 방법**:
```python
# clients/orthanc_client.py
class OrthancClient:
    def get_study(self, study_uid):
        """Orthanc에서 Study 조회"""

    def get_series(self, series_uid):
        """Orthanc에서 Series 조회"""

    def get_instance_image(self, instance_uid, frame=0):
        """DICOM 이미지 PNG 변환하여 반환"""
```

#### B. DICOM Web Viewer (Cornerstone.js)
**난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**소요 시간**: 2-3주
**필요 사항**:
- Cornerstone.js / Cornerstone3D 통합
- DICOM 파일 파싱 및 렌더링
- Window/Level 조정
- 기본 Annotation (Line, ROI)

**라이브러리**:
- `cornerstone-core`: DICOM 렌더링 엔진
- `cornerstone-tools`: Annotation 도구
- `dicomParser`: DICOM 파일 파싱

**프론트엔드 구조**:
```
CornerstoneViewer/
├─ CornerstoneViewport.tsx  (DICOM 렌더링)
├─ ViewerToolbar.tsx         (Zoom, Pan, Window/Level 버튼)
├─ AnnotationTools.tsx       (Line, ROI, Arrow, Text)
└─ SeriesList.tsx            (Series 선택)
```

#### C. Series 스크롤 및 동기화
**난이도**: ⭐⭐⭐⭐ (높음)
**소요 시간**: 1주
**필요 작업**:
- Slice 단위 스크롤 구현
- 다중 Series 동기화 (동일 slice index)
- 이전 Study 비교 뷰

---

### 2.4 장기 확장 필요 (Phase 5+ - PACS 워크스테이션 수준)

#### A. OHIF Viewer 통합
**난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**소요 시간**: 1개월+
**설명**:
- OHIF (Open Health Imaging Foundation) Viewer는 오픈소스 의료 영상 뷰어
- PACS 수준의 모든 기능 제공 (MPR, 3D, Segmentation 등)
- DICOMweb 표준 지원

**필요 사항**:
- OHIF Viewer v3 설치 및 커스터마이징
- DICOMweb 서버 구축 (Orthanc + DICOMweb 플러그인)
- React 앱에 OHIF 임베딩

#### B. AI Overlay 및 Heatmap
**난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**소요 시간**: 1개월+
**필요 작업**:
- AI 분석 결과 (Segmentation Mask) 시각화
- Heatmap Overlay (병변 위치 표시)
- Confidence Score 표시

**데이터 흐름**:
```
AI Analysis → Segmentation Mask (NIfTI)
             ↓
         Convert to DICOM SEG
             ↓
      Store in Orthanc
             ↓
   Display in OHIF Viewer
```

#### C. Advanced Annotation
**난이도**: ⭐⭐⭐⭐ (높음)
**소요 시간**: 2-3주
**필요 기능**:
- ROI 측정 (면적, 부피)
- 3D ROI (Multi-slice)
- DICOM SR (Structured Report) 저장

#### D. Multi-Modality Fusion
**난이도**: ⭐⭐⭐⭐⭐ (매우 높음)
**소요 시간**: 2개월+
**설명**:
- CT + MRI 융합 표시
- PET/CT Fusion
- Image Registration 필요

---

## 3. 구현 우선순위 및 로드맵

### Phase 2.5: 메타데이터 기반 확장 (현재 → 1주 이내)
**즉시 구현 가능, DICOM 없이도 가능**

1. ✅ 환자별 영상 히스토리 조회 (1-2시간)
2. ✅ Study 메타데이터 트리 구조 (2-3시간)
3. ✅ 판독 상태별 필터링 강화 (1시간)
4. ✅ 판독 리포트 연계 강화 (2시간)

**총 소요 시간**: 약 6-8시간 (1일)

---

### Phase 3: 기본 뷰어 (1-2주)
**정적 이미지 기반, Orthanc 없이도 가능**

1. ⏳ 정적 썸네일 업로드 및 표시 (1-2일)
2. ⏳ ImagingSeries 모델 추가 (1일)
3. ⏳ React 이미지 뷰어 통합 (2-3일)
4. ⏳ 기본 Zoom/Pan 기능 (1일)

**총 소요 시간**: 약 5-7일

---

### Phase 4: DICOM 기본 지원 (2-4주)
**Orthanc PACS 연동 필수**

1. ⏳ Orthanc 서버 설치 및 설정 (2-3일)
2. ⏳ Orthanc REST API 연동 (3-4일)
3. ⏳ Cornerstone.js DICOM 뷰어 (1-2주)
4. ⏳ Window/Level, 기본 Annotation (3-5일)
5. ⏳ Series 스크롤 및 동기화 (1주)

**총 소요 시간**: 약 3-4주

---

### Phase 5+: PACS 워크스테이션 수준 (2-3개월)
**대규모 개발 필요**

1. ⏳ OHIF Viewer 통합 (1개월)
2. ⏳ AI Overlay 및 Heatmap (1개월)
3. ⏳ Advanced Annotation (2-3주)
4. ⏳ Multi-Modality Fusion (2개월)

**총 소요 시간**: 약 4-6개월

---

## 4. 현재 시스템에서 즉시 구현할 항목

### 4.1 구현 목표 (Phase 2.5)
**목표**: DICOM 없이도 의미 있는 영상 조회/판독 기능 제공

### 4.2 구현 항목

#### A. 환자 중심 영상 조회 페이지
**파일**: `PatientImagingHistoryPage.tsx`
**API**: `GET /api/imaging/studies/?patient_id={id}`

**기능**:
- 환자 기본 정보 패널
- Study 목록 (날짜순 정렬)
- Study별 상태 표시 (미판독/판독중/완료)
- 비교 기능 (동일 부위 이전 Study 매칭)

#### B. Study 상세 정보 페이지
**파일**: `StudyDetailPage.tsx`
**API**: `GET /api/imaging/studies/{id}/`

**기능**:
- Patient → Study → Report 계층 구조
- Series Count, Instance Count 표시
- 판독문 바로 보기/작성
- 이전 Study 비교 링크

#### C. 판독 리포트 연계
**파일**: `ImagingReportModal.tsx` (기존 확장)

**기능**:
- Key Findings 강조 (종양, 출혈, 부종 등 키워드)
- 영상 Study로 돌아가기 버튼
- 이전 판독과 비교 (동일 환자, 동일 부위)

#### D. 권한 기반 조회
**현재 구현됨**: RIS, DOCTOR, SYSTEMMANAGER 권한 체크

**확장**:
- DOCTOR: 원본 영상 메타데이터 + 판독문 전체
- RIS: 모든 정보 + 판독문 작성
- NURSE: 판독 결과 요약만

---

## 5. 제외 항목 (확장 계획으로 이관)

### 5.1 DICOM 파일 처리
**이유**: Orthanc PACS 서버 필요
**확장 시기**: Phase 4 (2-4주 소요)

### 5.2 실시간 영상 뷰어
**이유**: Cornerstone.js 또는 OHIF Viewer 통합 필요
**확장 시기**: Phase 4-5 (1-2개월 소요)

### 5.3 Annotation 도구
**이유**: DICOM 뷰어 필수
**확장 시기**: Phase 4-5

### 5.4 Window/Level 조정
**이유**: DICOM 렌더링 엔진 필요
**확장 시기**: Phase 4

### 5.5 Series 간 동기화
**이유**: Series 모델 및 DICOM 데이터 필요
**확장 시기**: Phase 4

### 5.6 AI Overlay
**이유**: AI 분석 결과 + DICOM Viewer 필요
**확장 시기**: Phase 5+ (AI Analysis 앱 완성 후)

### 5.7 Multi-Modality Fusion
**이유**: 고급 영상 처리 알고리즘 필요
**확장 시기**: Phase 5+

---

## 6. 기술 스택 및 의존성

### 6.1 현재 사용 가능 (Phase 2.5)
- ✅ Django REST Framework
- ✅ React + TypeScript
- ✅ MySQL
- ✅ 기존 ImagingStudy/ImagingReport 모델

### 6.2 Phase 3 추가 필요
- 📦 react-image-viewer (또는 react-viewer)
- 📦 multer (파일 업로드)

### 6.3 Phase 4 추가 필요
- 🔧 Orthanc PACS Server
- 🔧 Orthanc DICOMweb Plugin
- 📦 cornerstone-core
- 📦 cornerstone-tools
- 📦 dicomParser

### 6.4 Phase 5+ 추가 필요
- 🔧 OHIF Viewer v3
- 🔧 NVIDIA Clara (AI Inference)
- 📦 vtk.js (3D Visualization)
- 📦 itk.js (Image Processing)

---

## 7. 예상 비용 및 리소스

### 7.1 Phase 2.5 (즉시 구현)
- **개발 시간**: 1일
- **추가 비용**: $0
- **서버 요구사항**: 기존 Django 서버

### 7.2 Phase 3 (기본 뷰어)
- **개발 시간**: 1-2주
- **추가 비용**: $0 (오픈소스 라이브러리)
- **서버 요구사항**: 파일 저장소 추가 (10-100GB)

### 7.3 Phase 4 (DICOM 지원)
- **개발 시간**: 2-4주
- **추가 비용**: $0 (Orthanc 오픈소스)
- **서버 요구사항**:
  - Orthanc 서버 (별도 VM 권장)
  - DICOM 저장소 (100GB-1TB)

### 7.4 Phase 5+ (PACS 워크스테이션)
- **개발 시간**: 2-6개월
- **추가 비용**:
  - OHIF 커스터마이징: $0 (오픈소스)
  - GPU 서버 (AI Inference): $1,000-5,000/월
- **서버 요구사항**:
  - 고성능 GPU 서버 (NVIDIA A100 등)
  - 대용량 저장소 (1TB-10TB)

---

## 8. 결론

### 8.1 현재 즉시 구현 가능 항목 (Phase 2.5)
1. ✅ 환자별 영상 히스토리 조회
2. ✅ Study 메타데이터 계층 구조
3. ✅ 판독 상태별 필터링
4. ✅ 판독 리포트 연계

**소요 시간**: 약 1일
**추가 비용**: $0

### 8.2 확장 계획으로 이관 항목
- DICOM 파일 처리 (Phase 4)
- 실시간 영상 뷰어 (Phase 4-5)
- Annotation 도구 (Phase 4-5)
- AI Overlay (Phase 5+)
- Multi-Modality Fusion (Phase 5+)

### 8.3 권장 접근 방법
1. **Phase 2.5 먼저 구현**: 메타데이터 기반 기능으로 사용성 확보
2. **Phase 3 검토**: 정적 썸네일 필요 시 추가
3. **Phase 4 이후**: Orthanc PACS 서버 구축 후 본격적인 DICOM 지원
4. **Phase 5+**: 실제 임상 요구사항 확인 후 고급 기능 추가

---

## 9. 다음 단계

### 9.1 완료 (2026-01-11) ✅
1. **OCS 완료**
   - OCS 모델/Serializer/View 정상 동작
   - OCS API 엔드포인트 테스트 완료
   - 5개 마이그레이션 적용 완료
   - 54건 더미 데이터 (RIS 33건, LIS 21건)

2. **Imaging-OCS 통합 완료**
   - ImagingStudy-OCS FK 연결 정상 동작
   - OCS.worker_result JSON 매핑 완료
   - 33건 ImagingStudy 레코드

3. **AI Inference API 완료**
   - ai_inference 앱 생성 및 URL 등록
   - AIModel, AIInferenceRequest, AIInferenceResult, AIInferenceLog 모델
   - 모델 목록/상세, 추론 요청, 데이터 검증, 결과 검토 API
   - 환자별 사용 가능 모델 조회 API

4. **LIS 기능 완료**
   - GENETIC, PROTEIN 검사 유형 지원
   - gene_mutations, protein_markers, RNA_seq 필드

5. **Treatment/FollowUp 완료**
   - treatment, followup 앱 구현

### 9.2 단기 (Phase 4)
1. **AI 추론 프론트엔드**: 추론 요청/결과 검토 페이지
2. **권한 시스템 재활성화**: 메뉴별 권한 체크
3. **Orthanc PACS 준비**: Phase 4-5를 위한 서버 구축 계획

---

## 10. OCS 연동 계획 (Phase 3) - ✅ 구현 완료 (2026-01-09)

### 10.1 실제 구현된 구조 (단일 테이블 JSON 방식)
**OCS 단일 테이블 + ImagingStudy FK 연결**:
- OCS 테이블에 job_role 필드로 RIS/LIS/TREATMENT/CONSULT 구분
- ImagingStudy에 `ocs` FK 추가 (1:1 연결)
- ImagingReport 모델 삭제 → OCS.worker_result JSON으로 통합

### 10.2 현재 워크플로우 ✅
```
OCS 생성 (job_role='RIS') → ImagingStudy 생성 (ocs FK 연결)
    ↓
OCS 상태 변경 (ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED)
    ↓
판독 정보 저장 (OCS.worker_result JSON에 findings, impression, tumor 정보)
    ↓
판독 서명 시 OCS.worker_result._confirmed = true
```

### 10.3 데이터 저장 구조 ✅
| 데이터 | 저장소 | 필드/테이블 |
|--------|--------|---------|
| DICOM 메타데이터 | MySQL | imaging.ImagingStudy |
| 영상검사 오더 | MySQL | ocs.OCS (job_role='RIS') |
| 판독 소견 | MySQL | OCS.worker_result (JSON) |
| 종양 정보 | MySQL | OCS.worker_result.tumor (JSON) |
| 작업 노트 | MySQL | OCS.worker_result.work_notes (JSON array) |

### 10.4 ✅ 이슈 해결됨 (2026-01-09)
- OCS 모델/API 정상 동작
- 마이그레이션 적용 완료
- 더미 데이터 생성 완료 (RIS 30건, LIS 20건)
- LIS GENETIC/PROTEIN 검사 유형 지원 추가
- LIS/RIS 담당자 confirm 권한 추가

**상세 설계**: [OCS–AI Inference Architecture Speci.md](../OCS–AI Inference Architecture Speci.md) 참조

---

**작성자**: Claude
**문서 버전**: 1.3
**마지막 업데이트**: 2026-01-11
