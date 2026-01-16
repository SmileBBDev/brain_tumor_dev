# CDSS_STORAGE 경로 분석 보고서

**작성일**: 2026-01-16
**버전**: 1.0
**작성자**: AI Assistant

---

## 1. 개요

### 1.1 배경
CDSS_STORAGE는 Brain Tumor CDSS 시스템에서 LIS/RIS 검사 결과와 AI 추론 결과를 저장하는 핵심 저장소입니다. 현재 여러 프로그램(Django Backend, modAI, 더미 데이터 생성기)에서 이 저장소를 참조하고 있으나, 각 프로그램이 사용하는 상대경로가 일치하지 않아 문제가 발생하고 있습니다.

### 1.2 분석 범위
- Django Backend (brain_tumor_back)
- modAI 서버
- 더미 데이터 생성 스크립트 (setup_dummy_data)

---

## 2. 현재 경로 정의 현황

### 2.1 경로 정의 위치별 상세

#### A. Django Backend - settings.py
```python
# 파일: brain_tumor_back/config/settings.py (Line 256-262)
BASE_DIR = Path(__file__).resolve().parent.parent  # brain_tumor_back/

CDSS_STORAGE_ROOT = BASE_DIR / "CDSS_STORAGE"      # brain_tumor_back/CDSS_STORAGE/
CDSS_LIS_STORAGE = CDSS_STORAGE_ROOT / "LIS"       # brain_tumor_back/CDSS_STORAGE/LIS/
CDSS_RIS_STORAGE = CDSS_STORAGE_ROOT / "RIS"       # brain_tumor_back/CDSS_STORAGE/RIS/
```

**실제 경로**: `c:\0000\brain_tumor_dev\brain_tumor_back\CDSS_STORAGE\`

#### B. Django Backend - views.py
```python
# 파일: brain_tumor_back/apps/ai_inference/views.py (Line 28-32)
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent.parent  # brain_tumor_dev/

CDSS_STORAGE_BASE = _PROJECT_ROOT / "CDSS_STORAGE"         # brain_tumor_dev/CDSS_STORAGE/
CDSS_STORAGE_AI = CDSS_STORAGE_BASE / "AI"                 # brain_tumor_dev/CDSS_STORAGE/AI/
CDSS_STORAGE_LIS = CDSS_STORAGE_BASE / "LIS"               # brain_tumor_dev/CDSS_STORAGE/LIS/
```

**실제 경로**: `c:\0000\brain_tumor_dev\CDSS_STORAGE\`

#### C. modAI - config.py
```python
# 파일: modAI/config.py (Line 54-61)
BASE_DIR: Path = Path(__file__).parent  # modAI/

STORAGE_DIR: Path = Path(os.environ.get(
    "STORAGE_DIR",
    str(BASE_DIR.parent.parent / "CDSS_STORAGE" / "AI")  # ../../CDSS_STORAGE/AI
))
```

**실제 경로**: `c:\0000\CDSS_STORAGE\AI\` (brain_tumor_dev 상위)

#### D. 더미 데이터 생성기 - sync_lis_ocs.py
```python
# 파일: brain_tumor_back/setup_dummy_data/sync_lis_ocs.py (Line 50-51)
PATIENT_DATA_PATH = settings.PATIENT_DATA_ROOT
CDSS_STORAGE_PATH = settings.CDSS_LIS_STORAGE  # settings.py 참조
```

**실제 경로**: `c:\0000\brain_tumor_dev\brain_tumor_back\CDSS_STORAGE\LIS\`

---

## 3. 경로 불일치 분석

### 3.1 불일치 매트릭스

| 프로그램 | 참조 방식 | CDSS_STORAGE 경로 | AI 경로 | LIS 경로 |
|---------|----------|------------------|---------|----------|
| settings.py | BASE_DIR 기준 | `brain_tumor_back/CDSS_STORAGE/` | N/A | `brain_tumor_back/CDSS_STORAGE/LIS/` |
| views.py | 직접 계산 | `brain_tumor_dev/CDSS_STORAGE/` | `brain_tumor_dev/CDSS_STORAGE/AI/` | `brain_tumor_dev/CDSS_STORAGE/LIS/` |
| modAI | 직접 계산 | `CDSS_STORAGE/` (상위) | `CDSS_STORAGE/AI/` (상위) | N/A |
| sync_lis_ocs.py | settings 참조 | settings와 동일 | N/A | `brain_tumor_back/CDSS_STORAGE/LIS/` |

### 3.2 디렉토리 구조 시각화

```
c:\0000\
│
├── CDSS_STORAGE/                    ← [C] modAI가 출력하려는 위치
│   └── AI/
│
└── brain_tumor_dev/
    │
    ├── CDSS_STORAGE/                ← [B] views.py가 읽으려는 위치
    │   ├── AI/
    │   └── LIS/
    │
    ├── brain_tumor_back/
    │   │
    │   ├── CDSS_STORAGE/            ← [A,D] settings.py가 생성/참조하는 위치
    │   │   ├── LIS/
    │   │   └── RIS/
    │   │
    │   ├── config/
    │   │   └── settings.py
    │   │
    │   ├── apps/
    │   │   └── ai_inference/
    │   │       └── views.py
    │   │
    │   └── setup_dummy_data/
    │       └── sync_lis_ocs.py
    │
    └── modAI/
        └── config.py
```

### 3.3 데이터 흐름별 문제점

#### 문제 1: AI 추론 결과 저장/조회 불일치
```
modAI (출력) → c:\0000\CDSS_STORAGE\AI\{job_id}\
views.py (읽기) → c:\0000\brain_tumor_dev\CDSS_STORAGE\AI\{job_id}\

결과: 파일을 찾을 수 없음 (404 오류)
```

#### 문제 2: LIS 데이터 생성/조회 불일치
```
sync_lis_ocs.py (생성) → brain_tumor_back\CDSS_STORAGE\LIS\{ocs_id}\
views.py (읽기) → brain_tumor_dev\CDSS_STORAGE\LIS\{ocs_id}\

결과: MG 추론 시 CSV 파일을 찾을 수 없음
```

#### 문제 3: settings.py vs views.py 불일치
```
settings.py는 CDSS_STORAGE를 brain_tumor_back 내부에 정의
views.py는 settings를 참조하지 않고 직접 brain_tumor_dev 레벨로 계산

결과: 동일 Django 앱 내에서도 경로 불일치
```

---

## 4. 영향 분석

### 4.1 기능별 영향

| 기능 | 현재 상태 | 영향도 |
|------|----------|--------|
| 더미 LIS 데이터 생성 | 정상 작동 | - |
| M1 추론 결과 저장 | **경로 불일치** | 높음 |
| M1 추론 결과 조회 | **파일 없음** | 높음 |
| MG 추론 CSV 읽기 | **경로 불일치** | 높음 |
| MM 추론 feature 읽기 | **경로 불일치** | 높음 |
| 세그멘테이션 데이터 조회 | **파일 없음** | 높음 |

### 4.2 사용자 시나리오별 영향

1. **RIS 담당자가 M1 분석 요청**
   - modAI가 결과를 `c:\0000\CDSS_STORAGE\AI\`에 저장
   - Django가 `brain_tumor_dev\CDSS_STORAGE\AI\`에서 조회 시도
   - **결과**: 404 Not Found

2. **LIS 담당자가 MG 분석 요청**
   - 더미 데이터가 `brain_tumor_back\CDSS_STORAGE\LIS\`에 저장됨
   - views.py가 `brain_tumor_dev\CDSS_STORAGE\LIS\`에서 CSV 조회
   - **결과**: 파일 없음 오류

3. **의사가 MM 통합 분석 요청**
   - M1, MG feature 파일을 잘못된 경로에서 조회
   - **결과**: 전처리 feature 로드 실패

---

## 5. 수정 방안

### 5.1 권장 통일 경로 구조

```
brain_tumor_dev/
├── CDSS_STORAGE/           ← 단일 저장소 (모든 프로그램이 이 위치 사용)
│   ├── AI/                 ← AI 추론 결과 (modAI 출력, Django 읽기)
│   │   └── {job_id}/
│   │       ├── m1_classification.json
│   │       ├── m1_encoder_features.npz
│   │       ├── m1_segmentation.npz
│   │       ├── mg_gene_features.json
│   │       └── mm_result.json
│   │
│   ├── LIS/                ← LIS 검사 결과 (더미 생성, MG 추론 읽기)
│   │   └── {ocs_id}/
│   │       ├── gene_expression.csv
│   │       └── rppa.csv
│   │
│   └── RIS/                ← RIS 검사 결과 (더미 생성)
│       └── {ocs_id}/
│           └── dicom_info.json
│
├── brain_tumor_back/
├── modAI/
└── ...
```

### 5.2 수정 대상 파일

#### 수정 1: settings.py
```python
# 변경 전 (Line 256)
CDSS_STORAGE_ROOT = BASE_DIR / "CDSS_STORAGE"

# 변경 후
CDSS_STORAGE_ROOT = BASE_DIR.parent / "CDSS_STORAGE"  # brain_tumor_dev/CDSS_STORAGE/
```

**변경 이유**: CDSS_STORAGE를 brain_tumor_back 내부가 아닌 brain_tumor_dev 레벨에 통일

#### 수정 2: views.py
```python
# 변경 전 (Line 26-32)
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent.parent
CDSS_STORAGE_BASE = _PROJECT_ROOT / "CDSS_STORAGE"
CDSS_STORAGE_AI = CDSS_STORAGE_BASE / "AI"
CDSS_STORAGE_LIS = CDSS_STORAGE_BASE / "LIS"

# 변경 후
from django.conf import settings

CDSS_STORAGE_BASE = settings.CDSS_STORAGE_ROOT
CDSS_STORAGE_AI = CDSS_STORAGE_BASE / "AI"
CDSS_STORAGE_LIS = settings.CDSS_LIS_STORAGE
```

**변경 이유**: 직접 경로 계산 대신 settings.py의 설정값을 참조하여 일관성 확보

#### 수정 3: modAI/config.py
```python
# 변경 전 (Line 58-61)
STORAGE_DIR: Path = Path(os.environ.get(
    "STORAGE_DIR",
    str(BASE_DIR.parent.parent / "CDSS_STORAGE" / "AI")
))

# 변경 후
STORAGE_DIR: Path = Path(os.environ.get(
    "STORAGE_DIR",
    str(BASE_DIR.parent / "CDSS_STORAGE" / "AI")  # brain_tumor_dev/CDSS_STORAGE/AI
))
```

**변경 이유**: brain_tumor_dev 상위가 아닌 brain_tumor_dev 내부의 CDSS_STORAGE 참조

### 5.3 수정 우선순위

| 순서 | 파일 | 중요도 | 영향 범위 |
|------|------|--------|----------|
| 1 | settings.py | 높음 | 전체 Django 앱 |
| 2 | views.py | 높음 | AI 추론 API |
| 3 | modAI/config.py | 높음 | AI 결과 저장 |

---

## 6. 검증 체크리스트

### 6.1 수정 후 테스트 항목

- [ ] 더미 데이터 생성 (`python -m setup_dummy_data --sync`)
  - [ ] CDSS_STORAGE/LIS에 파일 생성 확인
  - [ ] CDSS_STORAGE/RIS에 파일 생성 확인

- [ ] M1 추론 테스트
  - [ ] modAI가 CDSS_STORAGE/AI/{job_id}/에 결과 저장 확인
  - [ ] Django가 동일 경로에서 결과 조회 확인
  - [ ] 세그멘테이션 API 정상 응답 확인

- [ ] MG 추론 테스트
  - [ ] views.py가 CDSS_STORAGE/LIS/{ocs_id}/gene_expression.csv 정상 읽기
  - [ ] MG 추론 결과 저장/조회 확인

- [ ] MM 추론 테스트
  - [ ] M1 encoder features 로드 확인
  - [ ] MG gene features 로드 확인
  - [ ] Protein CSV 로드 확인

### 6.2 경로 확인 명령어

```bash
# Django 설정 확인
python -c "
import os, sys
sys.path.insert(0, 'brain_tumor_back')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django; django.setup()
from django.conf import settings
print('CDSS_STORAGE_ROOT:', settings.CDSS_STORAGE_ROOT)
print('CDSS_LIS_STORAGE:', settings.CDSS_LIS_STORAGE)
print('CDSS_RIS_STORAGE:', settings.CDSS_RIS_STORAGE)
"

# modAI 설정 확인
python -c "
import sys; sys.path.insert(0, 'modAI')
from config import settings
print('STORAGE_DIR:', settings.STORAGE_DIR)
"
```

---

## 7. 결론

### 7.1 핵심 문제
- Django settings.py, views.py, modAI config.py가 각각 다른 CDSS_STORAGE 경로를 참조
- 이로 인해 AI 추론 결과 저장/조회, LIS 데이터 읽기에서 파일 경로 불일치 발생

### 7.2 해결 방안
- `brain_tumor_dev/CDSS_STORAGE/`를 단일 저장소로 통일
- settings.py에서 경로를 정의하고, 모든 Django 코드는 settings를 참조
- modAI는 환경변수 또는 기본값으로 동일 경로 참조

### 7.3 예상 효과
- AI 추론 결과 저장/조회 정상화
- LIS/RIS 데이터 접근 일관성 확보
- 향후 Docker 배포 시 환경변수로 유연하게 경로 설정 가능

---

## 부록 A: 관련 파일 목록

| 파일 경로 | 역할 |
|----------|------|
| `brain_tumor_back/config/settings.py` | Django 전역 설정 |
| `brain_tumor_back/apps/ai_inference/views.py` | AI 추론 API |
| `modAI/config.py` | modAI 서버 설정 |
| `brain_tumor_back/setup_dummy_data/sync_lis_ocs.py` | LIS 더미 데이터 생성 |
| `brain_tumor_back/setup_dummy_data/main.py` | 더미 데이터 통합 실행 |
| `modAI/services/m1_service.py` | M1 추론 결과 저장 |
| `modAI/services/mm_service.py` | MM 추론 결과 저장 |

## 부록 B: 환경변수 설정 (Docker 배포 시)

```yaml
# docker-compose.yml
services:
  django:
    environment:
      - CDSS_STORAGE_ROOT=/app/CDSS_STORAGE

  modai:
    environment:
      - STORAGE_DIR=/app/CDSS_STORAGE/AI
    volumes:
      - cdss_storage:/app/CDSS_STORAGE

volumes:
  cdss_storage:
```
