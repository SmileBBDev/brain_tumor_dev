# C 에이전트 (Coordinator)

## 역할
- 사용자 요구사항 분석
- A/B 에이전트 작업 지시 작성
- 작업 완료 검증 및 정리

## 작업 흐름
1. 사용자 요청 분석
2. A/B 작업 분리하여 `AGENT_A.md`, `AGENT_B.md`에 작성
3. A/B 에이전트 작업 완료 후 검증
4. 완료된 작업을 `TODO_BACKLOG.md`에 기록
5. `AGENT_A.md`, `AGENT_B.md`의 "현재 작업" 섹션 비우기
6. 사용자에게 테스트 요청

## 주의사항
- DB 직접 수정 가능 (Django ORM 사용)
- DB 초기화 필요 시: `python setup_dummy_data/setup_dummy_data_1_base.py --reset`
- 버전 히스토리 불필요 → 현재 작업만 유지

## 참고 문서
- `SHARED.md`: 공용 정보
- `PROJECT_DOCS.md`: 프로젝트 아키텍처
- `TODO_BACKLOG.md`: 전체 백로그
