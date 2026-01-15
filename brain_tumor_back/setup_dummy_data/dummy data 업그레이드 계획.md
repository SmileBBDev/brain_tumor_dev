# Dummy Data 업그레이드 계획

## 개요

OCS worker_result 데이터 양식을 실제 운영 환경에 맞게 업그레이드합니다.

---

## 1. 현재 상태 분석

### 1.1 OCS 더미 데이터 위치

| 파일 | RIS | LIS | 설명 |
|------|-----|-----|------|
| `setup_dummy_data_2_clinical.py` | 30건 | 20건 | 기본 임상 데이터 |
| `setup_dummy_data_3_extended.py` | 100건 | 80건 | 확장 데이터 |

### 1.2 현재 worker_result 구조 (구버전)

#### RIS (구버전 - v1.0)
```json
{
  "_template": "RIS",
  "_version": "1.0",
  "_confirmed": false,
  "dicom": {
    "study_uid": "1.2.840.xxx",
    "series_count": 4,
    "instance_count": 100
  },
  "findings": "소견",
  "impression": "인상",
  "recommendation": "권고사항",
  "tumor": {
    "detected": true,
    "location": { "lobe": "frontal", "hemisphere": "left" },
    "size": { "max_diameter_cm": 2.5, "volume_cc": 10.5 }
  }
}
```

#### LIS (구버전)
```json
{
  "_template": "LIS",
  "_version": "1.0",
  "_confirmed": false,
  "test_type": "GENETIC",
  "gene_mutations": [...],
  "summary": "요약",
  "interpretation": "해석"
}
```

---

## 2. 업그레이드 목표 (실제 운영 데이터 기반)

### 2.1 RIS (MRI) - Orthanc 양식 v1.2

> **실제 운영 데이터 참조**: `ocs_0107` (OCS ID: 287)

**실제 운영 양식 (v1.2):**
```json
{
  "_template": "RIS",
  "_version": "1.2",
  "_confirmed": true,
  "_verifiedAt": "2026-01-15T05:47:22.707Z",
  "_verifiedBy": "시스템관리자",

  "orthanc": {
    "patient_id": "P202600032",
    "orthanc_study_id": "d33631a2-826ce14a-51d08259-121d1f00-6fd93174",
    "study_id": "848757b7-624f-43f1-b4c7-ada2960ca43c",
    "study_uid": "OCS_287_P202600032_20260115054433",
    "uploaded_at": "2026-01-15T05:44:46.328Z",
    "series": [
      {
        "orthanc_id": "136db762-6e5d2dc4-d4d3c598-c992042a-4e36dfab",
        "series_uid": "1.2.826.0.1.3680043.8.498.41777472177878251332292215283471445171",
        "series_type": "T1",
        "description": "t1",
        "instances_count": 155
      },
      {
        "orthanc_id": "dd28aa23-94315d7b-385aa0cb-c6a50e85-ced608f1",
        "series_uid": "1.2.826.0.1.3680043.8.498.69991311131513955503526758382311553092",
        "series_type": "T2",
        "description": "t2",
        "instances_count": 155
      },
      {
        "orthanc_id": "50f83d61-3efff3be-46ad51e6-0865e15c-41b602b5",
        "series_uid": "1.2.826.0.1.3680043.8.498.81182699929160760860147875400096852629",
        "series_type": "T1C",
        "description": "t1ce",
        "instances_count": 155
      },
      {
        "orthanc_id": "d54fb82b-e91c8691-a8396f8c-954f2488-3dd59d27",
        "series_uid": "1.2.826.0.1.3680043.8.498.97262784403330516932600850967100145800",
        "series_type": "FLAIR",
        "description": "flair",
        "instances_count": 155
      },
      {
        "orthanc_id": "25098b5d-325e1000-92091bfd-e3dac0a5-efcdeaa0",
        "series_uid": "1.2.826.0.1.3680043.8.498.43163004205864498006728837409232576791",
        "series_type": "SEG",
        "description": "seg",
        "instances_count": 155
      }
    ]
  },

  "dicom": {
    "study_uid": "OCS_287_P202600032_20260115054433",
    "series_count": 5,
    "instance_count": 775
  },

  "findings": "brain_tumor_ 너무 큽니다.",
  "impression": "brain_tumor _ 있습니다.",
  "recommendation": "brain_tumor 절제술 시급",

  "tumorDetected": true,
  "imageResults": [],
  "files": [],
  "_custom": {}
}
```

**주요 필드 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `_template` | string | "RIS" 고정 |
| `_version` | string | "1.2" |
| `_confirmed` | boolean | 확정 여부 |
| `_verifiedAt` | ISO datetime | 확정 일시 |
| `_verifiedBy` | string | 확정자 이름 |
| `orthanc` | object | Orthanc PACS 연동 정보 |
| `orthanc.patient_id` | string | 환자번호 (P202600032) |
| `orthanc.orthanc_study_id` | string | Orthanc 내부 Study ID |
| `orthanc.study_id` | string | DICOM Study ID (UUID) |
| `orthanc.study_uid` | string | StudyInstanceUID |
| `orthanc.series` | array | 시리즈 배열 (T1, T2, T1C, FLAIR, SEG) |
| `orthanc.uploaded_at` | ISO datetime | 업로드 일시 |
| `dicom` | object | DICOM 요약 정보 |
| `findings` | string | 소견 |
| `impression` | string | 인상 |
| `recommendation` | string | 권고사항 |
| `tumorDetected` | boolean | 종양 검출 여부 |
| `imageResults` | array | 검사 결과 항목 |
| `files` | array | 첨부 파일 |
| `_custom` | object | 사용자 정의 필드 |

**Series Types:**
- `T1`: T1 강조 영상
- `T2`: T2 강조 영상
- `T1C`: T1 조영증강 영상 (t1ce)
- `FLAIR`: FLAIR 영상
- `SEG`: Segmentation 마스크

---

### 2.2 LIS - RNA-seq 양식

**목표 양식:**
```json
{
  "_template": "LIS",
  "_version": "1.1",
  "_confirmed": true,
  "_verifiedAt": "2026-01-15T06:00:00.000Z",
  "_verifiedBy": "검사자명",

  "test_type": "GENETIC",

  "gene_mutations": [
    {
      "gene_name": "IDH1",
      "mutation_type": "R132H",
      "position": "chr2:209113112",
      "variant": "c.395G>A",
      "allele_frequency": 0.45,
      "clinical_significance": "pathogenic",
      "is_actionable": true
    },
    {
      "gene_name": "MGMT",
      "mutation_type": "Methylated",
      "position": "chr10:131265521",
      "variant": "promoter methylation",
      "clinical_significance": "likely_pathogenic",
      "is_actionable": true
    },
    {
      "gene_name": "TP53",
      "mutation_type": "Wild Type",
      "clinical_significance": "benign",
      "is_actionable": false
    },
    {
      "gene_name": "EGFR",
      "mutation_type": "Amplified",
      "clinical_significance": "pathogenic",
      "is_actionable": true
    }
  ],

  "RNA_seq": {
    "sample_id": "RNA_20260115_001",
    "quality_score": 95.5,
    "read_count": 50000000,
    "gene_expression": {
      "EGFR": 2.5,
      "VEGFA": 1.8,
      "TP53": 0.9,
      "IDH1": 1.2,
      "MGMT": 0.3
    },
    "raw_data_path": "/data/rna_seq/RNA_20260115_001.fastq"
  },

  "sequencing_data": {
    "method": "NGS",
    "coverage": 98.5,
    "quality_score": 95.5,
    "raw_data_path": "/data/sequencing/SEQ_20260115_001"
  },

  "summary": "IDH1 R132H 변이 양성, MGMT 프로모터 메틸화 양성",
  "interpretation": "WHO Grade 4 교모세포종 예후 양호 인자 확인. 테모졸로마이드 반응 예측 양호.",

  "test_results": [],
  "_custom": {}
}
```

**주요 변경사항:**
1. `gene_mutations` 필드 확장 (position, variant, allele_frequency, clinical_significance, is_actionable)
2. `RNA_seq` 필드 추가 (sample_id, quality_score, read_count, gene_expression, raw_data_path)
3. `sequencing_data` 필드 추가
4. `_verifiedAt`, `_verifiedBy` 필드 추가
5. `_version`: "1.1"

---

### 2.3 LIS - Protein (BIOMARKER) 양식

**목표 양식:**
```json
{
  "_template": "LIS",
  "_version": "1.1",
  "_confirmed": true,
  "_verifiedAt": "2026-01-15T07:00:00.000Z",
  "_verifiedBy": "검사자명",

  "test_type": "PROTEIN",

  "protein_markers": [
    {
      "marker_name": "GFAP",
      "value": "3.2",
      "unit": "ng/mL",
      "reference_range": "0-2.0",
      "interpretation": "상승",
      "is_abnormal": true
    },
    {
      "marker_name": "S100B",
      "value": "0.25",
      "unit": "ug/L",
      "reference_range": "0-0.15",
      "interpretation": "상승",
      "is_abnormal": true
    },
    {
      "marker_name": "NSE",
      "value": "18.5",
      "unit": "ng/mL",
      "reference_range": "0-15",
      "interpretation": "상승",
      "is_abnormal": true
    },
    {
      "marker_name": "Ki-67",
      "value": "25",
      "unit": "%",
      "reference_range": "0-10",
      "interpretation": "고증식",
      "is_abnormal": true
    },
    {
      "marker_name": "EGFR",
      "value": "양성",
      "unit": "-",
      "reference_range": "음성",
      "interpretation": "과발현",
      "is_abnormal": true
    }
  ],

  "protein": {
    "analysis_method": "Immunohistochemistry",
    "sample_type": "Tissue",
    "sample_id": "PRO_20260115_001",
    "quality_status": "Adequate"
  },

  "summary": "뇌종양 관련 바이오마커 다수 상승",
  "interpretation": "GFAP, S100B, NSE 상승으로 뇌손상/종양 활성 시사. Ki-67 25%로 고증식 종양 확인.",

  "test_results": [],
  "_custom": {}
}
```

**주요 변경사항:**
1. `protein_markers` 필드 확장 (interpretation 추가)
2. `protein` 필드 추가 (analysis_method, sample_type, sample_id, quality_status)
3. 뇌종양 특이 마커 추가 (Ki-67, EGFR)

---

## 3. 구현 계획

### 3.1 파일 수정 목록

| 파일 | 수정 내용 |
|------|----------|
| `setup_dummy_data_2_clinical.py` | RIS, LIS worker_result 템플릿 업데이트 |
| `setup_dummy_data_3_extended.py` | RIS, LIS worker_result 템플릿 업데이트 |
| `setup_dummy_data_1_base.py` | (필요시) AI 모델 데이터 타입 매칭 확인 |

### 3.2 RIS 더미 데이터 생성 로직 (실제 운영 양식 기반)

```python
def generate_ris_worker_result(ocs_id, patient_number, modality, is_confirmed=True):
    """
    RIS worker_result 생성 (Orthanc 양식 v1.2)

    실제 운영 데이터 참조: ocs_0107 (OCS ID: 287)
    - 5채널 MRI: T1, T2, T1C(t1ce), FLAIR, SEG
    - 각 시리즈당 155개 인스턴스 (총 775개)
    """
    import uuid
    from django.utils import timezone

    timestamp = timezone.now().isoformat() + "Z"
    study_uid = f"OCS_{ocs_id}_{patient_number}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

    # 5채널 MRI 시리즈 생성 (실제 운영 양식)
    series_configs = [
        ('T1', 't1'),
        ('T2', 't2'),
        ('T1C', 't1ce'),
        ('FLAIR', 'flair'),
        ('SEG', 'seg'),
    ]

    series = []
    total_instances = 0
    instances_per_series = random.randint(100, 200)  # 실제: 155

    for series_type, description in series_configs:
        # Orthanc 스타일 ID 생성
        orthanc_id = f"{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:12]}"
        series_uid = f"1.2.826.0.1.3680043.8.498.{random.randint(10000000000000000000, 99999999999999999999)}"

        series.append({
            "orthanc_id": orthanc_id,
            "series_uid": series_uid,
            "series_type": series_type,
            "description": description,
            "instances_count": instances_per_series
        })
        total_instances += instances_per_series

    tumor_detected = random.random() < 0.7  # 70% 확률로 종양 검출

    # Orthanc Study ID 생성 (실제: d33631a2-826ce14a-51d08259-121d1f00-6fd93174)
    orthanc_study_id = f"{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:12]}"

    return {
        "_template": "RIS",
        "_version": "1.2",
        "_confirmed": is_confirmed,
        "_verifiedAt": timestamp if is_confirmed else None,
        "_verifiedBy": "시스템관리자" if is_confirmed else None,

        "orthanc": {
            "patient_id": patient_number,
            "orthanc_study_id": orthanc_study_id,
            "study_id": str(uuid.uuid4()),
            "study_uid": study_uid,
            "uploaded_at": timestamp,
            "series": series
        } if modality == 'MRI' else None,

        "dicom": {
            "study_uid": study_uid,
            "series_count": len(series),
            "instance_count": total_instances
        },

        "findings": random.choice(FINDINGS_SAMPLES),
        "impression": random.choice(IMPRESSION_SAMPLES),
        "recommendation": random.choice(RECOMMENDATION_SAMPLES),

        "tumorDetected": tumor_detected,
        "imageResults": [],
        "files": [],
        "_custom": {}
    }


# 샘플 데이터
FINDINGS_SAMPLES = [
    "우측 전두엽에 3.2cm 크기의 종괴 관찰됨",
    "좌측 측두엽에 불규칙한 조영증강 병변 확인",
    "뇌실질 내 다발성 병변 소견",
    "T2 고신호 병변이 좌측 두정엽에서 관찰됨",
    "조영증강 MRI에서 환형 조영증강 패턴 확인",
]

IMPRESSION_SAMPLES = [
    "고등급 신경교종 의심",
    "뇌전이암 가능성 높음",
    "교모세포종(GBM) 시사",
    "저등급 신경교종 의심",
    "수막종 의심",
]

RECOMMENDATION_SAMPLES = [
    "조직검사 권고",
    "신경외과 협진 의뢰",
    "수술적 절제 고려",
    "3개월 후 추적 MRI 권고",
    "종양표지자 검사 시행 권고",
]
```

### 3.3 LIS (RNA-seq) 더미 데이터 생성 로직

```python
def generate_rna_seq_worker_result(is_confirmed=True):
    """RNA-seq worker_result 생성"""

    timestamp = timezone.now().isoformat()
    is_abnormal = random.random() < 0.3

    gene_mutations = [
        {
            "gene_name": "IDH1",
            "mutation_type": "R132H" if is_abnormal else "Wild Type",
            "position": "chr2:209113112" if is_abnormal else None,
            "variant": "c.395G>A" if is_abnormal else None,
            "allele_frequency": round(random.uniform(0.3, 0.5), 2) if is_abnormal else None,
            "clinical_significance": "pathogenic" if is_abnormal else "benign",
            "is_actionable": is_abnormal
        },
        {
            "gene_name": "MGMT",
            "mutation_type": random.choice(["Methylated", "Unmethylated"]),
            "position": "chr10:131265521",
            "variant": "promoter methylation",
            "clinical_significance": "likely_pathogenic" if random.random() > 0.5 else "uncertain",
            "is_actionable": True
        },
        # ... TP53, EGFR 등
    ]

    return {
        "_template": "LIS",
        "_version": "1.1",
        "_confirmed": is_confirmed,
        "_verifiedAt": timestamp if is_confirmed else None,
        "_verifiedBy": "검사자" if is_confirmed else None,

        "test_type": "GENETIC",

        "gene_mutations": gene_mutations,

        "RNA_seq": {
            "sample_id": f"RNA_{random.randint(10000, 99999)}",
            "quality_score": round(random.uniform(90, 99), 1),
            "read_count": random.randint(40000000, 60000000),
            "gene_expression": {
                "EGFR": round(random.uniform(0.5, 3.0), 1),
                "VEGFA": round(random.uniform(0.5, 2.5), 1),
                "TP53": round(random.uniform(0.5, 1.5), 1),
                "IDH1": round(random.uniform(0.5, 2.0), 1),
                "MGMT": round(random.uniform(0.1, 1.0), 1)
            },
            "raw_data_path": f"/data/rna_seq/RNA_{random.randint(10000, 99999)}.fastq"
        },

        "sequencing_data": {
            "method": "NGS",
            "coverage": round(random.uniform(95, 99), 1),
            "quality_score": round(random.uniform(90, 99), 1)
        },

        "summary": generate_genetic_summary(gene_mutations),
        "interpretation": generate_genetic_interpretation(gene_mutations),

        "test_results": [],
        "_custom": {}
    }
```

### 3.4 LIS (Protein) 더미 데이터 생성 로직

```python
def generate_protein_worker_result(is_confirmed=True):
    """Protein/BIOMARKER worker_result 생성"""

    timestamp = timezone.now().isoformat()

    protein_markers = [
        {
            "marker_name": "GFAP",
            "value": str(round(random.uniform(0.5, 5.0), 2)),
            "unit": "ng/mL",
            "reference_range": "0-2.0",
            "interpretation": "상승" if random.random() > 0.5 else "정상",
            "is_abnormal": random.random() > 0.5
        },
        {
            "marker_name": "S100B",
            "value": str(round(random.uniform(0.05, 0.5), 3)),
            "unit": "ug/L",
            "reference_range": "0-0.15",
            "interpretation": "상승" if random.random() > 0.5 else "정상",
            "is_abnormal": random.random() > 0.5
        },
        {
            "marker_name": "NSE",
            "value": str(round(random.uniform(5, 25), 1)),
            "unit": "ng/mL",
            "reference_range": "0-15",
            "interpretation": "상승" if random.random() > 0.5 else "정상",
            "is_abnormal": random.random() > 0.5
        },
        {
            "marker_name": "Ki-67",
            "value": str(random.randint(5, 40)),
            "unit": "%",
            "reference_range": "0-10",
            "interpretation": "고증식" if random.randint(5, 40) > 15 else "저증식",
            "is_abnormal": random.random() > 0.4
        }
    ]

    return {
        "_template": "LIS",
        "_version": "1.1",
        "_confirmed": is_confirmed,
        "_verifiedAt": timestamp if is_confirmed else None,
        "_verifiedBy": "검사자" if is_confirmed else None,

        "test_type": "PROTEIN",

        "protein_markers": protein_markers,

        "protein": {
            "analysis_method": "Immunohistochemistry",
            "sample_type": "Tissue",
            "sample_id": f"PRO_{random.randint(10000, 99999)}",
            "quality_status": "Adequate"
        },

        "summary": generate_protein_summary(protein_markers),
        "interpretation": generate_protein_interpretation(protein_markers),

        "test_results": [],
        "_custom": {}
    }
```

---

## 4. Orthanc 연동 관련

### 4.1 Orthanc 데이터 읽기 가능 여부

> **질문:** Orthanc에 있는 데이터를 읽고 더미 데이터를 만들 수 있는가?

**답변:** 가능합니다. 다음 방법으로 구현할 수 있습니다:

1. **Orthanc REST API 활용**
   - `GET /patients/` - 환자 목록
   - `GET /studies/?patient_id=xxx` - Study 목록
   - `GET /series/?study_id=xxx` - Series 목록

2. **더미 데이터 생성 시 Orthanc 연동**
   ```python
   import requests

   ORTHANC_URL = "http://localhost:8042"

   def get_orthanc_study_for_patient(patient_id):
       """환자 ID로 Orthanc Study 조회"""
       # 1. Orthanc에서 환자 검색
       patients = requests.get(f"{ORTHANC_URL}/patients").json()

       for pid in patients:
           patient = requests.get(f"{ORTHANC_URL}/patients/{pid}").json()
           if patient.get("MainDicomTags", {}).get("PatientID") == patient_id:
               # 2. Study 조회
               studies = patient.get("Studies", [])
               if studies:
                   study = requests.get(f"{ORTHANC_URL}/studies/{studies[0]}").json()
                   series_list = []

                   for sid in study.get("Series", []):
                       series = requests.get(f"{ORTHANC_URL}/series/{sid}").json()
                       tags = series.get("MainDicomTags", {})
                       series_list.append({
                           "orthanc_id": sid,
                           "series_uid": tags.get("SeriesInstanceUID"),
                           "series_type": _parse_series_type(tags.get("SeriesDescription", "")),
                           "description": tags.get("SeriesDescription"),
                           "instances_count": len(series.get("Instances", []))
                       })

                   return {
                       "orthanc_study_id": studies[0],
                       "study_uid": study.get("MainDicomTags", {}).get("StudyInstanceUID"),
                       "series": series_list
                   }

       return None
   ```

3. **하이브리드 방식**
   - Orthanc 서버가 실행 중이면: 실제 데이터 사용
   - Orthanc 서버가 없으면: 가상 데이터 생성

---

## 5. 작업 순서

### Phase 1: 템플릿 정의 (1단계)
- [ ] RIS worker_result v1.2 템플릿 확정
- [ ] LIS RNA-seq worker_result v1.1 템플릿 확정
- [ ] LIS Protein worker_result v1.1 템플릿 확정

### Phase 2: 헬퍼 함수 구현 (2단계)
- [ ] `generate_ris_worker_result()` 함수 구현
- [ ] `generate_rna_seq_worker_result()` 함수 구현
- [ ] `generate_protein_worker_result()` 함수 구현
- [ ] 샘플 데이터 (findings, impression 등) 확장

### Phase 3: 더미 데이터 스크립트 수정 (3단계)
- [ ] `setup_dummy_data_2_clinical.py` 수정
- [ ] `setup_dummy_data_3_extended.py` 수정
- [ ] 테스트 실행

### Phase 4: Orthanc 연동 (선택)
- [ ] Orthanc 서버 연동 로직 구현
- [ ] 실제 DICOM 데이터 기반 더미 생성

---

## 6. 예상 결과

업그레이드 후 더미 데이터:

| 항목 | Before | After |
|------|--------|-------|
| RIS _version | 1.0 | 1.2 |
| RIS orthanc 필드 | 없음 | 있음 (4채널 시리즈) |
| RIS tumorDetected | tumor.detected | tumorDetected (루트) |
| LIS RNA_seq | 기본 구조 | 확장 구조 (gene_expression 포함) |
| LIS protein | 기본 구조 | 확장 구조 (interpretation 포함) |

---

**작성일**: 2026-01-15
**작성자**: Claude
