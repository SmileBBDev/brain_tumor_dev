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

  DASHBOARD :{
    DOCTOR: '의사 대시보드',
    NURSE: '간호 대시보드',
    LIS: '검사실 대시보드',
    RIS: '영상의학과 대시보드',
    ADMIN: '관리자 대시보드',
    SYSTEMMANAGER: '시스템 대시보드',
  }
};
