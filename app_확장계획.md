# Brain Tumor CDSS - 의료 영상 Viewer/Reading 확장 계획

**작성일**: 2026-01-07
**수정일**: 2026-01-08 (OCS 재설계 반영)
**현재 Phase**: Phase 2 완료, Phase 3 OCS 재설계 진행중

---

## 1. 현재 구현 상태 (Phase 2)

### 1.1 구현 완료된 기능
- ✅ **ImagingStudy 모델**: 영상 검사 메타데이터 관리
  - Modality (CT/MRI/PET/X-RAY), Body Part, Status 관리
  - Study UID, Series Count, Instance Count 저장
- ✅ **ImagingReport 모델**: 판독문 작성 및 서명
  - Findings, Impression, Tumor Detection
  - Tumor Location/Size (JSON 저장)
- ✅ **기본 CRUD API**: 검사 생성, 조회, 수정, 삭제
- ✅ **판독 워크플로우**: Draft → Signed 상태 관리
- ✅ **RIS 워크리스트**: 검사 대기 목록, 판독 대기 목록
- ✅ **프론트엔드**:
  - ImagingListPage (목록, 필터, 검색)
  - ImagingReportModal (판독문 작성/조회/서명)
  - ImagingWorklistPage (워크리스트)
  - RIS Dashboard (통계 카드)

### 1.2 현재 제한사항
- ❌ **DICOM 파일 저장 없음**: 메타데이터만 DB에 저장
- ❌ **실제 영상 뷰어 없음**: 영상을 볼 수 없음
- ❌ **Orthanc/PACS 연동 없음**: 외부 DICOM 서버 미연동
- ❌ **영상 조작 도구 없음**: Zoom, Pan, Window/Level 없음
- ❌ **Annotation 기능 없음**: ROI, Arrow, Text 등 없음
- ❌ **Series 단위 관리 없음**: Study만 관리, Series는 count만 저장
- ❌ **Instance 단위 관리 없음**: 개별 DICOM 파일 추적 불가

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

1. **Phase 3 OCS 재설계 완료**: 새로운 OCS 구조 구현
   - OCS, RIS_REQUEST, LIS_REQUEST, TREATMENT_REQUEST, CONSULTATION_REQUEST 모델
   - 각 요청별 COMMENT 테이블
   - READY 상태 파생 로직
2. **Phase 4 ai_inference 앱**: AI 추론 기능 별도 앱으로 구현
3. **Phase 2.5 구현**: 환자별 영상 히스토리 조회 페이지
4. **Orthanc PACS 준비**: Phase 4-5를 위한 서버 구축 계획

---

## 10. OCS 연동 계획 (Phase 3)

### 10.1 OCS와 Imaging 연동
**RIS_REQUEST ↔ ImagingStudy 연결**:
- RIS_REQUEST에 `imaging_study_id` FK 추가
- ImagingReport를 RIS_REQUEST의 소견으로 활용
- OCS에서 영상검사 오더 생성 시 ImagingStudy 자동 생성

### 10.2 워크플로우 연동
```
OCS 생성 → RIS_REQUEST 생성 → ImagingStudy 생성
    ↓
RIS_REQUEST 상태 변경 ← ImagingStudy 상태 변경
    ↓
ImagingReport 작성 시 RIS_REQUEST COMPLETED
    ↓
모든 필수 요청 완료 시 OCS READY
```

### 10.3 저장소 분리
| 데이터 | 저장소 | OCS 연동 |
|--------|--------|---------|
| DICOM 영상 | Orthanc | RIS_REQUEST.dicom_study_uid |
| 영상검사 소견 | MySQL | imaging.ImagingReport |
| LIS 결과 파일 | GCP Cloud Storage | LIS_REQUEST.result_file_uri |
| LIS 소견 | MySQL | ocs.LIS_COMMENT |

**상세 설계**: [OCS–AI Inference Architecture Speci.md](../OCS–AI Inference Architecture Speci.md) 참조

---

**작성자**: Claude
**문서 버전**: 1.1
**마지막 업데이트**: 2026-01-08
