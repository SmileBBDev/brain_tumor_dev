# Docker Compose 구성 가이드

## 개요

이 프로젝트는 의료 영상 분석 시스템을 위한 Docker 기반 마이크로서비스 아키텍처입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                          메인 VM                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────────┐  │
│  │ Django  │  │ Orthanc │  │  Redis  │  │ OpenEMR + HAPI    │  │
│  │  :8000  │  │  :8042  │  │  :6379  │  │ FHIR :8080/:8081  │  │
│  └────┬────┘  └─────────┘  └─────────┘  └───────────────────┘  │
│       │              medical-net (Docker Bridge)                 │
└───────┼─────────────────────────────────────────────────────────┘
        │ HTTP (내부 IP)
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI VM (별도 서버)                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐              │
│  │ FastAPI  │  │ Celery       │  │ FastAPI-Redis │              │
│  │  :8001   │──│ Worker       │──│    :6380      │              │
│  └──────────┘  └──────────────┘  └───────────────┘              │
│                      fastapi-net (Docker Bridge)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 파일 구조

```
docker/
├── docker-compose.yml              # 기본 인프라 (Orthanc + Redis + Network)
├── docker-compose.django.yml       # Django + MySQL
├── docker-compose.fastapi.yml      # FastAPI + Celery (⚠️ 별도 VM 배포)
├── docker-compose.emr.yml          # OpenEMR + HAPI FHIR + DBs
├── setup.py                        # 환경 체크 및 자동 설정 스크립트
├── .env.example                    # 환경변수 템플릿
├── .env                            # 실제 환경변수 (생성 필요)
└── orthanc/
    └── orthanc.json                # Orthanc 설정
```

---

## 서비스 구성

| 파일 | 서비스 | 포트 | 배포 위치 |
|------|--------|------|----------|
| `docker-compose.yml` | orthanc, redis | 8042, 4242, 6379 | 메인 VM |
| `docker-compose.django.yml` | django, django-db | 8000, 3306 | 메인 VM |
| `docker-compose.emr.yml` | openemr, openemr-db, hapi-fhir, hapi-db | 8080, 8081, 3308, 5432 | 메인 VM |
| `docker-compose.fastapi.yml` | fastapi, fastapi-celery, fastapi-redis | 8001, 6380 | **별도 VM** |

---

## 빠른 시작

### 1단계: 환경 설정 (메인 VM)

```bash
cd docker
# cd C:\0000\brain_tumor_dev\docker

# .env 파일 생성
cp .env.example .env

# .env 파일 편집 - IP 주소와 비밀번호 수정
```

### 2단계: 메인 VM 서비스 실행

```bash
# 기본 인프라 (Orthanc + Redis)
# docker compose -f docker-compose.yml up -d

# Django + MySQL + 기본 인프라 (Orthanc + Redis)
docker compose -f docker-compose.django.yml up -d

# OpenEMR + HAPI FHIR (필요시)
docker compose -f docker-compose.emr.yml up -d
```

### 3단계: FastAPI VM 설정 (별도 서버)

```bash
# 1. 프로젝트 파일 복사 (docker 폴더 전체)
scp -r docker/ user@fastapi-vm:/path/to/project/

# 2. FastAPI VM에서 setup.py 실행 (필수!)
cd docker
python setup.py

# 3. .env 파일에서 MAIN_VM_IP 수정

# 4. Docker 빌드 및 실행
docker compose -f docker-compose.fastapi.yml up -d --build


```




cd C:\0000\brain_tumor_dev\docker
docker compose -f docker-compose.fastapi.yml down
docker compose -f docker-compose.django.yml down
docker compose -f docker-compose.django.yml up -d --build

docker compose -f docker-compose.fastapi.yml down
docker compose -f docker-compose.fastapi.yml up -d --build




---

## ⚠️ 중요: setup.py 사전 실행 (FastAPI VM)

FastAPI VM에서는 **반드시 `setup.py`를 먼저 실행**해야 합니다.

```bash
cd docker
python setup.py
```

### setup.py가 자동으로 하는 일

| 단계 | 내용 |
|------|------|
| 1 | Docker / Docker Compose 설치 확인 |
| 2 | **GPU 자동 감지** (nvidia-smi 실행) |
| 3 | 포트 사용 가능 여부 확인 |
| 4 | `.env` 파일 생성 및 **USE_GPU 자동 설정** |
| 5 | `docker-compose.fastapi.yml` GPU 설정 자동 활성화 |

### 실행 결과 예시

```
============================================================
   Brain Tumor CDSS - Docker 배포 설정
============================================================

============================================================
  1. Docker 체크
============================================================
  ✓ Docker - Docker version 24.0.7
  ✓ Docker Compose - Docker Compose version v2.21.0
  ✓ Docker 서비스 실행 중

============================================================
  2. GPU 체크
============================================================
  ✓ GPU 감지됨 - NVIDIA RTX 4090
  ✓ CUDA Version - 12.1
  ✓ NVIDIA Container Toolkit - Docker GPU 지원 확인됨

============================================================
  4. 환경 변수 설정
============================================================
  ✓ .env 파일 존재
  ✓ USE_GPU=true - 자동 설정됨
  ! MAIN_VM_IP 설정 필요 - 실제 IP로 변경하세요

============================================================
  설정 완료
============================================================

  ✓ 설정 완료!

  다음 단계:
  1. .env 파일에서 IP 주소와 비밀번호를 수정하세요
  2. 아래 명령어로 Docker를 실행하세요:

     # FastAPI VM (GPU)
     docker compose -f docker-compose.fastapi.yml up -d --build
```

---

## ⚠️ 중요: VM 간 통신 설정 (MAIN_VM_IP)

FastAPI는 별도의 VM에서 실행되므로, 메인 VM의 서비스에 접근하기 위해 **IP 주소 설정이 필수**입니다.

### 설정 방법

1. **메인 VM의 IP 주소 확인**
   ```bash
   # Linux
   ip addr show | grep "inet "

   # Windows
   ipconfig
   ```

2. **FastAPI VM의 `.env` 파일에 IP 설정**
   ```env
   # ⚠️ 반드시 실제 메인 VM IP로 변경!
   MAIN_VM_IP=192.168.1.100
   ```

3. **메인 VM의 `.env` 파일에 FastAPI URL 설정**
   ```env
   # ⚠️ 반드시 실제 FastAPI VM IP로 변경!
   FASTAPI_URL=http://192.168.1.200:8001
   ```








### 통신 흐름

```
┌─────────────────┐                      ┌─────────────────┐
│    메인 VM      │                      │   FastAPI VM    │
│  192.168.1.100  │                      │  192.168.1.200  │
├─────────────────┤                      ├─────────────────┤
│                 │   HTTP Request       │                 │
│  Django :8000   │ ──────────────────►  │  FastAPI :8001  │
│                 │   (AI 분석 요청)      │                 │
│                 │                      │                 │
│                 │   HTTP Response      │                 │
│                 │ ◄──────────────────  │  Celery Worker  │
│                 │   (분석 결과)         │                 │
│                 │                      │                 │
│  Orthanc :8042  │ ◄──────────────────  │                 │
│                 │   (DICOM 조회)        │                 │
└─────────────────┘                      └─────────────────┘
```

### 체크리스트

- [ ] 메인 VM과 FastAPI VM이 같은 네트워크에 있는지 확인
- [ ] 방화벽에서 필요한 포트 개방 (8000, 8001, 8042, 8080, 8081)
- [ ] FastAPI VM의 `.env`에 `MAIN_VM_IP` 설정 완료
- [ ] 메인 VM의 `.env`에 `FASTAPI_URL` 설정 완료
- [ ] `ping` 명령으로 VM 간 통신 테스트

---

## 서비스별 실행 명령어

### 메인 VM

```bash
cd docker

# 기본 인프라 (Orthanc + Redis + Network)
docker compose -f docker-compose.yml up -d

# Django + MySQL
docker compose -f docker-compose.django.yml up -d

# OpenEMR + HAPI FHIR
docker compose -f docker-compose.emr.yml up -d
```

### FastAPI VM (별도 서버)

```bash
cd docker

# 1. 환경 체크 및 자동 설정 (필수!)
python setup.py

# 2. .env 파일에서 MAIN_VM_IP 수정

# 3. 빌드 및 실행
docker compose -f docker-compose.fastapi.yml up -d --build
```

---

## 서비스 관리

### 로그 확인

```bash
# 메인 VM
docker compose -f docker-compose.yml logs -f
docker compose -f docker-compose.django.yml logs -f django
docker compose -f docker-compose.emr.yml logs -f openemr

# FastAPI VM
docker compose -f docker-compose.fastapi.yml logs -f fastapi
docker compose -f docker-compose.fastapi.yml logs -f fastapi-celery
```

### 서비스 재시작

```bash
# 메인 VM - Django만 재시작
docker compose -f docker-compose.django.yml restart django

# FastAPI VM - FastAPI만 재시작
docker compose -f docker-compose.fastapi.yml restart fastapi
```

### 서비스 중지

```bash
# 메인 VM
docker compose -f docker-compose.yml down
docker compose -f docker-compose.django.yml down
docker compose -f docker-compose.emr.yml down

# FastAPI VM
docker compose -f docker-compose.fastapi.yml down
```

### 서비스 상태 확인

```bash
# 메인 VM
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.django.yml ps
docker compose -f docker-compose.emr.yml ps

# FastAPI VM
docker compose -f docker-compose.fastapi.yml ps
```

---

## 데이터 볼륨

### 메인 VM

| 볼륨 | 용도 |
|------|------|
| `redis_data` | Redis 영속 데이터 |
| `orthanc_data` | DICOM 이미지 저장 |
| `django_db_data` | Django MySQL 데이터 |
| `django_static` | Django 정적 파일 |
| `django_media` | Django 미디어 파일 |
| `openemr_sites` | OpenEMR 사이트 데이터 |
| `openemr_db_data` | OpenEMR MariaDB 데이터 |
| `hapi_db_data` | HAPI FHIR PostgreSQL 데이터 |

### FastAPI VM

| 볼륨 | 용도 |
|------|------|
| `fastapi_models` | AI 모델 파일 |
| `fastapi_temp` | 임시 처리 파일 |
| `fastapi_redis_data` | Celery 브로커 데이터 |

---

## 문제 해결

### Docker 서비스 연결 실패

```bash
# 네트워크 확인
docker network ls
docker network inspect medical-net

# 컨테이너 IP 확인
docker inspect nn-django | grep IPAddress
```

### VM 간 통신 불가

1. **방화벽 확인**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 8001/tcp

   # Windows
   netsh advfirewall firewall show rule name=all
   ```

2. **IP 설정 확인**
   ```bash
   # FastAPI VM에서 메인 VM 접근 테스트
   curl http://${MAIN_VM_IP}:8042/system
   ```

### GPU 인식 안 됨 (FastAPI VM)

```bash
# 1. NVIDIA 드라이버 확인
nvidia-smi

# 2. NVIDIA Container Toolkit 설치
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker

# 3. setup.py 다시 실행
python setup.py

# 4. 이미지 재빌드
docker compose -f docker-compose.fastapi.yml up -d --build
```

### 데이터베이스 연결 실패

```bash
# DB 컨테이너 로그 확인
docker logs nn-django-db

# DB 직접 접속 테스트
docker exec -it nn-django-db mysql -u root -p
```

---

## 백업 및 복원

### 볼륨 백업

```bash
# Django DB 백업
docker exec nn-django-db mysqldump -u root -p brain_tumor > backup.sql

# 볼륨 전체 백업
docker run --rm -v django_db_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/django_db_backup.tar.gz /data
```

### 볼륨 복원

```bash
docker run --rm -v django_db_data:/data -v $(pwd):/backup \
    alpine tar xzf /backup/django_db_backup.tar.gz -C /
```

---

## 배포 체크리스트

### 메인 VM

- [ ] `.env` 파일 생성 및 설정
- [ ] `FASTAPI_URL` 설정 (FastAPI VM IP)
- [ ] `docker-compose.yml` 실행
- [ ] `docker-compose.django.yml` 실행
- [ ] `docker-compose.emr.yml` 실행 (필요시)
- [ ] 방화벽 포트 개방

### FastAPI VM

- [ ] 프로젝트 파일 복사
- [ ] **`python setup.py` 실행** (필수!)
- [ ] `.env` 파일에서 `MAIN_VM_IP` 설정
- [ ] `docker-compose.fastapi.yml` 빌드 및 실행
- [ ] 방화벽 포트 개방
- [ ] 메인 VM과 통신 테스트
