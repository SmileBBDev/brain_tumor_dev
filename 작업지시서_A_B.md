# 작업 지시서 (개발자 A, B)

## 작업 개요

다음 3가지 작업을 분담하여 진행합니다.

---

## 1. [Backend - 개발자 A] worker_result에 series_id, series_type 필드 추가

### 배경
현재 `db_ocs.worker_result` JSON 필드에 `series_count`만 저장되고 있음.
DICOM 영상 업로드 시 Orthanc에서 개별 시리즈의 ID와 유형(T1, T2, T1C, FLAIR 등)을 읽어와 저장해야 함.

### 현재 구조 (OCS 모델)

**파일**: `brain_tumor_back/apps/ocs/models.py`

```python
# worker_result 기본 템플릿 (RIS)
"RIS": {
    "_template": "RIS",
    "_version": "1.0",
    "_confirmed": False,
    "dicom": {
        "study_uid": "",
        "series": [],           # <-- 여기에 시리즈 정보 배열
        "accession_number": "",
        "series_count": 0,
        "instance_count": 0
    },
    ...
}
```

### 수정 사항

#### 1.1 OCS 모델 템플릿 수정
**파일**: `brain_tumor_back/apps/ocs/models.py` (line 300-328)

`get_default_worker_result()` 메서드의 RIS 템플릿을 다음과 같이 수정:

```python
"RIS": {
    "_template": "RIS",
    "_version": "1.1",  # 버전 업
    "_confirmed": False,
    "dicom": {
        "study_uid": "",
        "series": [
            # 각 시리즈 항목 구조:
            # {
            #     "series_id": "",        # Orthanc Series ID (NEW)
            #     "series_uid": "",       # DICOM SeriesInstanceUID
            #     "series_type": "",      # T1, T2, T1C, FLAIR 등 (NEW)
            #     "modality": "",         # MR, CT 등
            #     "description": "",      # Series Description
            #     "instance_count": 0
            # }
        ],
        "accession_number": "",
        "series_count": 0,
        "instance_count": 0
    },
    ...
}
```

#### 1.2 Orthanc Proxy View 수정
**파일**: `brain_tumor_back/apps/orthancproxy/views.py`

DICOM 업로드 시 Orthanc API에서 시리즈 정보를 읽어올 때:
1. Series ID (Orthanc 내부 ID)
2. Series Type (SeriesDescription에서 T1, T2, T1C, FLAIR 등 파싱)

```python
# Orthanc API 호출로 시리즈 정보 가져오기
# GET /series/{series_id} 응답에서:
# - "ID" -> series_id
# - "MainDicomTags.SeriesDescription" -> series_type 파싱
# - "MainDicomTags.Modality" -> modality

def extract_series_type(description: str) -> str:
    """
    SeriesDescription에서 시리즈 유형 추출
    예: "T1_MPRAGE" -> "T1"
        "T2_FLAIR" -> "T2_FLAIR" 또는 "FLAIR"
        "T1C_POST" -> "T1C"
    """
    description_upper = description.upper()
    if "FLAIR" in description_upper:
        return "FLAIR"
    if "T1C" in description_upper or "T1_C" in description_upper or "POST" in description_upper:
        return "T1C"
    if "T2" in description_upper:
        return "T2"
    if "T1" in description_upper:
        return "T1"
    return "OTHER"
```

#### 1.3 업로드 완료 시 OCS worker_result 업데이트
업로드 완료 후 OCS 레코드의 `worker_result.dicom.series` 배열에 다음 정보 저장:

```python
series_info = {
    "series_id": orthanc_series_id,
    "series_uid": series_instance_uid,
    "series_type": extract_series_type(series_description),
    "modality": modality,
    "description": series_description,
    "instance_count": instances_count
}
```

---

## 2. [Backend - 개발자 A] db_ocs_attachments 용도 확인 및 doctor_request 저장 위치 확인

### 배경
- `attachments` 필드가 worker가 작성하는 용도인데 혼용되어 사용된 것 같음
- 작업자가 입력한 사항이 `doctor_request`에 입력되는지, 별도 테이블에 저장되는지 확인 필요

### 현재 구조 분석

**파일**: `brain_tumor_back/apps/ocs/models.py`

```python
# OCS 모델 필드
doctor_request = models.JSONField(...)   # 의사가 작성한 요청 내용
worker_result = models.JSONField(...)    # 작업자가 작성한 결과
attachments = models.JSONField(...)      # 첨부파일 정보
```

### 확인 사항

#### 2.1 doctor_request 용도 확인
- **의사 전용**: 의사가 오더 생성 시 작성하는 필드
- 포함 내용: `chief_complaint`, `clinical_info`, `request_detail`, `special_instruction`
- **작업자가 수정하면 안 됨**

#### 2.2 attachments 용도 확인
현재 템플릿 (`get_default_attachments()`):
```python
{
    "files": [],
    "zip_url": None,
    "total_size": 0,
    "last_modified": None,
    "external_source": {...},  # LIS 업로드 시 외부 기관 데이터
    "_custom": {}
}
```

**확인 필요**:
1. 의사가 오더 생성 시 첨부하는 파일 -> `doctor_request._custom` 또는 별도 필드?
2. 작업자가 결과 제출 시 첨부하는 파일 -> `attachments.files`
3. 혼용 여부 확인: `OCSCreateView`, `OCSUpdateView`, `save_result`, `submit_result` API에서 attachments 처리 로직 검토

#### 2.3 수정 방안 (필요 시)
만약 혼용되어 있다면:
- `doctor_attachments`: 의사가 오더 생성 시 첨부
- `worker_attachments`: 작업자가 결과 제출 시 첨부

또는 `attachments` 내부에 분리:
```python
{
    "doctor_files": [],   # 의사 첨부
    "worker_files": [],   # 작업자 첨부
    ...
}
```

---

## 3. [Frontend - 개발자 B] DICOM 영상 조회 페이지 Ellipsis 처리

### 배경
'DICOM 영상 조회' 페이지에서 기본 화면을 초과하는 데이터 표시 시 스크롤바 대신 말줄임표(...) 처리 필요.

### 수정 대상 파일

1. **PacsSelector.css**: `brain_tumor_front/src/components/PacsSelector.css`
2. **DicomViewerPopup.css**: `brain_tumor_front/src/components/DicomViewerPopup.css`

### 수정 사항

#### 3.1 PacsSelector.css 수정
이미 일부 적용되어 있음 (line 84-91, 126-143). 추가 확인 필요한 부분:

```css
/* select 옵션 텍스트 말줄임 (이미 적용 여부 확인) */
.select {
  height: 40px;
  /* ... 기존 스타일 ... */
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

/* select 내부 option 텍스트 - 브라우저 기본 동작 제한적 */
/* option 태그는 CSS 스타일링이 제한적이므로 대안 검토 */
```

#### 3.2 DicomViewerPopup.css 수정
**파일**: `brain_tumor_front/src/components/DicomViewerPopup.css`

```css
/* 시리즈 이름 말줄임 (이미 적용됨: line 332-337) */
.viewer-cell-header .series-name {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 추가 적용 필요 영역 확인 */
```

#### 3.3 PacsSelector.jsx 수정
**파일**: `brain_tumor_front/src/components/PacsSelector.jsx`

select option 텍스트가 길 경우 CSS로는 한계가 있으므로, JavaScript에서 텍스트 길이 제한:

```jsx
// 텍스트 truncate 함수
const truncate = (text, maxLen = 40) => {
  if (!text || text.length <= maxLen) return text;
  return text.substring(0, maxLen) + '...';
};

// option에 적용
<option key={p.orthancId} value={p.orthancId}>
  {truncate(asText(p.patientName || p.patientId))} ({p.studiesCount})
</option>
```

#### 3.4 전체 적용 CSS 규칙

```css
/* 공통 말줄임 클래스 */
.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 여러 줄 말줄임 (필요 시) */
.text-ellipsis-multiline {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

### 스크롤바 제거 확인 영역

1. **dicom-popup-left** (좌측 패널): `overflow-y: auto` -> 스크롤 유지 또는 제거 검토
2. **select 드롭다운**: 브라우저 기본 스크롤 - 제어 불가
3. **studyInfoBox** 내부 텍스트: 이미 ellipsis 적용됨

---

## 작업 분담 요약

| 작업 | 담당 | 우선순위 | 관련 파일 |
|------|------|----------|-----------|
| series_id, series_type 필드 추가 | A | 높음 | ocs/models.py, orthancproxy/views.py |
| attachments/doctor_request 용도 확인 | A | 중간 | ocs/views.py, ocs/serializers.py |
| DICOM 페이지 Ellipsis 처리 | B | 중간 | PacsSelector.css/jsx, DicomViewerPopup.css |

---

## 참고: 관련 타입 정의 (Frontend)

**파일**: `brain_tumor_front/src/types/ocs.ts`

```typescript
// RIS worker result - series 구조 업데이트 필요
export interface RISWorkerResult {
  // ...
  dicom: {
    study_uid: string;
    series: {
      series_id: string;      // NEW: Orthanc Series ID
      series_uid: string;
      series_type: string;    // NEW: T1, T2, T1C, FLAIR 등
      modality: string;
      description: string;
      instance_count: number;
    }[];
    accession_number: string;
  };
  // ...
}
```

---

## 완료 기준

1. **개발자 A**
   - [ ] worker_result.dicom.series에 series_id, series_type 저장 구현
   - [ ] Orthanc에서 시리즈 정보 읽어오는 로직 구현
   - [ ] attachments/doctor_request 용도 명확화 및 문서화

2. **개발자 B**
   - [ ] DICOM 페이지 모든 텍스트 영역 ellipsis 처리
   - [ ] 불필요한 스크롤바 제거 확인
   - [ ] 테스트: 긴 텍스트(50자 이상) 입력 시 말줄임 표시 확인
