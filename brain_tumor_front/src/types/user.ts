export interface User {
    id: number;
    login_id: string;
    name: string;
    role: {
    code: string;
    name: string;
    };
    is_active: boolean;
    last_login: string | null;

    is_locked: boolean;
    failed_login_count: number;
    locked_at: string | null; // 계정 잠금 시각
    is_online: boolean;        // 현재 접속 중
}
