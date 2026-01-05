import { useEffect, useState } from "react";
import type { User } from "@/types/user";
import '@/assets/style/adminPageStyle.css';
import {api} from "@/services/api";

export default function UserListPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [search, setSearch] = useState("");
    const [roleFilter, setRoleFilter] = useState("");

    /* 사용자 목록 조회 api */
    const fetchUsers = async () => {
        const res = await api.get<User[]>("/users/", {
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
        await api.patch(`/users/${id}/toggle-active/`);
        fetchUsers();
    };

    /* 사용자 잠금 해제 */
    const unlockUser = async (id: number) => {
        await api.patch(`/users/${id}/unlock/`);
        fetchUsers();
    };

    // 날짜 포맷 변환
    const formatDate = (dateString : string | null ) => {
        if (!dateString) return "-";
        return new Date(dateString).toLocaleString("ko-KR", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };
    // 최근 5분 이내 로그인 여부
    const isRecentLogin = (lastLogin?: string | null) => {
        if (!lastLogin) return false;
        const last = new Date(lastLogin).getTime();
        const now = Date.now();
        return now - last < 5 * 60 * 1000; // 5분
    };

    return (
    <div className="admin-card">
        {/* Toolbar */}
        <div className="admin-toolbar">
            <div>
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
            </div>

            <button className="primary">사용자 추가</button>
        </div>

        {/* 사용자 리스트 */}
        <table className="admin-table">
            <thead>
            <tr>
                <th>ID</th>
                <th>이름</th>
                <th>역할</th>
                <th>접속 유/무</th>
                <th>최근 로그인</th>
                <th>상태 변경</th>
            </tr>
            </thead>

            <tbody>
            {users.map((user) => (
                <tr key={user.id}>
                    <td>{user.login_id}</td>
                    <td>{user.name}</td>
                    <td>{user.role.name}</td>

                    <td>
                        {user.is_locked ? (
                            <span className="badge danger">잠김</span>
                        ) : (
                            <>
                            {user.is_online ? (
                                <span className="badge online">🟢 접속 중</span>
                            ) : (
                                <span className="badge offline">⚪ 오프라인</span>
                            )}
                            {user.is_active && <span className="badge active">활성</span>}
                            {!user.is_active && <span className="badge inactive">비활성</span>}
                            </>
                        )}
                    </td>
                    <td>
                        {formatDate(user.last_login)}
                    </td>



                    <td>
                    {user.is_locked ? (
                        <button
                        className="danger"
                        onClick={() => unlockUser(user.id)}
                        >
                        잠금 해제
                        </button>
                    ) : (
                        <button
                        className="ghost"
                        onClick={() => toggleActive(user.id)}
                        >
                        {user.is_active ? "비활성화" : "활성화"}
                        </button>
                    )}
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
