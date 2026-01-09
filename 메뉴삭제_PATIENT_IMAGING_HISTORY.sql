-- 환자별 영상 히스토리 메뉴 삭제 스크립트
-- 실행 전 백업 권장

-- 1. 역할-메뉴 권한 삭제
DELETE FROM menus_rolemenu
WHERE menu_id IN (SELECT id FROM menus_menu WHERE code = 'PATIENT_IMAGING_HISTORY');

-- 2. 메뉴 번역 삭제
DELETE FROM menus_menutranslation
WHERE menu_id IN (SELECT id FROM menus_menu WHERE code = 'PATIENT_IMAGING_HISTORY');

-- 3. 메뉴 삭제
DELETE FROM menus_menu WHERE code = 'PATIENT_IMAGING_HISTORY';

-- 확인
SELECT * FROM menus_menu WHERE code = 'PATIENT_IMAGING_HISTORY';
