import { useEffect, useState } from "react";
import {
  fetchRoles,
  createRole,
  updateRole,
  deleteRole,
} from "@/services/role.api";
import type { Role } from "@/types/role";
import RoleFormModal from "./components/RoleFormModal";

export default function RoleControlPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [open, setOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);

  const load = async () => {
    const data = await fetchRoles();
    setRoles(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (data: any) => {
    if (editingRole) {
      await updateRole(editingRole.id, data);
    } else {
      await createRole(data);
    }
    setOpen(false);
    setEditingRole(null);
    load();
  };

  const handleDelete = async (role: Role) => {
    if (!confirm("이 역할을 비활성화할까요?")) return;
    await deleteRole(role.id);
    load();
  };

  return (
    <div>
      <button onClick={() => setOpen(true)}>+ 역할 생성</button>

      <table>
        <thead>
          <tr>
            <th>역할명</th>
            <th>코드</th>
            <th>상태</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {roles.map((role) => (
            <tr key={role.id}>
              <td>{role.name}</td>
              <td>{role.code}</td>
              <td>{role.is_active ? "활성" : "비활성"}</td>
              <td>
                <button
                  onClick={() => {
                    setEditingRole(role);
                    setOpen(true);
                  }}
                >
                  수정
                </button>
                <button onClick={() => handleDelete(role)}>삭제</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <RoleFormModal
        open={open}
        role={editingRole}
        onClose={() => {
          setOpen(false);
          setEditingRole(null);
        }}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
