# React + TypeScript + Vite

## TypeScript 선택이유
1. 대규모 협업에서 코드 품질 관리에 유리
2. 라이브러리/프레임워크 대부분이 TS 지원을 우선시함
3. 자동완성 & 타입 체크 → 실수 줄이고 유지보수 쉬워짐

- 작은 팀/빠른 개발 → 그냥 JavaScript + React Router v7
- 중규모 이상/장기 유지보수 → TypeScript + SWC + React Router v7


## 폴더 구조

## types - 공통 타입 지정
├─ types/          # 공통 타입
  ├─  role.ts # TODO : DB에서 Role 어떻게 받아오는지 확인 작업 필요, role 추가시 role.ts 파일에도 추가 필요
  └─menu.ts # TODO : 메뉴가 추가되는 경우 - menu.ts 파일에도 추가 필요

| 변경 내용      | 수정 파일                             |
| ---------- | --------------------------------- |
| 새 화면 추가    | `menu.ts`                         |
| 메뉴 이름 변경   | `MENU_LABEL_BY_ROLE`              |
| 메뉴 위치 변경   | `MENU_CONFIG`                     |
| 접근 Role 변경 | Admin 권한관리 or `MENU_CONFIG.roles` |
| UX만 다름     | Page 내부 Role 분기                   |
