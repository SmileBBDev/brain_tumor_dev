// src/services/admin.permission.ts
import { api } from './api';
import type { MenuNode } from '@/types/menu';
import type { Role } from '@/types/adminManager';

/** Role 목록 조회 */
export async function fetchRoles(): Promise<Role[]> {
  const res = await api.get('/admin/roles/');
  return res.data;
}

/** 전체 메뉴 트리 */
export async function fetchMenuTree(): Promise<MenuNode[]> {
  const res = await api.get('/admin/menus/');
  return res.data;
}

/** 특정 Role의 메뉴 권한 조회 */
export async function fetchRoleMenus(
  roleCode: string
): Promise<number[]> {
  const res = await api.get(`/admin/roles/${roleCode}/menus/`);
  return res.data;
}

/** Role 메뉴 권한 저장 */
export async function saveRoleMenus(
  roleCode: string,
  menuIds: number[]
): Promise<void> {
  await api.put(`/admin/roles/${roleCode}/menus/`, {
    menuIds,
  });
}
