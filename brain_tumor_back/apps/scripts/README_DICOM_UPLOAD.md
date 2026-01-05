# DICOM 업로드 및 Orthanc 연동 테스트 가이드

**작성일**: 2025-12-29
**목적**: 로컬 DICOM 데이터를 Orthanc에 업로드하고 Django에서 조회하는 방법

---

## 📋 목차

1. [사전 준비](#1-사전-준비)
2. [DICOM 업로드 스크립트 실행](#2-dicom-업로드-스크립트-실행)
3. [Django API 테스트](#3-django-api-테스트)
4. [문제 해결](#4-문제-해결)

---

## 1. 사전 준비

### 1.1 Orthanc 서버 실행

```powershell
# Orthanc Docker 컨테이너 시작
cd d:\1222\NeuroNova_v1\NeuroNova_02_back_end\03_orthanc_pacs
docker-compose up -d

# 서버 상태 확인
docker ps | findstr orthanc
```

**Orthanc 접속 정보:**
- URL: `http://localhost:8042`
- 웹 UI: `http://localhost:8042/app/explorer.html`
- 인증: 비활성화 (Django에서 인증 처리)

### 1.2 DICOM 파일 준비 확인

다음 경로에 DICOM 파일이 있는지 확인:

```
C:\Users\302-28\Downloads\sub\sub-0004\
C:\Users\302-28\Downloads\sub\sub-0005\
```

---

## 2. DICOM 업로드 스크립트 실행

### 2.1 스크립트 실행

```powershell
cd d:\1222\NeuroNova_v1\NeuroNova_02_back_end\01_django_server

# 가상환경 활성화
./venv/Scripts/activate

# 업로드 스크립트 실행
python scripts/upload_dicom_to_orthanc.py
```

### 2.2 예상 출력

```
================================================================================
🏥 DICOM 파일 Orthanc 업로드 시작
================================================================================
Orthanc 서버: http://localhost:8042
대상 환자 수: 2명

✅ Orthanc 서버 연결 성공!
   버전: 1.12.1
   이름: Orthanc

================================================================================
👤 환자 1/2 처리 중
================================================================================
📁 디렉토리 스캔 중: C:\Users\302-28\Downloads\sub\sub-0004
   발견된 DICOM 파일: 150개

📤 업로드 시작: 150개 파일
--------------------------------------------------------------------------------
[1/150] 처리 중...
✅ 업로드 성공: image_001.dcm (Instance ID: abc123...)
[2/150] 처리 중...
✅ 업로드 성공: image_002.dcm (Instance ID: def456...)
...
--------------------------------------------------------------------------------

================================================================================
👤 환자 2/2 처리 중
================================================================================
...

================================================================================
📊 업로드 완료 - 결과 요약
================================================================================
총 파일 수:    300개
성공:          298개 ✅
실패:          2개 ❌
성공률:        99.3%

✅ Orthanc에 저장된 총 환자 수: 2명
   환자 ID 목록: ['abc123', 'def456']

🎉 모든 작업이 완료되었습니다!
Orthanc 웹 UI: http://localhost:8042/app/explorer.html
```

### 2.3 Orthanc 웹 UI 확인

1. 브라우저에서 접속: `http://localhost:8042/app/explorer.html`
2. "All patients" 메뉴에서 업로드된 환자 확인 (인증 불필요)

---

## 3. Django API 테스트

### 3.1 Django 서버 실행

```powershell
cd d:\1222\NeuroNova_v1\NeuroNova_02_back_end\01_django_server
./venv/Scripts/activate
python manage.py runserver
```

### 3.2 Orthanc 연결 상태 확인

**API 엔드포인트**: `GET http://localhost:8000/api/ris/health/`

**Postman 또는 브라우저로 접속**:
```
http://localhost:8000/api/ris/health/
```

**예상 응답**:
```json
{
  "success": true,
  "message": "Orthanc 연결 성공",
  "version": "1.12.1",
  "name": "Orthanc"
}
```

### 3.3 환자 목록 조회 테스트

**API 엔드포인트**: `GET http://localhost:8000/api/ris/test/patients/`

**Query Parameters**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10, 최대: 100)

**curl 명령어**:
```bash
# 첫 번째 페이지 조회 (10명)
curl http://localhost:8000/api/ris/test/patients/

# 두 번째 페이지 조회
curl http://localhost:8000/api/ris/test/patients/?page=2

# 페이지당 5명씩 조회
curl http://localhost:8000/api/ris/test/patients/?page_size=5
```

**예상 응답**:
```json
{
  "success": true,
  "message": "Orthanc 연동 성공",
  "data": {
    "total_patients": 25,
    "current_page": 1,
    "page_size": 10,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false,
    "patients_detail_shown": 10,
    "patients": [
      {
        "patient_id": "abc123...",
        "patient_name": "환자001",
        "patient_birth_date": "19800101",
        "patient_sex": "M",
        "studies": ["study-id-1", "study-id-2"],
        "study_count": 2
      }
    ]
  }
}
```

### 3.4 검사(Study) 목록 조회 테스트

**API 엔드포인트**: `GET http://localhost:8000/api/ris/test/studies/`

**Query Parameters**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10, 최대: 100)

**curl 명령어**:
```bash
# 첫 번째 페이지 조회 (10개)
curl http://localhost:8000/api/ris/test/studies/

# 두 번째 페이지 조회
curl http://localhost:8000/api/ris/test/studies/?page=2

# 페이지당 20개씩 조회
curl http://localhost:8000/api/ris/test/studies/?page_size=20
```

**예상 응답**:
```json
{
  "success": true,
  "message": "Orthanc Study 조회 성공",
  "data": {
    "total_studies": 35,
    "current_page": 1,
    "page_size": 10,
    "total_pages": 4,
    "has_next": true,
    "has_previous": false,
    "studies_detail_shown": 10,
    "studies": [
      {
        "study_id": "study-id-1",
        "study_instance_uid": "1.2.840.113619...",
        "study_date": "20231215",
        "study_time": "143022",
        "study_description": "Brain MRI",
        "modality": "MR",
        "patient_name": "환자001",
        "patient_id": "P001",
        "series": ["series-id-1", "series-id-2"],
        "series_count": 2
      }
    ]
  }
}
```

---

## 4. 문제 해결

### 4.1 Orthanc 서버 연결 실패

**증상**:
```
❌ Orthanc 서버 연결 실패: HTTPConnectionPool...
```

**해결 방법**:
1. Orthanc 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps | findstr orthanc
   ```

2. Orthanc 재시작:
   ```bash
   cd d:\1222\NeuroNova_v1\NeuroNova_02_back_end\03_orthanc_pacs
   docker-compose down
   docker-compose up -d
   ```

3. 방화벽 확인 (포트 8042가 열려 있는지)

### 4.2 DICOM 파일을 찾을 수 없음

**증상**:
```
❌ 디렉토리가 존재하지 않습니다: C:\Users\302-28\Downloads\sub\sub-0004
```

**해결 방법**:
1. 경로가 올바른지 확인
2. 스크립트 내 경로 수정:
   ```python
   PATIENT_DIRECTORIES = [
       r'실제\경로\sub-0004',
       r'실제\경로\sub-0005',
   ]
   ```

### 4.3 업로드는 성공했는데 Django에서 조회 안 됨

**증상**: 업로드는 성공했지만 API 호출 시 `total_patients: 0`

**해결 방법**:
1. Orthanc 웹 UI에서 직접 확인: `http://localhost:8042/app/explorer.html`
2. Django 서버가 올바른 Orthanc URL을 사용하는지 확인:
   ```python
   # settings.py
   ORTHANC_API_URL = 'http://localhost:8042'
   ```

### 4.4 Docker 데이터 영구 저장

**증상**: Docker 컨테이너를 재시작하면 업로드한 DICOM 데이터가 사라짐

**해결 방법**:
1. `docker-compose.yml`에서 named volume 설정 확인:
   ```yaml
   volumes:
     - orthanc-data:/var/lib/orthanc/db
   ```
2. Volume이 정상 생성되었는지 확인:
   ```bash
   docker volume ls | findstr orthanc
   ```

---

## 📚 추가 리소스

- **Orthanc 공식 문서**: https://book.orthanc-server.com/
- **Orthanc REST API**: https://api.orthanc-server.com/
- **DICOM 표준**: https://www.dicomstandard.org/

---

## 🎯 다음 단계

1. **AI 모듈 연동**: 업로드된 DICOM 데이터를 AI 분석 모듈로 전송
2. **자동 동기화**: Orthanc 데이터를 Django DB에 자동 동기화
3. **이미지 뷰어 통합**: DICOM 이미지를 웹에서 볼 수 있도록 뷰어 통합

---

**작성자**: Claude AI
**프로젝트**: NeuroNova CDSS
**문서 버전**: 1.0
