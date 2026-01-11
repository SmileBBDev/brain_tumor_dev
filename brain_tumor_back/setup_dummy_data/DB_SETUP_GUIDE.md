# Brain Tumor CDSS - DB 설정 가이드

## 빠른 시작

```bash
cd brain_tumor_back

# 한 번에 모든 것 (DB 생성 + 마이그레이션 + 더미 데이터)
python -m setup_dummy_data
```

> DB가 없으면 자동 생성하고, 마이그레이션도 자동 실행합니다.

**리셋 후 재생성 (권장):**
```bash
python -m setup_dummy_data --reset
```

**끝!** 이제 서버를 실행하세요:
```bash
python manage.py runserver
```


===
python -m setup_dummy_data 실행 시 순서:
-m은 **패키지의 __main__.py**를 실행합니다.

1. main.py 실행 (통합 래퍼)
   │
   ├─► setup_dummy_data_1_base.py 호출
   │   │
   │   ├─ [0단계] DB 존재 확인 → 없으면 자동 생성
   │   ├─ [1단계] 마이그레이션 실행 (python manage.py migrate)
   │   ├─ [2단계] 역할 7개 생성
   │   ├─ [3단계] 슈퍼유저 생성 (system/system001)
   │   ├─ [4단계] 테스트 사용자 10명 생성
   │   ├─ [5단계] 메뉴/권한 시드 데이터
   │   ├─ [6단계] 환자 30명
   │   ├─ [7단계] 진료 20건
   │   ├─ [8단계] OCS(RIS) 30건 + ImagingStudy
   │   ├─ [9단계] OCS(LIS) 20건
   │   └─ [10단계] AI 모델 3개
   │
   └─► setup_dummy_data_2_add.py 호출
       │
       ├─ [1단계] 치료 계획 15건 + 세션
       ├─ [2단계] 경과 추적 25건
       └─ [3단계] AI 요청 10건

2. 최종 통계 출력
결론: 빈 DB에서 시작해도 모든 것이 자동으로 셋업됩니다.

---

## 테스트 계정

### 비밀번호 생성 규칙

> **규칙: `{login_id}001`**
>
> 예시: `admin` → `admin001`, `doctor1` → `doctor1001`, `ris1` → `ris1001`

| ID | 비밀번호 | 역할 |
|-----|----------|------|
| system | system001 | 시스템 관리자 |
| admin | admin001 | 병원 관리자 |
| doctor1 | doctor1001 | 의사 |
| doctor2 | doctor2001 | 의사 |
| doctor3 | doctor3001 | 의사 |
| doctor4 | doctor4001 | 의사 |
| doctor5 | doctor5001 | 의사 |
| nurse1 | nurse1001 | 간호사 |
| patient1 | patient1001 | 환자 |
| ris1 | ris1001 | 영상과 |
| lis1 | lis1001 | 검사과 |

---

## 파일 구조

```
brain_tumor_back/
└── setup_dummy_data/
    ├── __init__.py
    ├── __main__.py              # python -m setup_dummy_data 진입점
    ├── main.py                  # 통합 래퍼 (1_base + 2_add 순차 실행)
    ├── setup_dummy_data_1_base.py  # 기본 데이터
    ├── setup_dummy_data_2_add.py   # 추가 데이터
    └── DB_SETUP_GUIDE.md        # 이 파일
```

---

## 상세 설명

### setup_dummy_data_1_base.py (기본 데이터)
- **DB 자동 생성** (없는 경우)
- **마이그레이션 자동 실행**
- 역할 7개 (SYSTEMMANAGER, ADMIN, DOCTOR, NURSE, PATIENT, RIS, LIS)
- 슈퍼유저 (system / system001)
- 테스트 사용자 10명 (admin, doctor1~5, nurse1, patient1, ris1, lis1)
- 메뉴/권한 시드 데이터
- 환자 30명
- 진료 20건
- OCS (RIS) 30건 + ImagingStudy
- OCS (LIS) 20건
- AI 모델 3개 (M1, MG, MM)

### setup_dummy_data_2_add.py (추가 데이터)
- 치료 계획 15건 + 치료 세션
- 경과 추적 25건
- AI 추론 요청 10건

---

## 실행 옵션

```bash
# 전체 실행 (기존 데이터 유지, 부족분만 추가)
python -m setup_dummy_data

# 리셋 후 새로 생성 (권장)
python -m setup_dummy_data --reset

# 목표 수량 이상이어도 강제 추가
python -m setup_dummy_data --force

# 기본 데이터만 생성
python -m setup_dummy_data --base

# 추가 데이터만 생성
python -m setup_dummy_data --add

# 메뉴/권한만 업데이트 (네비게이션 바 반영) ⭐
python -m setup_dummy_data --menu
```

### 개별 실행
```bash
# 기본 데이터만
python setup_dummy_data/setup_dummy_data_1_base.py [--reset] [--force]

# 추가 데이터만
python setup_dummy_data/setup_dummy_data_2_add.py [--reset] [--force]
```

---

## 데이터 초기화 (수동)

```bash
python manage.py shell
>>> from apps.ai_inference.models import AIInferenceLog, AIInferenceResult, AIInferenceRequest
>>> from apps.treatment.models import TreatmentSession, TreatmentPlan
>>> from apps.followup.models import FollowUp
>>> from apps.imaging.models import ImagingStudy
>>> from apps.ocs.models import OCS, OCSHistory
>>> from apps.encounters.models import Encounter
>>> from apps.patients.models import Patient

# 순서대로 삭제 (의존성 역순)
>>> AIInferenceLog.objects.all().delete()
>>> AIInferenceResult.objects.all().delete()
>>> AIInferenceRequest.objects.all().delete()
>>> TreatmentSession.objects.all().delete()
>>> TreatmentPlan.objects.all().delete()
>>> FollowUp.objects.all().delete()
>>> OCSHistory.objects.all().delete()
>>> ImagingStudy.objects.all().delete()
>>> OCS.objects.all().delete()
>>> Encounter.objects.all().delete()
>>> Patient.objects.all().delete()
```

---

## 생성되는 데이터 통계

| 항목 | 수량 |
|------|------|
| 메뉴 | ~30개 |
| 권한 | ~30개 |
| 환자 | 30명 |
| 진료 | 20건 |
| OCS (RIS) | 30건 |
| OCS (LIS) | 20건 |
| 영상 검사 | 30건 |
| 치료 계획 | 15건 |
| 경과 기록 | 25건 |
| AI 모델 | 3개 |
| AI 요청 | 10건 |
