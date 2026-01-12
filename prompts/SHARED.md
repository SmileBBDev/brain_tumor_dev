# 공용 정보

## 프로젝트 구조
```
brain_tumor_dev/
├── brain_tumor_back/    # Django 백엔드 (A 담당)
├── brain_tumor_front/   # React 프론트엔드 (B 담당)
└── prompts/             # 에이전트 프롬프트
```

## 비밀번호 규칙
`{login_id}001`
- system → system001
- doctor1 → doctor1001
- nurse1 → nurse1001

## DB 초기화
```bash
cd brain_tumor_back
python -m setup_dummy_data --reset -y
```
- DB 없으면 자동 생성
- 마이그레이션 자동 실행
- 기존 데이터 삭제 후 재생성

## API 응답 규칙
- 목록 API: 배열 직접 반환 `[{...}, {...}]`
- 프론트엔드: 방어적 처리 `Array.isArray(data) ? data : data?.results || []`

## 역할 (Role)
| 코드 | 설명 |
|------|------|
| SYSTEMMANAGER | 시스템 관리자 (전체 권한) |
| ADMIN | 병원 관리자 |
| DOCTOR | 의사 |
| NURSE | 간호사 |
| RIS | 영상과 |
| LIS | 검사과 |
| PATIENT | 환자 |

## 주요 경로
- `/patients` - 환자 목록
- `/patients/:id` - 환자 상세 (읽기 전용)
- `/patientsCare` - 진료 화면 (DOCTOR, SYSTEMMANAGER만)
- `/encounters` - 진료 예약
