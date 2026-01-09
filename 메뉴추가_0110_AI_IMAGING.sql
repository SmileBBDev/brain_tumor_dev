-- =============================================================================
-- 2026-01-10 메뉴 추가: AI 추론 관리, 환자별 영상 히스토리
-- =============================================================================

-- =============================================================================
-- 1. AI 추론 관리 메뉴 추가 (AI 그룹 하위)
-- =============================================================================

-- AI 그룹 메뉴를 상위 메뉴로 변경 (path 제거, parent 없음)
UPDATE menus_menu
SET path = NULL, group_label = 'AI 분석'
WHERE code = 'AI_SUMMARY';

-- AI 하위 메뉴 추가
INSERT INTO menus_menu
(code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
SELECT 'AI_REQUEST_LIST', '/ai/requests', NULL, NULL, 0, 2, 1, m.id
FROM menus_menu m WHERE m.code = 'AI_SUMMARY';

INSERT INTO menus_menu
(code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
SELECT 'AI_REQUEST_CREATE', '/ai/requests/create', NULL, NULL, 1, 3, 1,
(SELECT id FROM menus_menu WHERE code = 'AI_REQUEST_LIST');

INSERT INTO menus_menu
(code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
SELECT 'AI_REQUEST_DETAIL', '/ai/requests/:id', NULL, NULL, 1, 4, 1,
(SELECT id FROM menus_menu WHERE code = 'AI_REQUEST_LIST');

-- AI 추론 권한 추가
INSERT INTO accounts_permission (code, name, description)
VALUES
('AI_REQUEST_LIST', 'AI 분석 요청 목록', 'AI 분석 요청 목록 화면'),
('AI_REQUEST_CREATE', 'AI 분석 요청 생성', 'AI 분석 요청 생성 화면'),
('AI_REQUEST_DETAIL', 'AI 분석 요청 상세', 'AI 분석 요청 상세 화면');

-- MENU ↔ PERMISSION 매핑
INSERT IGNORE INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id
FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.code IN ('AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL');

-- ROLE ↔ PERMISSION 매핑
-- SYSTEMMANAGER, ADMIN, DOCTOR에게 AI 분석 요청 권한 부여
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code IN ('AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL')
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'DOCTOR');

-- 메뉴 라벨 추가
INSERT INTO menus_menulabel (`role`, `text`, menu_id)
SELECT 'DEFAULT', 'AI 분석 요청', m.id
FROM menus_menu m WHERE m.code = 'AI_REQUEST_LIST';

INSERT INTO menus_menulabel (`role`, `text`, menu_id)
SELECT 'DEFAULT', 'AI 분석 요청 생성', m.id
FROM menus_menu m WHERE m.code = 'AI_REQUEST_CREATE';

INSERT INTO menus_menulabel (`role`, `text`, menu_id)
SELECT 'DEFAULT', 'AI 분석 요청 상세', m.id
FROM menus_menu m WHERE m.code = 'AI_REQUEST_DETAIL';

-- =============================================================================
-- 2. 환자별 영상 히스토리 메뉴 추가 (IMAGING 그룹 하위)
-- =============================================================================

INSERT INTO menus_menu
(code, path, icon, group_label, breadcrumb_only, `order`, is_active, parent_id)
SELECT 'PATIENT_IMAGING_HISTORY', '/imaging/patient-history', NULL, NULL, 0, 2, 1, m.id
FROM menus_menu m WHERE m.code = 'IMAGING';

-- 환자 영상 히스토리 권한 추가
INSERT INTO accounts_permission (code, name, description)
VALUES
('PATIENT_IMAGING_HISTORY', '환자별 영상 히스토리', '환자별 영상 검사 이력 화면');

-- MENU ↔ PERMISSION 매핑
INSERT IGNORE INTO menus_menupermission (menu_id, permission_id)
SELECT m.id, p.id
FROM menus_menu m
JOIN accounts_permission p ON m.code = p.code
WHERE m.code = 'PATIENT_IMAGING_HISTORY';

-- ROLE ↔ PERMISSION 매핑
-- SYSTEMMANAGER, ADMIN, DOCTOR, NURSE, RIS에게 환자 영상 히스토리 권한 부여
INSERT IGNORE INTO accounts_role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM accounts_role r
JOIN accounts_permission p
WHERE p.code = 'PATIENT_IMAGING_HISTORY'
  AND r.code IN ('SYSTEMMANAGER', 'ADMIN', 'DOCTOR', 'NURSE', 'RIS');

-- 메뉴 라벨 추가
INSERT INTO menus_menulabel (`role`, `text`, menu_id)
SELECT 'DEFAULT', '환자별 영상 히스토리', m.id
FROM menus_menu m WHERE m.code = 'PATIENT_IMAGING_HISTORY';


-- =============================================================================
-- 검증 쿼리
-- =============================================================================

-- 추가된 메뉴 확인
SELECT code, path, parent_id, breadcrumb_only, is_active
FROM menus_menu
WHERE code IN ('AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL', 'PATIENT_IMAGING_HISTORY');

-- 추가된 권한 확인
SELECT code, name FROM accounts_permission
WHERE code IN ('AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL', 'PATIENT_IMAGING_HISTORY');

-- 역할별 새 권한 확인
SELECT r.code as role_code, p.code as permission_code
FROM accounts_role_permissions rp
JOIN accounts_role r ON r.id = rp.role_id
JOIN accounts_permission p ON p.id = rp.permission_id
WHERE p.code IN ('AI_REQUEST_LIST', 'AI_REQUEST_CREATE', 'AI_REQUEST_DETAIL', 'PATIENT_IMAGING_HISTORY')
ORDER BY r.code, p.code;
