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
}
