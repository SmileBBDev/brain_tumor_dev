# modAI Docker 빌드 최적화 가이드

## 빌드 시간 분석

첫 빌드 시 약 **18분** 소요되는 이유:
- PyTorch + TorchVision: ~800MB (CPU) / ~2GB (GPU)
- MONAI (의료 영상 딥러닝): 대용량 의존성
- NumPy, SciPy, Pandas: 컴파일 필요

---

## 방법 1: Docker 캐시 활용 (자동)

아무것도 안해도 됩니다. Docker가 자동으로 레이어를 캐시합니다.

```bash
# 코드만 수정하고 다시 빌드
docker compose -f docker-compose.fastapi.yml up -d --build
```

**캐시 동작:**
| 레이어 | 캐시 사용 |
|--------|----------|
| FROM python:3.11-slim | O |
| apt-get install | O |
| pip install torch | O |
| pip install -r requirements.txt | O (requirements.txt 변경 없을 시) |
| COPY . . | X (소스코드 변경 시 재실행) |

**결과:** 소스코드만 변경 시 빌드 시간 **몇 초**

---

## 방법 2: Base 이미지 만들기 (권장)

PyTorch가 포함된 base 이미지를 미리 만들어둡니다.

### Step 1: Base Dockerfile 생성

`docker/Dockerfile.base` 파일 생성:

```dockerfile
# Dockerfile.base - PyTorch 포함 Base 이미지
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# PyTorch CPU 버전 설치
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU 버전 사용 시 위 라인을 아래로 교체:
# RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 2: Base 이미지 빌드 (한 번만 실행)

```bash
cd docker
docker build -f Dockerfile.base -t modai-pytorch-base:latest .
```

### Step 3: 기존 Dockerfile 수정

`modAI/Dockerfile` 수정:

```dockerfile
# 변경 전
FROM python:3.11-slim

# 변경 후
FROM modai-pytorch-base:latest
```

그리고 PyTorch 설치 부분(33-43줄) 삭제:

```dockerfile
# 이 부분 삭제
RUN if [ "$USE_GPU" = "true" ]; then \
    ...
fi
```

**결과:** 빌드 시간 **18분 → 2-3분**

---

## 방법 3: Docker Hub에 Base 이미지 푸시 (팀 공유)

### 이미지 푸시

```bash
# Docker Hub 로그인
docker login

# 태그 지정
docker tag modai-pytorch-base:latest [your-dockerhub-id]/modai-pytorch-base:latest

# 푸시
docker push [your-dockerhub-id]/modai-pytorch-base:latest
```

### 팀원 사용법

```dockerfile
FROM [your-dockerhub-id]/modai-pytorch-base:latest
```

---

## 추천 시나리오

| 상황 | 추천 방법 |
|------|----------|
| 혼자 개발 | 방법 1 (캐시 자동 활용) |
| 팀 개발 / CI/CD | 방법 2 + 3 (Base 이미지) |
| requirements.txt 자주 변경 | 방법 2 필수 |
| 새 PC에서 빌드 | 방법 3 (Docker Hub) |

---

## 캐시 초기화 (문제 발생 시)

```bash
# 캐시 없이 완전 새로 빌드
docker compose -f docker-compose.fastapi.yml build --no-cache

# 모든 이미지/컨테이너 정리
docker system prune -a
```

---

## 빠른 참조

```bash
# 일반 빌드 (캐시 사용)
docker compose -f docker-compose.fastapi.yml up -d --build

# 백그라운드 실행
docker compose -f docker-compose.fastapi.yml up -d

# 로그 확인
docker compose -f docker-compose.fastapi.yml logs -f

# 중지
docker compose -f docker-compose.fastapi.yml down

# 볼륨 포함 완전 삭제
docker compose -f docker-compose.fastapi.yml down -v
```
