# MG 추론 Callback 실패 문제 해결 보고서

## 문제 요약

| 항목 | 내용 |
|------|------|
| 발생일 | 2026-01-17 |
| 증상 | MG 추론 요청 후 PENDING 상태에서 멈춤 |
| 영향 범위 | MG (Gene Expression) 추론 기능 전체 |
| 해결 상태 | 완료 |

---

## 증상

1. Dashboard에서 MG 추론 버튼 클릭
2. 추론 요청은 정상적으로 FastAPI로 전달됨
3. Celery Worker에서 추론 완료 (약 0.5초 소요)
4. **Django로 결과 Callback 실패**
5. 프론트엔드에서 계속 PENDING 상태로 폴링

```
127.0.0.1:64690 - - [17/Jan/2026:14:24:49] "GET /api/ai/inferences/ai_req_0003/" 200 309
127.0.0.1:64690 - - [17/Jan/2026:14:24:50] "GET /api/ai/inferences/ai_req_0003/" 200 309
(무한 반복...)
```

---

## 원인 분석

### 1. Celery Worker 로그 확인

**MG 추론 성공, Callback 실패:**
```
[2026-01-17 05:24:15,684: WARNING/ForkPoolWorker-2]   Inference complete: 23.7ms
[2026-01-17 05:24:15,783: WARNING/ForkPoolWorker-2]   Warning: Callback failed: [Errno 111] Connection refused
```

**M1 추론 성공, Callback 성공:**
```
[M1] Callback URL resolved: http://localhost:8000/api/ai/callback/ -> http://host.docker.internal:8000/api/ai/callback/
HTTP Request: POST http://host.docker.internal:8000/api/ai/callback/ "HTTP/1.1 200 OK"
Callback sent successfully with 4 files
```

### 2. 근본 원인

Docker 컨테이너 내부에서 `localhost:8000`으로 Django에 접근할 수 없음.

- **M1 tasks**: `resolve_callback_url()` 함수로 `localhost` → `host.docker.internal` 변환 로직 존재
- **MG tasks**: 해당 변환 로직 **누락**

### 3. 코드 비교

**m1_tasks.py (정상 동작):**
```python
def resolve_callback_url(callback_url: str) -> str:
    """Docker 환경에서 callback URL의 localhost를 실제 Django URL로 대체"""
    django_url = os.getenv('DJANGO_URL', '')

    if 'localhost' in callback_url or '127.0.0.1' in callback_url:
        # localhost를 host.docker.internal로 변환
        resolved_url = django_url.rstrip('/') + path
        return resolved_url

    return callback_url

# 사용
resolved_url = resolve_callback_url(callback_url)
response = httpx.post(resolved_url, json=callback_data, timeout=60.0)
```

**mg_tasks.py (문제 코드):**
```python
# resolve_callback_url 함수 없음!

# 직접 localhost로 요청 시도 → Connection refused
response = httpx.post(callback_url, json=callback_data, timeout=60.0)
```

---

## 해결 방법

### 수정 파일

`modAI/tasks/mg_tasks.py`

### 변경 내용

1. `resolve_callback_url()` 함수 추가
2. 성공 Callback과 에러 Callback 모두에 적용

```python
import os

def resolve_callback_url(callback_url: str) -> str:
    """
    Docker 환경에서 callback URL의 localhost를 실제 Django URL로 대체
    """
    django_url = os.getenv('DJANGO_URL', '')

    if not django_url:
        return callback_url

    if 'localhost' in callback_url or '127.0.0.1' in callback_url:
        from urllib.parse import urlparse
        parsed = urlparse(callback_url)
        path = parsed.path
        if parsed.query:
            path += f'?{parsed.query}'

        resolved_url = django_url.rstrip('/') + path
        print(f"[MG] Callback URL resolved: {callback_url} -> {resolved_url}")
        return resolved_url

    return callback_url


# 성공 Callback
resolved_callback_url = resolve_callback_url(callback_url)
response = httpx.post(resolved_callback_url, json=callback_data, timeout=60.0)

# 에러 Callback
resolved_callback_url = resolve_callback_url(callback_url)
httpx.post(resolved_callback_url, json=callback_data, timeout=10.0)
```

### 적용 방법

```bash
# Celery Worker 재시작
docker restart nn-fastapi-celery
```

---

## 환경 설정 요구사항

Docker 환경에서 Callback이 동작하려면 `DJANGO_URL` 환경변수 필요:

**docker/.env:**
```env
# Django (호스트) - 콜백 URL용
DJANGO_URL=http://host.docker.internal:8000
```

**docker-compose.fastapi.yml:**
```yaml
fastapi-celery:
  environment:
    - DJANGO_URL=${DJANGO_URL:-http://${MAIN_VM_IP}:8000}
```

---

## 검증 결과

### 수정 후 Celery 로그

```
[MG] Callback URL resolved: http://localhost:8000/api/ai/callback/ -> http://host.docker.internal:8000/api/ai/callback/
HTTP Request: POST http://host.docker.internal:8000/api/ai/callback/ "HTTP/1.1 200 OK"
Callback sent successfully with 2 files
```

### 프론트엔드 동작

- MG 추론 요청 → PROCESSING → **COMPLETED**
- 결과 데이터 정상 표시

---

## 추가 수정 사항

### 1. BIOMARKER OCS 리스트업 안됨 문제

**원인:** `MMAvailableOCSView`에서 BIOMARKER OCS 필터링 조건 누락

**수정 파일:** `brain_tumor_back/apps/ai_inference/views.py`

**변경 전:**
```python
protein_ocs_queryset = OCS.objects.filter(
    patient=patient,
    job_type='BIOMARKER',
    ocs_status=OCS.OcsStatus.CONFIRMED  # CONFIRMED만
)
```

**변경 후:**
```python
protein_ocs_queryset = OCS.objects.filter(
    patient=patient,
    job_role='LIS',  # job_role 조건 추가
    job_type='BIOMARKER',
    ocs_status__in=[OCS.OcsStatus.CONFIRMED, OCS.OcsStatus.RESULT_READY]  # RESULT_READY 추가
)
```

### 2. FastAPI 포트 불일치 (8001 → 9000)

**원인:** 일부 파일에서 구버전 포트(8001) 사용

**수정 파일:**
- `views.py` - FASTAPI_URL 기본값
- `docker/.env` - FASTAPI_URL
- `docker/.env.example` - FASTAPI_URL
- `docker-compose.django.yml` - 기본값
- `docker/setup.py` - REQUIRED_PORTS
- `docker/README.md` - 문서
- `README.md` - 문서
- `docs/ai-inference-sequence.puml` - 다이어그램
- `modAI/test_mg_queue.py` - 테스트 코드

---

## 교훈 및 권장사항

1. **새 Task 작성 시** Docker 환경의 네트워크 특성 고려 필요
2. **localhost 사용 금지** - Docker 내부에서 호스트 접근 시 `host.docker.internal` 사용
3. **공통 유틸리티 분리** - `resolve_callback_url`을 공통 모듈로 분리 권장
4. **일관된 포트 사용** - 환경변수로 중앙 관리

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `modAI/tasks/mg_tasks.py` | MG Celery Task (수정됨) |
| `modAI/tasks/m1_tasks.py` | M1 Celery Task (참조) |
| `docker/.env` | Docker 환경변수 |
| `docker-compose.fastapi.yml` | FastAPI + Celery 구성 |
| `brain_tumor_back/apps/ai_inference/views.py` | Django AI 추론 API |
