import { createContext, useContext, useEffect, useState } from 'react';
import type { Role } from '@/types/role';

interface AuthContextValue {
  role: Role | null;
  setRole: (role: Role | null) => void;
  sessionRemain: number;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [sessionRemain, setSessionRemain] = useState(30 * 60);

  /** 🔁 앱 시작 시 localStorage → state 복원 */
  useEffect(() => {
    const savedRole = localStorage.getItem('role') as Role | null;
    if (savedRole) {
      setRole(savedRole);
    }
  }, []);

  /** ⏱ 세션 타이머 */
  useEffect(() => {
    if (!role) return;

    const timer = setInterval(() => {
      setSessionRemain((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [role]);

  /** ⛔ 만료 시 로그아웃 */
  useEffect(() => {
    if (sessionRemain <= 0) {
      logout();
    }
  }, [sessionRemain]);

  const logout = () => {
    localStorage.clear();
    setRole(null);
    setSessionRemain(0);
  };

  return (
    <AuthContext.Provider
      value={{ role, setRole, sessionRemain, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
