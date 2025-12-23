import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';

// Role별 메뉴 라벨 설정
export const MENU_LABEL_BY_ROLE: Partial<
  Record<MenuId, Partial<Record<Role, string>>>
> = {
  PATIENT_LIST: {
    DOCTOR: '환자 목록',
    NURSE: '환자 관리',
    PATIENT: '내 진료 기록',
    SYSTEMMANAGER: '환자 관리',
  },
};
