# Docker 환경에서 CDSS_STORAGE 경로 문제 해결

## 문제 상황

로컬 가상환경에서 Docker 환경으로 전환 시 다음과 같은 404 에러 발생:

```
GET http://localhost:8000/api/ai/mg/gene-expression/44/ 404 (Not Found)
POST http://localhost:8000/api/ai/mg/inference/ 404 (Not Found)
```

**특징:**
- M1 추론은 정상 동작
- MG, MM 등 파일 시스템 접근이 필요한 API만 404 발생

## 원인

### 1. 볼륨 마운트 누락

`docker-compose.django.yml`에서 `CDSS_STORAGE` 폴더가 마운트되지 않음:

```yaml
# 기존 (문제 발생)
volumes:
  - ../brain_tumor_back:/app
  - django_static:/app/static
  - django_media:/app/media
```

### 2. 경로 불일치

Django `settings.py`에서 경로 설정:

```python
CDSS_STORAGE_ROOT = BASE_DIR.parent / "CDSS_STORAGE"
```

- **로컬 환경**: `BASE_DIR` = `c:\0000\brain_tumor_dev\brain_tumor_back` → 상위에 `CDSS_STORAGE` 존재
- **Docker 환경**: `BASE_DIR` = `/app` → `/CDSS_STORAGE`는 마운트되지 않아 존재하지 않음

## 해결 방법

### Step 1: docker-compose.django.yml 수정

`CDSS_STORAGE` 볼륨 마운트 추가:

```yaml
volumes:
  - ../brain_tumor_back:/app
  - ../CDSS_STORAGE:/CDSS_STORAGE    # 추가
  - django_static:/app/static
  - django_media:/app/media
```

### Step 2: settings.py 수정

Docker/로컬 환경 자동 감지 로직 추가:

```python
# ==================================================
# CDSS STORAGE (Single Source of Truth)
# Docker 환경: /CDSS_STORAGE (볼륨 마운트)
# 로컬 환경: BASE_DIR.parent / "CDSS_STORAGE"
# ==================================================
_docker_cdss_path = Path("/CDSS_STORAGE")
CDSS_STORAGE_ROOT = _docker_cdss_path if _docker_cdss_path.exists() else BASE_DIR.parent / "CDSS_STORAGE"

CDSS_LIS_STORAGE = CDSS_STORAGE_ROOT / "LIS"
CDSS_RIS_STORAGE = CDSS_STORAGE_ROOT / "RIS"
CDSS_AI_STORAGE = CDSS_STORAGE_ROOT / "AI"
```

### Step 3: Docker 컨테이너 재시작

```bash
cd c:\0000\brain_tumor_dev\docker
docker-compose -f docker-compose.django.yml down
docker-compose -f docker-compose.django.yml up -d
```

## 디렉토리 구조

```
brain_tumor_dev/
├── brain_tumor_back/          # Django 프로젝트 (/app으로 마운트)
│   └── config/
│       └── settings.py
├── CDSS_STORAGE/              # 데이터 저장소 (/CDSS_STORAGE로 마운트)
│   ├── LIS/
│   │   ├── ocs_0036/
│   │   │   └── gene_expression.csv
│   │   └── ocs_0044/
│   │       └── gene_expression.csv
│   ├── RIS/
│   └── AI/
└── docker/
    └── docker-compose.django.yml
```

## 확인 방법

### Docker 컨테이너 내부에서 경로 확인

```bash
docker exec -it nn-django sh
ls -la /CDSS_STORAGE/LIS/
```

### Django 설정 확인

```bash
docker exec -it nn-django python -c "from django.conf import settings; print(settings.CDSS_STORAGE_ROOT)"
```

정상이면 `/CDSS_STORAGE` 출력

## 관련 파일

| 파일 | 역할 |
|------|------|
| `docker/docker-compose.django.yml` | 볼륨 마운트 설정 |
| `brain_tumor_back/config/settings.py` | CDSS_STORAGE 경로 설정 |
| `brain_tumor_back/apps/ai_inference/views.py` | MG/MM API에서 경로 사용 |

## 주의사항

1. **다른 docker-compose 파일도 확인**: `docker-compose.yml`, `docker-compose.production.yml` 등에도 동일하게 볼륨 마운트 추가 필요

2. **Windows 경로**: Windows에서 Docker Desktop 사용 시 경로가 자동 변환됨 (`c:\0000\...` → `/mnt/c/0000/...` 또는 직접 마운트)

3. **권한 문제**: Linux/Mac에서는 볼륨 마운트 시 파일 권한 문제가 발생할 수 있음. 필요시 `:rw` 옵션 또는 사용자 설정 추가
