import {api} from '@/services/api';
import type { Role } from "@/types/role";

export const fetchRoles = async (): Promise<Role[]> => {
  const res = await api.get("/auth/roles/");
  return res.data;
};

export const createRole = async (data: {
  code: string;
  name: string;
  description?: string;
}) => {
  return api.post("/auth/roles/", data);
};

export const updateRole = async (
  id: number,
  data: { name: string; description?: string; is_active: boolean }
) => {
  return api.put(`/auth/roles/${id}`, data);
};

export const deleteRole = async (id: number) => {
  return api.delete(`/auth/roles/${id}`);
};
