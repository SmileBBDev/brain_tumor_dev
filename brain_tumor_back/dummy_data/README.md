# 더미 데이터 생성

## 빠른 시작 (Quick Start)

```bash
cd brain_tumor_back

# 1. 환자 데이터 (30명)
python manage.py shell -c "exec(open('dummy_data/create_dummy_patients.py', encoding='utf-8').read())"

# 2. 진료 데이터 (20건)
python manage.py shell -c "exec(open('dummy_data/create_dummy_encounters.py', encoding='utf-8').read())"

# 3. 영상 검사 데이터 (검사 30건, 판독문 20건)
python manage.py shell -c "from dummy_data.create_dummy_imaging import create_dummy_imaging_studies; create_dummy_imaging_studies(30, 20)"
```

> 중복 방지: 이미 데이터가 있으면 자동으로 스킵됩니다.

---

## 상세 정보

### 파일 목록
| 파일명 | 설명 |
|--------|------|
| `create_dummy_patients.py` | 환자 30명 생성 |
| `create_dummy_encounters.py` | 진료 20건 생성 |
| `create_dummy_imaging.py` | 영상검사/판독문 생성 |

### 실행 순서
환자 → 진료 → 영상 (외래키 관계 때문에 순서 중요)

### 필수 조건
- 최소 1명의 User 존재
- DOCTOR role 사용자 존재 (진료/영상 생성 시)

### 강제 추가 (중복 무시)
```python
python manage.py shell
>>> from dummy_data.create_dummy_encounters import create_dummy_encounters
>>> create_dummy_encounters(20, force=True)

>>> from dummy_data.create_dummy_imaging import create_dummy_imaging_studies
>>> create_dummy_imaging_studies(30, 20, force=True)
```

### 데이터 삭제
```python
python manage.py shell
>>> from apps.imaging.models import ImagingStudy, ImagingReport
>>> from apps.encounters.models import Encounter
>>> from apps.patients.models import Patient
>>> ImagingReport.objects.all().delete()
>>> ImagingStudy.objects.all().delete()
>>> Encounter.objects.all().delete()
>>> Patient.objects.all().delete()
```

## 트러블슈팅
- **"No active patients found"** → 환자 먼저 생성
- **"No doctors found"** → DOCTOR role 사용자 생성 필요
- **"ModuleNotFoundError"** → `brain_tumor_back` 디렉토리에서 실행
