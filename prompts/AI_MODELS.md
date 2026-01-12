# AI 모델 정의 문서

> **최종 업데이트**: 2026-01-12

## 개요

Brain Tumor CDSS에서 사용하는 AI 추론 모델 정의입니다.

---

## 모델 목록

### M1: MRI 4-Channel Analysis

| 항목 | 내용 |
|------|------|
| **용도** | MRI 영상 기반 뇌종양 분석 |
| **입력 데이터** | T1, T2, T1C, FLAIR (4채널 MRI) |
| **OCS 소스** | RIS |
| **자동 트리거** | RIS 결과 제출 시 (RESULT_READY) |
| **출력** | 종양 위치, 크기, 등급 예측 |

**required_keys**:
```json
{
  "RIS": ["dicom.series", "dicom.study_uid"]
}
```

---

### MG: Genetic Analysis

| 항목 | 내용 |
|------|------|
| **용도** | 유전자 분석 기반 종양 특성 예측 |
| **입력 데이터** | RNA_seq, gene_mutations |
| **OCS 소스** | LIS (job_type: GENETIC) |
| **자동 트리거** | LIS GENETIC 결과 제출 시 (RESULT_READY) |
| **출력** | 유전자 마커 분석, 예후 예측 |

**required_keys**:
```json
{
  "LIS": ["RNA_seq", "gene_mutations"]
}
```

---

### MM: Multimodal Analysis

| 항목 | 내용 |
|------|------|
| **용도** | 영상 + 유전 + 단백질 통합 분석 |
| **입력 데이터** | MRI 영상 + RNA_seq + protein_markers |
| **OCS 소스** | RIS + LIS |
| **자동 트리거** | 없음 (수동 요청만) |
| **출력** | 종합 진단 결과, 치료 권고 |

**required_keys**:
```json
{
  "RIS": ["dicom.series"],
  "LIS": ["RNA_seq", "protein_markers"]
}
```

---

## 데이터 충족 조건

| 모델 | RIS (영상) | LIS (GENETIC) | LIS (PROTEIN) |
|------|------------|---------------|---------------|
| M1   | **필수**   | -             | -             |
| MG   | -          | **필수**      | -             |
| MM   | **필수**   | **필수**      | 선택          |

---

## 자동 추론 트리거 맵

```python
AUTO_TRIGGER_MAP = {
    ('RIS', None): 'M1',           # RIS 결과 → M1
    ('LIS', 'GENETIC'): 'MG',      # LIS GENETIC 결과 → MG
}
```

**트리거 시점**: `submit_result()` 호출 시 (RESULT_READY 상태)

---

## AIModel 테이블 초기 데이터

```json
[
  {
    "code": "M1",
    "name": "MRI 4-Channel Analysis",
    "description": "MRI 영상 기반 뇌종양 분석 (T1, T2, T1C, FLAIR)",
    "ocs_sources": ["RIS"],
    "required_keys": {"RIS": ["dicom.series", "dicom.study_uid"]},
    "is_active": true
  },
  {
    "code": "MG",
    "name": "Genetic Analysis",
    "description": "유전자 분석 기반 종양 특성 예측 (RNA_seq)",
    "ocs_sources": ["LIS"],
    "required_keys": {"LIS": ["RNA_seq", "gene_mutations"]},
    "is_active": true
  },
  {
    "code": "MM",
    "name": "Multimodal Analysis",
    "description": "영상 + 유전 + 단백질 통합 분석",
    "ocs_sources": ["RIS", "LIS"],
    "required_keys": {"RIS": ["dicom.series"], "LIS": ["RNA_seq", "protein_markers"]},
    "is_active": true
  }
]
```
