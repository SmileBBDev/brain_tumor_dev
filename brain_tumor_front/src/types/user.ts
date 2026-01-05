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

export interface UserProfileForm {
  name: string;
  birthDate: string;
  phoneMobile: string;
  phoneOffice: string;
  email: string;
  hireDate: string;
  departmentId: string;
  title: string;
}

export interface UserSearchParams {
    search?: string;
    role?: string;
}