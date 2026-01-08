-- 권한 설계 가이드
-- 📌 핵심 원칙 (절대 규칙)
-- menu.code === permission.code
-- 
-- 화면 접근 권한은 무조건 permission 기준
-- menu는 UI 표현용
-- role은 permission 집합

-- MENU / PERMISSION / ROLE 분리
-- menus_menu : UI 트리
-- accounts_permission : 접근 제어
-- menus_menupermission : 메뉴 ↔ 권한 연결
-- accounts_role_permissions : 역할 ↔ 권한 연결

-- 논리 ERD
-- ┌───────────────┐
-- │  accounts_role│
-- │───────────────│
-- │ id            │
-- │ code          │
-- │ name          │
-- └───────┬───────┘
--         │
--         │ 1:N
--         ▼
-- ┌────────────────────────┐
-- │ accounts_role_permissions│
-- │────────────────────────│
-- │ role_id  (FK)           │
-- │ permission_id (FK)      │
-- └────────┬───────────────┘
--          │
--          │ N:1
--          ▼
-- ┌─────────────────────┐
-- │ accounts_permission │
-- │─────────────────────│
-- │ id                  │
-- │ code (UNIQUE)       │◀──────────────┐
-- │ name                │               │
-- └─────────┬───────────┘               │
--           │                           │
--           │ 1:N                       │ 1:1 (논리)
--           ▼                           │
-- ┌─────────────────────┐               │
-- │ menus_menupermission│               │
-- │─────────────────────│               │
-- │ menu_id (FK)        │───────────────┘
-- │ permission_id (FK)  │
-- └─────────┬───────────┘
--           │
--           │ N:1
--           ▼
-- ┌─────────────────────┐
-- │     menus_menu      │
-- │─────────────────────│
-- │ id                  │
-- │ code (UNIQUE)       │
-- │ path                │
-- │ parent_id (self FK) │
-- │ breadcrumb_only     │
-- └─────────────────────┘

INSERT INTO brain_tumor.accounts_role (code,name,description,is_active,created_at,updated_at) VALUES
	 ('SYSTEMMANAGER','System Manager','시스템 관리자',1,'2025-12-30 13:13:19','2026-01-07 10:28:46.959361'),
	 ('ADMIN','Admin','병원 관리자',1,'2025-12-30 13:13:23','2026-01-07 10:28:46.959361'),
	 ('DOCTOR','Doctor','의사',1,'2025-12-30 13:13:25','2026-01-07 10:28:46.959361'),
	 ('NURSE','nurse','간호사',1,'2025-12-30 14:28:15','2026-01-07 10:28:46.959361'),
	 ('PATIENT','Patient','환자',1,'2025-12-30 14:28:16','2026-01-07 10:28:46.959361'),
	 ('RIS','Ris','영상과',1,'2025-12-30 14:28:17','2026-01-07 10:28:46.959361'),
	 ('LIS','Lis','검사과',1,'2025-12-30 14:28:19','2026-01-07 10:28:46.959361'),
	 ('','test','',1,'2026-01-07 17:03:55.239054','2026-01-07 17:03:55.239054');

INSERT INTO brain_tumor.accounts_user (password,last_login,is_superuser,login_id,must_change_password,name,email,is_active,is_staff,created_at,updated_at,failed_login_count,is_locked,locked_at,last_login_ip,last_seen,role_id) VALUES
	 ('pbkdf2_sha256$1000000$40jR2KPPgb6CVEOVStAoFF$Ghkqw9I6bIqfCa/Sz1pjRja6yybF7/MUBsUoLH6+u3o=','2026-01-08 03:42:58.331389',1,'system',0,'시스템관리자',NULL,1,1,'2026-01-01 14:52:40','2026-01-05 11:35:04.277220',0,0,NULL,'127.0.0.1','2026-01-08 03:44:30.271733',1),
	 ('pbkdf2_sha256$1000000$VXDBF97JI7re4z92oqAfas$9UmkStg2/S9hmRNJccAD8ZY8CY/k9xn4ATNQIwcPVhM=','2026-01-08 03:42:40.923626',0,'admin',0,'병원관리자',NULL,1,1,'2026-01-01 14:53:00','2026-01-05 07:43:50.226316',0,0,NULL,'127.0.0.1','2026-01-08 03:42:51.345209',2),
	 ('pbkdf2_sha256$1000000$aoXSw3HNA9xMMHKwa6b8l5$EDPcdHj4KKoOxhyvROxkVJ9lAedSmzHIieJS19TZ6X4=','2026-01-08 02:21:27.106851',0,'doctor1',0,'의사',NULL,1,0,'2026-01-01 14:53:20','2026-01-05 03:56:46.276092',0,0,NULL,'127.0.0.1','2026-01-08 02:21:38.250613',3),
	 ('pbkdf2_sha256$1000000$KwHiBggUTZxQmEUxpsjaMR$+Fu0oSV1eSlgviQy6OHxcKf5hY6zpz44ok0L/M1//r8=','2026-01-08 03:26:38.289840',0,'nurse1',0,'간호사',NULL,1,0,'2026-01-01 14:53:40','2026-01-05 06:22:38.705151',0,0,NULL,'127.0.0.1','2026-01-08 03:26:56.828156',4),
	 ('pbkdf2_sha256$1000000$QQRaodY6S1alpJyrTh4LxU$FnijGoCMJDkC3OtCLpg1dTB4GZXcQhyloP8C6kxmUUo=','2026-01-08 02:21:49.856486',0,'patient1',0,'환자',NULL,1,0,'2026-01-01 14:54:00','2026-01-05 03:56:43.171526',0,0,NULL,'127.0.0.1','2026-01-08 02:22:21.512186',5),
	 ('pbkdf2_sha256$1000000$YYqLmKU6QSu3DQrNYQiAeg$iJ29dcvWFNV5814Ev9bMv0nRlTHGb+lNHMlcCOB1tS0=','2026-01-08 03:27:15.418162',0,'ris1',0,'영상과',NULL,1,0,'2026-01-01 14:54:20','2026-01-01 14:54:20',0,0,NULL,'127.0.0.1','2026-01-08 03:42:40.977779',6),
	 ('pbkdf2_sha256$1000000$L0n2ssUSf1HeSi7HUXjQmA$07tvL6Uiis2stIXpfYahxZ3pqee7YirfEVTgaBnQX44=','2026-01-08 02:06:33.629980',0,'lis1',0,'검사과',NULL,1,0,'2026-01-01 14:54:40','2026-01-01 14:54:40',0,0,NULL,'127.0.0.1','2026-01-08 02:08:49.314178',7),
	 ('pbkdf2_sha256$1000000$O6lDmrrZ5hDveOOMewl0Qj$YzuMWaP9bns6R5021kJpMEJ2l7s8lu5S0yRt50OtCCo=',NULL,0,'honggildong260106',0,'홍길동','ddde@gmail.com',1,0,'2026-01-06 02:15:40.058085','2026-01-06 02:15:40.058085',0,0,NULL,NULL,NULL,3),
	 ('pbkdf2_sha256$1000000$TRuzfH9uJ0SuD50UPaTDmv$asoufrDCZC04t4zCyjoERE3jDJa7CIxivkA9HbfaroY=','2026-01-06 02:23:32.447782',0,'simgangyeon230510',0,'심강연','erer03@gmail.com',1,0,'2026-01-06 02:22:50.639705','2026-01-06 02:22:50.639705',0,0,NULL,'127.0.0.1','2026-01-06 02:24:02.375558',6),
	 ('pbkdf2_sha256$1000000$ZkfjGgPofwoaiHCCymwitm$jbkM3M0mHtqY0C5FpVpSUP6F08hvBYbz+CjgUbO9iHo=','2026-01-06 03:48:33.121677',0,'iii250220',1,'이이이','dtp03137@gmail.com',1,0,'2026-01-06 03:48:04.762311','2026-01-06 03:48:04.762311',0,0,NULL,'127.0.0.1','2026-01-06 03:53:52.309054',3);
INSERT INTO brain_tumor.accounts_user (password,last_login,is_superuser,login_id,must_change_password,name,email,is_active,is_staff,created_at,updated_at,failed_login_count,is_locked,locked_at,last_login_ip,last_seen,role_id) VALUES
	 ('pbkdf2_sha256$1000000$H6eahgl6bebR3GTekk6II4$nfS7B0wnfRvgQiH0Gi1nH3iBA54m+PkbhcA8h/pna7Y=','2026-01-06 05:56:54.325110',0,'gimbyeonho120229',1,'김변호','dtp03137@gmail.com',1,0,'2026-01-06 03:54:54.496152','2026-01-06 03:54:54.496152',0,0,NULL,'127.0.0.1','2026-01-06 06:14:57.973280',4);



-- 안전 초기화 (선택)
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE menus_menupermission;
TRUNCATE TABLE accounts_role_permissions;
TRUNCATE TABLE menus_menu;
TRUNCATE TABLE accounts_permission;

SET FOREIGN_KEY_CHECKS = 1;


-- 메뉴 / 권한 Seed (초기화 스크립트)
-- 1. MENU Seed
-- 최상위 메뉴
INSERT INTO menus_menu
(id, code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
VALUES
(1, 'ADMIN', NULL, 'settings', NULL, 0, 7, 1, NULL),
(2, 'AI_SUMMARY', '/ai', 'brain', NULL, 0, 5, 1, NULL),
(3, 'DASHBOARD', '/dashboard', 'home', NULL, 0, 1, 1, NULL),
(4, 'IMAGING', NULL, NULL, '영상', 0, 4, 1, NULL),
(5, 'LAB', NULL, NULL, '검사', 0, 6, 1, NULL),
(6, 'ORDER', NULL, NULL, '검사 오더', 0, 3, 1, NULL),
(7, 'PATIENT', NULL, NULL, '환자', 0, 2, 1, NULL);

-- Admin 하위
INSERT INTO menus_menu VALUES
(8,  'ADMIN_AUDIT_LOG',        '/admin/audit',        NULL, NULL, 0, 4, 1, 1),
(9,  'ADMIN_MENU_PERMISSION',  '/admin/permissions',  NULL, NULL, 0, 3, 1, 1),
(10, 'ADMIN_ROLE',             '/admin/roles',        NULL, NULL, 0, 2, 1, 1),
(11, 'ADMIN_SYSTEM_MONITOR',   '/admin/monitor',      NULL, NULL, 0, 5, 1, 1),
(12, 'ADMIN_USER',             '/admin/users',        NULL, NULL, 0, 1, 1, 1),
(13, 'ADMIN_USER_DETAIL',      '/admin/users/:id',    NULL, NULL, 1, 1, 1, 12);

-- Imaging 하위
INSERT INTO menus_menu VALUES
(14, 'IMAGE_VIEWER', '/imaging',       'image', NULL, 0, 1, 1, 4),
(15, 'RIS_WORKLIST', '/ris/worklist',  'x-ray', NULL, 0, 2, 1, 4);

-- LAB 하위
INSERT INTO menus_menu VALUES
(16, 'LAB_RESULT_UPLOAD', '/lab/upload', NULL, NULL, 1, 2, 1, 5),
(17, 'LAB_RESULT_VIEW',   '/lab',        'book', NULL, 0, 1, 1, 5);


-- ORDER 하위
INSERT INTO menus_menu VALUES
(18, 'ORDER_CREATE', '/orders/create', NULL, NULL, 1, 2, 1, 6),
(19, 'ORDER_LIST',   '/orders/list',   'clipboard', NULL, 0, 1, 1, 6);

-- PATIENT 하위
INSERT INTO menus_menu VALUES
(20, 'PATIENT_LIST',   '/patients',              NULL, NULL, 0, 1, 1, 7),
(21, 'PATIENT_DETAIL', '/patients/:patientId',   NULL, NULL, 1, 1, 1, 20);



-- 2. PERMISSION Seed
-- 공통 / 대시보드
INSERT INTO accounts_permission (code, name, description) VALUES
('DASHBOARD', '대시보드', '대시보드 화면 접근');

-- 환자 (PATIENT)
INSERT INTO accounts_permission (code, name, description) VALUES
('PATIENT', '환자', '환자 메뉴'),
('PATIENT_LIST', '환자 목록', '환자 목록 화면'),
('PATIENT_DETAIL', '환자 상세', '환자 상세 화면');

-- 검사 오더(ORDER)
INSERT INTO accounts_permission (code, name, description) VALUES
('ORDER', '검사 오더', '검사 오더 메뉴 '),
('ORDER_LIST', '오더 목록', '검사 오더 목록 화면'),
('ORDER_CREATE', '오더 생성', '검사 오더 생성 화면');

-- 영상(IMAGIMG)
INSERT INTO accounts_permission (code, name, description) VALUES
('IMAGING', '영상', '영상 메뉴'),
('IMAGE_VIEWER', '영상 조회', '영상 조회 화면'),
('RIS_WORKLIST', '판독 Worklist', 'RIS 판독 Worklist 화면');

-- 검사(LIS)
INSERT INTO accounts_permission (code, name, description) VALUES
('LAB', '검사', '검사 메뉴'),
('LAB_RESULT_VIEW', '검사 결과 조회', '검사 결과 조회 화면'),
('LAB_RESULT_UPLOAD', '검사 결과 업로드', '검사 결과 업로드 화면');

-- AI
INSERT INTO accounts_permission (code, name, description) VALUES
('AI_SUMMARY', 'AI 분석 요약', 'AI 분석 요약 화면');


-- 관지라 (ADMIN)
INSERT INTO accounts_permission (code, name, description) VALUES
('ADMIN', '관리자', '관리자 메뉴'),
('ADMIN_USER', '사용자 관리', '사용자 관리 화면'),
('ADMIN_USER_DETAIL', '사용자 관리 상세', '사용자 상세 화면'),
('ADMIN_ROLE', '역할 관리', '역할 관리 화면'),
('ADMIN_MENU_PERMISSION', '메뉴 권한 관리', '메뉴 권한 관리 화면'),
('ADMIN_AUDIT_LOG', '접근 감사 로그', '접근 감사 로그 화면'),
('ADMIN_SYSTEM_MONITOR', '시스템 모니터링', '시스템 모니터링 화면');



-- 3. MENU ↔ PERMISSION 자동 매핑
INSERT IGNORE INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id
FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.path IS NOT NULL
  AND m.breadcrumb_only = 0;

-- 4. ROLE ↔ PERMISSION
-- 역할별 메뉴 접근 권한 부여
-- SYSTEMMANAGER : 모든 권한
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
CROSS JOIN accounts_permission p
WHERE r.code = 'SYSTEMMANAGER';

-- ADMIN (병원 관리자) — 제한된 전체 관리
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE r.code = 'ADMIN'
AND p.code IN (
  'DASHBOARD',
  'PATIENT','PATIENT_LIST','PATIENT_DETAIL',
  'ORDER','ORDER_LIST','ORDER_CREATE',
  'IMAGING','IMAGE_VIEWER','RIS_WORKLIST',
  'LAB','LAB_RESULT_VIEW','LAB_RESULT_UPLOAD',
  'AI_SUMMARY',
  'ADMIN','ADMIN_USER','ADMIN_USER_DETAIL',
  'ADMIN_ROLE','ADMIN_MENU_PERMISSION',
  'ADMIN_AUDIT_LOG'
);

-- 의사
INSERT INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p ON p.code IN (
  'DASHBOARD',
  'PATIENT_LIST',
  'PATIENT_DETAIL',
  'ORDER_LIST',
  'IMAGE_VIEWER',
  'RIS_WORKLIST'
)
WHERE r.code = 'DOCTOR';

-- 간호사
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE r.code = 'NURSE'
  AND p.code IN (
    'DASHBOARD',
    'PATIENT_LIST',
    'PATIENT_DETAIL',
    'ORDER_LIST',
    'IMAGE_VIEWER',
    'LAB_RESULT_VIEW'
  );

-- RIS(영상과)
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE r.code = 'RIS'
  AND p.code IN (
    'DASHBOARD',
    'IMAGE_VIEWER',
    'RIS_WORKLIST'
  );

-- LIS(검사과)
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE r.code = 'LIS'
  AND p.code IN (
    'DASHBOARD',
    'LAB_RESULT_VIEW',
    'LAB_RESULT_UPLOAD'
  );



-- 최정 검증 쿼리 -> 0 row 나와야 함.
SELECT m.code, p.code
FROM menus_menu m
JOIN menus_menupermission mp ON mp.menu_id = m.id
JOIN accounts_permission p ON p.id = mp.permission_id
WHERE m.code != p.code;

-- role 별 권한 수 확인
SELECT r.code, COUNT(*) 
FROM accounts_role_permissions rp
JOIN accounts_role r ON r.id = rp.role_id
GROUP BY r.code;


-- -- 메뉴를 삭제 해야 되는 경우
-- -- 1. ROLE ↔ PERMISSION
-- DELETE rp
-- FROM accounts_role_permissions rp
-- JOIN accounts_permission p ON p.id = rp.permission_id
-- WHERE p.code = 'ADMIN_SYSTEM_MONITOR';
-- 
-- -- 2. MENU ↔ PERMISSION
-- DELETE mp
-- FROM menus_menupermission mp
-- JOIN menus_menu m ON m.id = mp.menu_id
-- WHERE m.code = 'ADMIN_SYSTEM_MONITOR';
-- 
-- -- 3. PERMISSION
-- DELETE FROM accounts_permission
-- WHERE code = 'ADMIN_SYSTEM_MONITOR';
-- 
-- -- 4. MENU
-- DELETE FROM menus_menu
-- WHERE code = 'ADMIN_SYSTEM_MONITOR';


INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','대시보드',3),
	 ('DOCTOR','의사 대시보드',3),
	 ('NURSE','간호 대시보드',3),
	 ('DEFAULT','환자',7),
	 ('DEFAULT','환자 목록',20),
	 ('DEFAULT','환자 상세',21),
	 ('DEFAULT','검사 오더',6),
	 ('DOCTOR','검사 오더',6),
	 ('NURSE','검사 현황',6),
	 ('DEFAULT','오더 목록',19);
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','오더 생성',18),
	 ('DEFAULT','영상',4),
	 ('DEFAULT','영상 조회',14),
	 ('DEFAULT','판독 Worklist',15),
	 ('DEFAULT','AI 분석 요약',2),
	 ('DEFAULT','검사',5),
	 ('DEFAULT','검사 결과 조회',17),
	 ('DEFAULT','검사 결과 업로드',16),
	 ('DEFAULT','관리자',1),
	 ('DEFAULT','사용자 관리',12);
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','역할 권한 관리',10),
	 ('DEFAULT','메뉴 권한 관리',9),
	 ('DEFAULT','접근 감사 로그',8),
	 ('DEFAULT','시스템 모니터링',11),
	 ('DEFAULT','사용자 관리 상세조회',13),
	 ('DEFAULT','오더 생성',18),
	 ('DEFAULT','영상',4),
	 ('DEFAULT','영상 조회',14),
	 ('DEFAULT','판독 Worklist',15),
	 ('DEFAULT','AI 분석 요약',2);
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','검사',5),
	 ('DEFAULT','검사 결과 조회',17),
	 ('DEFAULT','검사 결과 업로드',16),
	 ('DEFAULT','관리자',1),
	 ('DEFAULT','사용자 관리',12),
	 ('DEFAULT','역할 권한 관리',10),
	 ('DEFAULT','메뉴 권한 관리',9),
	 ('DEFAULT','접근 감사 로그',8),
	 ('DEFAULT','시스템 모니터링',11),
	 ('DEFAULT','사용자 관리 상세조회',13);
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','사용자 관리 상세조회',13),
	 ('DEFAULT','대시보드',3),
	 ('DOCTOR','의사 대시보드',3),
	 ('NURSE','간호 대시보드',3),
	 ('DEFAULT','환자',7),
	 ('DEFAULT','환자 목록',20),
	 ('DEFAULT','환자 상세',21),
	 ('DEFAULT','검사 오더',6),
	 ('DOCTOR','검사 오더',6),
	 ('NURSE','검사 현황',6);
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','오더 목록',19);



-- PATIENT 하위 "진료" 메뉴 추가
INSERT INTO menus_menu
(id, code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
VALUES
(22, 'PATIENT_CARE', '/patients/care', NULL, NULL, 0, 2, 1, 7);


-- 환자 진료 권한
INSERT INTO accounts_permission (code, name, description)
VALUES
('PATIENT_CARE', '환자 진료', '환자 진료 화면 접근');

-- MENU ↔ PERMISSION 매핑
INSERT IGNORE INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id
FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.code = 'PATIENT_CARE';


-- ROLE ↔ PERMISSION 매핑
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code = 'PATIENT_CARE'
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'DOCTOR', 'NURSE');

INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	 ('DEFAULT','환자 진료',22);


-- =============================================================================
-- OCS (Order Communication System) 역할별 메뉴 추가
-- =============================================================================
-- OCS_ORDER: 의사용 검사 오더 생성/관리
-- OCS_RIS: RIS 작업자용 영상 워크리스트
-- OCS_LIS: LIS 작업자용 검사 워크리스트
-- =============================================================================

-- 1. 메뉴 추가 (ORDER 그룹 하위, parent_id=6)
INSERT INTO menus_menu
(id, code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
VALUES
(23, 'OCS_ORDER', '/ocs/order', 'file-medical', NULL, 0, 3, 1, 6),
(24, 'OCS_RIS', '/ocs/ris', 'x-ray', NULL, 0, 4, 1, 6),
(25, 'OCS_LIS', '/ocs/lis', 'flask', NULL, 0, 5, 1, 6);

-- 2. 권한 추가
INSERT INTO accounts_permission (code, name, description)
VALUES
('OCS_ORDER', '검사 오더', '의사용 검사 오더 생성/관리'),
('OCS_RIS', '영상 워크리스트', 'RIS 작업자용 영상 오더 처리'),
('OCS_LIS', '검사 워크리스트', 'LIS 작업자용 검사 오더 처리');

-- 3. MENU ↔ PERMISSION 매핑
INSERT IGNORE INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id
FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.code IN ('OCS_ORDER', 'OCS_RIS', 'OCS_LIS');

-- 4. ROLE ↔ PERMISSION 매핑
-- OCS_ORDER: 의사용
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code = 'OCS_ORDER'
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'DOCTOR');

-- OCS_RIS: 영상의학과용
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code = 'OCS_RIS'
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'RIS');

-- OCS_LIS: 검사실용
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code = 'OCS_LIS'
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'LIS');

-- 5. 메뉴 라벨 추가
INSERT INTO brain_tumor.menus_menulabel (`role`,`text`,menu_id) VALUES
	('DEFAULT', '검사 오더', 23),
	('DEFAULT', '영상 워크리스트', 24),
	('DEFAULT', '검사 워크리스트', 25);

