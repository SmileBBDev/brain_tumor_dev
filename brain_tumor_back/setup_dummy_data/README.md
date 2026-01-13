# Setup Dummy Data - 더미 데이터 생성 시스템

Brain Tumor CDSS 프로젝트의 개발/테스트용 더미 데이터 생성 시스템입니다.

## 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [설계 철학](#설계-철학)
4. [사용법](#사용법)
5. [파일 구조](#파일-구조)
6. [데이터 흐름](#데이터-흐름)
7. [새 기능 추가 가이드](#새-기능-추가-가이드)
8. [테스트 계정](#테스트-계정)

---

## 개요

이 시스템은 개발 및 테스트 환경에서 필요한 더미 데이터를 자동으로 생성합니다.

### 주요 기능

- **자동 DB 생성**: MySQL 데이터베이스가 없으면 자동 생성
- **자동 마이그레이션**: `makemigrations` + `migrate` 자동 실행
- **멱등성 보장**: 여러 번 실행해도 동일한 결과
- **계층적 데이터 생성**: 의존성 순서대로 데이터 생성
- **유연한 옵션**: 부분 실행, 초기화, 강제 추가 등 지원

---

## 아키텍처

```
setup_dummy_data/
├── main.py                          # 통합 실행 래퍼 (진입점)
├── __main__.py                      # python -m setup_dummy_data 지원
├── __init__.py                      # 패키지 초기화
├── setup_dummy_data_1_base.py       # 기본 데이터 (필수)
├── setup_dummy_data_2_add.py        # 추가 데이터 (선택)
├── setup_dummy_data_3_prescriptions.py  # 처방 데이터 (선택)
├── DB_SETUP_GUIDE.md                # DB 설정 가이드
└── README.md                        # 이 문서
```

### 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (통합 래퍼)                      │
├─────────────────────────────────────────────────────────────┤
│  1_base.py    │    2_add.py     │   3_prescriptions.py     │
│  (기본 데이터)  │   (추가 데이터)   │     (처방 데이터)         │
├───────────────┼─────────────────┼──────────────────────────┤
│  - DB 생성     │  - 치료 계획     │  - 처방전                 │
│  - 마이그레이션 │  - 경과 추적     │  - 처방 항목              │
│  - 역할/사용자  │  - AI 요청      │                          │
│  - 메뉴/권한   │                 │                          │
│  - 환자/진료   │                 │                          │
│  - OCS/영상   │                 │                          │
│  - AI 모델    │                 │                          │
└───────────────┴─────────────────┴──────────────────────────┘
```

---

## 설계 철학

### 1. 멱등성 (Idempotency)

여러 번 실행해도 동일한 결과를 보장합니다.

```python
# 이미 존재하면 SKIP, 없으면 CREATE
if User.objects.filter(login_id=login_id).exists():
    print(f"  [SKIP] {login_id} 이미 존재")
else:
    User.objects.create_user(...)
    print(f"  [CREATE] {login_id}")
```

### 2. 계층적 의존성 (Layered Dependencies)

```
1_base (기본) ──► 2_add (추가) ──► 3_prescriptions (처방)
     │                │                    │
     ▼                ▼                    ▼
  역할/사용자       치료계획              처방전
  메뉴/권한        경과추적              처방항목
  환자/진료        AI요청
  OCS/영상
  AI모델
```

각 스크립트는 이전 단계의 데이터에 의존합니다.

### 3. 목표 수량 기반 생성

```python
def create_dummy_patients(target_count=30, force=False):
    existing = Patient.objects.filter(is_deleted=False).count()

    # 이미 목표 수량 이상이면 SKIP
    if existing >= target_count and not force:
        print(f"[SKIP] 이미 {existing}명 존재")
        return

    # 부족분만 생성
    to_create = target_count - existing
```

### 4. 트랜잭션 안전성

```python
from django.db import transaction

@transaction.atomic
def create_complex_data():
    # 모든 작업이 성공하거나 모두 롤백
    ...
```

---

## 사용법

### 기본 실행

```bash
# 프로젝트 루트에서 실행
cd brain_tumor_back

# 전체 데이터 생성 (기존 데이터 유지, 부족분만 추가)
python -m setup_dummy_data

# 또는
python setup_dummy_data/main.py
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `--reset` | 기존 데이터 삭제 후 새로 생성 |
| `--force` | 목표 수량 이상이어도 강제 추가 |
| `--base` | 기본 데이터만 생성 (1_base) |
| `--add` | 추가 데이터만 생성 (2_add) |
| `--prescriptions` | 처방 데이터만 생성 (3_prescriptions) |
| `--menu` | 메뉴/권한만 업데이트 |
| `-y, --yes` | 확인 없이 자동 실행 |

### 사용 예시

```bash
# 전체 초기화 후 재생성
python -m setup_dummy_data --reset

# 메뉴/권한만 업데이트 (네비게이션 반영)
python -m setup_dummy_data --menu

# 기본 데이터만 강제 추가
python -m setup_dummy_data --base --force

# 처방 데이터 초기화 후 재생성
python -m setup_dummy_data --prescriptions --reset
```

---

## 파일 구조

### main.py - 통합 실행 래퍼

```python
def main():
    # 1. 기본 데이터
    run_script('setup_dummy_data_1_base.py', args)

    # 2. 추가 데이터
    run_script('setup_dummy_data_2_add.py', args)

    # 3. 처방 데이터
    run_script('setup_dummy_data_3_prescriptions.py', args)

    # 4. 추가 사용자 (admin2, nurse2...)
    create_additional_users()

    # 5. 환자 계정 연결
    link_patient_accounts()

    # 6. 최종 요약
    print_final_summary()
```

### setup_dummy_data_1_base.py - 기본 데이터

```python
# ========== 0단계: 인프라 ==========
create_database_if_not_exists()  # DB 자동 생성
run_migrations()                  # makemigrations + migrate

# ========== 1단계: 기본 설정 ==========
setup_roles()           # 역할 정의
setup_superuser()       # 시스템 관리자
setup_test_users()      # 테스트 사용자

# ========== 2단계: 메뉴/권한 ==========
setup_menus_and_permissions()
    ├── permissions_data[]     # 권한 정의
    ├── create_menu()          # 메뉴 생성
    ├── menu_labels_data[]     # 메뉴 라벨
    └── role_menu_permissions  # 역할별 권한

# ========== 3단계: 비즈니스 데이터 ==========
create_dummy_patients()      # 환자 30명
create_dummy_encounters()    # 진료 기록
create_dummy_ocs()           # OCS (RIS/LIS)
create_dummy_imaging()       # 영상 검사
setup_ai_models()            # AI 모델
```

### setup_dummy_data_2_add.py - 추가 데이터

```python
create_treatment_plans()     # 치료 계획 15건
create_follow_ups()          # 경과 추적 25건
create_ai_requests()         # AI 요청 10건
```

### setup_dummy_data_3_prescriptions.py - 처방 데이터

```python
create_prescriptions()       # 처방전 20건
# 자동으로 처방 항목 60건 생성
```

---

## 데이터 흐름

### 실행 순서

```
python -m setup_dummy_data
         │
         ▼
    ┌─────────┐
    │ main.py │
    └────┬────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 1_base.py                               │
    │  ├─► DB 생성 (없으면)                    │
    │  ├─► 마이그레이션 (makemigrations+migrate)│
    │  ├─► 역할 7개                            │
    │  ├─► 사용자 15명                         │
    │  ├─► 메뉴 40개                           │
    │  ├─► 권한 매핑                           │
    │  ├─► 환자 30명                           │
    │  ├─► 진료 23건                           │
    │  ├─► OCS 60건 (RIS 30, LIS 30)          │
    │  ├─► 영상 30건                           │
    │  └─► AI 모델 3개                         │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 2_add.py                                │
    │  ├─► 치료 계획 15건                      │
    │  ├─► 경과 추적 25건                      │
    │  └─► AI 요청 10건                        │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 3_prescriptions.py                      │
    │  └─► 처방 20건 + 항목 61건               │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 추가 사용자 생성                         │
    │  └─► admin2,3 / nurse2,3 / ris2,3 등    │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 환자 계정 연결                           │
    │  └─► patient1~3 ↔ P202600001~003       │
    └────┬────────────────────────────────────┘
         │
         ▼
    최종 요약 출력
```

---

## 새 기능 추가 가이드

### 새 권한 추가

`setup_dummy_data_1_base.py`의 `permissions_data` 수정:

```python
permissions_data = [
    # 기존 권한들...
    ('NEW_FEATURE', '새 기능', '새 기능 설명'),
    ('NEW_FEATURE_LIST', '새 기능 목록', '새 기능 목록 화면'),
]
```

### 새 메뉴 추가

`setup_dummy_data_1_base.py`의 `setup_menus_and_permissions()` 수정:

```python
# 메뉴 생성 (ID는 기존 최대값 + 1)
menu_new, _ = create_menu(
    42,                          # ID
    code='NEW_FEATURE',          # 코드
    path=None,                   # 상위 메뉴는 path 없음
    icon='star',                 # 아이콘
    group_label='새기능',         # 그룹 라벨
    order=9,                     # 정렬 순서
    is_active=True
)
menu_new_list, _ = create_menu(
    43,
    code='NEW_FEATURE_LIST',
    path='/new-feature',
    icon='list',
    order=1,
    is_active=True,
    parent=menu_new              # 상위 메뉴
)
```

### 메뉴 라벨 추가

```python
menu_labels_data = [
    # 기존 라벨들...
    (42, 'DEFAULT', '새 기능'),
    (43, 'DEFAULT', '새 기능 목록'),
]
```

### 역할별 권한 매핑

```python
role_menu_permissions = {
    'SYSTEMMANAGER': list(menu_map.keys()),  # 모든 메뉴
    'ADMIN': [
        # 기존 권한들...
        'NEW_FEATURE', 'NEW_FEATURE_LIST',
    ],
    'DOCTOR': [
        # 기존 권한들...
        'NEW_FEATURE_LIST',  # 필요시 추가
    ],
    # 다른 역할들...
}
```

### 새 앱 추가 시

1. `migrations/__init__.py` 파일 생성:
```bash
mkdir apps/newapp/migrations
touch apps/newapp/migrations/__init__.py
```

2. `config/urls.py`에 URL 등록:
```python
path("api/newapp/", include("apps.newapp.urls")),
```

3. `setup_dummy_data` 실행:
```bash
python -m setup_dummy_data
# makemigrations가 자동으로 새 앱의 마이그레이션 생성
```

---

## 테스트 계정

### 기본 계정

| 역할 | 로그인 ID | 비밀번호 | 설명 |
|------|----------|----------|------|
| SYSTEMMANAGER | system | system001 | 시스템 관리자 (전체 권한) |
| ADMIN | admin | admin001 | 병원 관리자 |
| DOCTOR | doctor1~5 | doctor001~005 | 의사 5명 |
| NURSE | nurse1 | nurse001 | 간호사 |
| PATIENT | patient1 | patient001 | 환자 |
| RIS | ris1 | ris001 | 영상과 |
| LIS | lis1 | lis001 | 검사과 |

### 추가 계정 (main.py에서 생성)

| 역할 | 로그인 ID | 비밀번호 |
|------|----------|----------|
| ADMIN | admin2, admin3 | admin001 |
| NURSE | nurse2, nurse3 | nurse001 |
| RIS | ris2, ris3 | ris001 |
| LIS | lis2, lis3 | lis001 |
| PATIENT | patient2, patient3 | patient001 |

### 환자 계정 연결

| 계정 | 환자번호 | 환자명 |
|------|----------|--------|
| patient1 | P202600001 | 김철수 |
| patient2 | P202600002 | 이영희 |
| patient3 | P202600003 | 박민수 |

---

## 트러블슈팅

### 마이그레이션 실패 시

```bash
# 수동으로 마이그레이션 실행
python manage.py makemigrations --skip-checks
python manage.py migrate --skip-checks
```

### 특정 앱 마이그레이션만

```bash
python manage.py makemigrations accounts reports --skip-checks
python manage.py migrate --skip-checks
```

### 메뉴가 네비게이션에 안 보일 때

```bash
# 메뉴/권한만 업데이트
python -m setup_dummy_data --menu
```

### 데이터 완전 초기화

```bash
# 모든 더미 데이터 삭제 후 재생성
python -m setup_dummy_data --reset -y
```

---

## 관련 문서

- [DB_SETUP_GUIDE.md](./DB_SETUP_GUIDE.md) - 데이터베이스 설정 가이드
- [프로젝트 README](../README.md) - 프로젝트 전체 문서
