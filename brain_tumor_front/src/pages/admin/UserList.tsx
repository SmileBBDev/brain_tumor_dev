import { useEffect, useState } from "react";
import axios from 'axios';
import type { User } from "@/types/user";

export default function UserListPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");

  /* 사용자 목록 조회 */
  const fetchUsers = async () => {
    const res = await axios.get<User[]>("/api/users/", {
      params: {
        search: search || undefined,
        role: roleFilter || undefined,
      },
    });
    setUsers(res.data);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  /* 사용자 활성 / 비활성 토글 */
  const toggleActive = async (id: number) => {
    await axios.patch(`/api/users/${id}/toggle-active/`);
    fetchUsers();
  };

  return (
    <div className="admin-card">
      {/* Toolbar */}
      <div className="admin-toolbar">
        <input
          placeholder="사용자명 / ID 검색"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchUsers()}
        />

        {/* Role 필터 */}
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setTimeout(fetchUsers, 0);
          }}
        >
            <option value="">전체 역할</option>
            <option value="ADMIN">관리자</option>
            <option value="DOCTOR">의사</option>
            <option value="NURSE">간호사</option>
            <option value="PATIENT">환자</option>
            <option value="RIS">영상과</option>
            <option value="LIS">검사과</option>
        </select>

        <button className="primary">사용자 추가</button>
      </div>

      {/* 사용자 리스트 */}
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>이름</th>
            <th>역할</th>
            <th>상태</th>
            <th>최근 로그인</th>
            <th></th>
          </tr>
        </thead>

        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.login_id}</td>
              <td>{user.name}</td>
              <td>{user.role.name}</td>

              <td>
                <span
                  className={`badge ${
                    user.is_active ? "active" : "inactive"
                  }`}
                >
                  {user.is_active ? "활성" : "비활성"}
                </span>
              </td>

              <td>{user.last_login ?? "-"}</td>

              <td>
                <button
                  className="ghost"
                  onClick={() => toggleActive(user.id)}
                >
                  {user.is_active ? "비활성화" : "활성화"}
                </button>
              </td>
            </tr>
          ))}

          {users.length === 0 && (
            <tr>
              <td colSpan={6} style={{ textAlign: "center", padding: "20px" }}>
                조회된 사용자가 없습니다.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
