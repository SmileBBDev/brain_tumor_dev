# A (Backend) 작업 지시

## 목표
API 응답 형식을 배열로 통일하고, 오늘 날짜 예약 데이터 추가

## 문제 상황
프론트엔드에서 다음 에러 발생:
```
TypeError: encounterData.slice is not a function
TypeError: appointments is not iterable
```
원인: API가 `{count, results}` 객체를 반환하는데, 프론트엔드는 배열을 기대함

---

## 작업 1: encounters/views.py 수정

### 1.1 `today()` 메서드 수정
**파일**: `apps/encounters/views.py`

현재 (문제):
```python
return Response({
    'count': queryset.count(),
    'date': today.isoformat(),
    'results': serializer.data
})
```

수정 후:
```python
return Response(serializer.data)  # 배열 직접 반환
```

### 1.2 `by_patient()` 메서드 확인
동일하게 배열을 직접 반환하도록 수정

---

## 작업 2: ocs/views.py 확인

### 2.1 환자별 OCS 조회 API 확인
**파일**: `apps/ocs/views.py`

`by_patient()` 또는 유사한 메서드가 있는지 확인하고, 배열을 직접 반환하도록 수정

---

## 작업 3: ai_inference/views.py 확인

### 3.1 환자별 AI 요청 조회 API 확인
**파일**: `apps/ai_inference/views.py`

환자별 조회 메서드가 있는지 확인하고, 배열을 직접 반환하도록 수정

---

## 작업 4: 오늘 날짜 예약 데이터 추가

### 4.1 더미 데이터 수정
**파일**: `setup_dummy_data/setup_dummy_data_1_base.py`

`create_dummy_encounters()` 함수에서 오늘 날짜의 `scheduled` 상태 진료 데이터 추가:

```python
from django.utils import timezone

# 기존 코드 이후에 추가
# 오늘 예약 진료 3건 생성 (테스트용)
print("\n[7-1단계] 오늘 예약 진료 생성...")
for i in range(3):
    Encounter.objects.create(
        patient=random.choice(patients),
        attending_doctor=random.choice(doctors),
        admission_date=timezone.now(),
        status='scheduled',
        encounter_type='outpatient',
        department=random.choice(['neurology', 'neurosurgery']),
        chief_complaint=random.choice(['정기 진료', '추적 검사', '상담'])
    )
print(f"  오늘 예약 진료: 3건 생성")
```

---

## 완료 기준 체크리스트

- [ ] `GET /api/encounters/today/` 가 배열 `[]` 반환
- [ ] `GET /api/encounters/patient/{id}/` 가 배열 `[]` 반환
- [ ] `GET /api/ocs/patient/{id}/` 가 배열 `[]` 반환 (있는 경우)
- [ ] `GET /api/ai/requests/patient/{id}/` 가 배열 `[]` 반환 (있는 경우)
- [ ] 더미 데이터에 오늘 날짜 예약 3건 추가

---

## 테스트 방법

```bash
# 서버 실행
cd brain_tumor_back
python manage.py runserver

# API 테스트 (Swagger 또는 curl)
# 1. 로그인하여 토큰 획득
# 2. /api/encounters/today/ 호출하여 배열 반환 확인
# 3. /api/encounters/patient/1/ 호출하여 배열 반환 확인
```

---

## 주의사항

1. **페이지네이션이 필요한 목록 API는 그대로 유지** (예: `GET /api/encounters/`)
2. **단일 조회용 API만 배열 반환으로 변경** (today, by_patient 등)
3. 수정 후 서버 재시작 필요
