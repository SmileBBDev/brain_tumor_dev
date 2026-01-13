# 공용 정보

## 프로젝트 구조
```
brain_tumor_dev/
├── brain_tumor_back/    # Django 백엔드 (A 담당)
├── brain_tumor_front/   # React 프론트엔드 (B 담당)
└── prompts/             # 에이전트 프롬프트
    ├── SHARED.md        # 공용 정보 (이 파일)
    ├── AGENT_A.md       # A 작업 지시
    ├── AGENT_B.md       # B 작업 지시
    ├── PROJECT_DOCS.md  # 프로젝트 아키텍처
    └── TODO_BACKLOG.md  # 미완료 작업
```

## 비밀번호 규칙
`{login_id}001`
- system → system001
- doctor1 → doctor1001
- nurse1 → nurse1001
- ris1 → ris1001
- lis1 → lis1001

## DB 초기화
```bash
cd brain_tumor_back
python setup_dummy_data/setup_dummy_data_1_base.py --reset
```

## 용어 통일 (2026-01-12)
- 담당자 → **작업자**
- 처방의사/의사 → **요청의사**

## OCS 상태 흐름
```
ORDERED → ACCEPTED → IN_PROGRESS → RESULT_READY → CONFIRMED
                                              └→ CANCELLED
```

## 주요 경로
| 경로 | 설명 |
|------|------|
| `/patients` | 환자 목록 |
| `/patients/:id` | 환자 상세 (읽기 전용) |
| `/patientsCare` | 진료 화면 (DOCTOR, SYSTEMMANAGER) |
| `/encounters` | 진료 목록 |
| `/ocs/manage` | OCS 관리 (의사용) |
| `/ocs/ris` | RIS Worklist |
| `/ocs/ris/process-status` | RIS 전체 현황 |
| `/ocs/lis` | LIS Worklist |
| `/ocs/lis/process-status` | LIS 전체 현황 |
| `/nurse/reception` | 간호사 접수 |

## 역할 (Role)
| 코드 | 설명 | 주요 메뉴 |
|------|------|----------|
| SYSTEMMANAGER | 시스템 관리자 | 전체 |
| ADMIN | 병원 관리자 | 관리 메뉴 |
| DOCTOR | 의사 | 환자, 진료, OCS 생성 |
| NURSE | 간호사 | 환자, 접수 |
| RIS | 영상과 | RIS Worklist |
| LIS | 검사과 | LIS Worklist |
| PATIENT | 환자 | 환자 포털 |

## API 규칙
- 목록 API: 페이지네이션 `{ count, results: [...] }`
- 프론트엔드 방어적 처리: `Array.isArray(data) ? data : data?.results || []`

## CSS 변수 (variables.css)
```css
--card-bg: #ffffff;       /* 카드 배경 */
--text-main: #1f2937;     /* 주 텍스트 */
--text-sub: #6b7280;      /* 부 텍스트 */
--bg-main: #f4f6f9;       /* 메인 배경 */
--border: #e5e7eb;        /* 테두리 */
--primary: #5b6fd6;       /* 주 색상 */
--success: #5fb3a2;       /* 성공 */
--warning: #f2a65a;       /* 경고 */
--danger: #e56b6f;        /* 위험 */
--info: #5b8def;          /* 정보 */
```
