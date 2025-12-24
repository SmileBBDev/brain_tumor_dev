import { createContext, useContext, useEffect, useState } from 'react';
import type { Role } from '@/types/role';
import SessionExtendModal from './SessionExtendModal';

interface AuthContextValue {
  role: Role | null;
  setRole: (role: Role | null) => void;
  sessionRemain: number;
  logout: () => void;
  isAuthReady: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [sessionRemain, setSessionRemain] = useState(30 * 60);


  /** 앱 시작 시 role 복원 | localStorage → state 복원 */
  useEffect(() => {
    const savedRole = localStorage.getItem('role') as Role | null;
    if (savedRole) {
      setRole(savedRole);
    }
    setIsAuthReady(true);
  }, []);

  /** ⏱ 세션 타이머 */
  useEffect(() => {
    if (!role) {
      setShowExtendModal(false);
      return;
    }

    const timer = setInterval(() => {
      setSessionRemain((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [role]);

  /** 만료 시 연장 또는 로그아웃 */
  // 로그인 후 25분	-> 연장 모달 1회 표시
  // 연장 클릭	세션 30분 리셋 + 다시 25분 후 재등장
  // 무시	만료 시 자동 로그아웃
  // 재로그인	정상 동작
  const WARNING_TIME = 5 * 60; // 5분
  const [showExtendModal, setShowExtendModal] = useState(false);
  const [hasWarned, setHasWarned] = useState(false);

  useEffect(() => {
    if (sessionRemain <= 0) {
      logout();
      return;
    }
    if (sessionRemain <= WARNING_TIME && !hasWarned) {
      setShowExtendModal(true);
      setHasWarned(true);
    }

  }, [sessionRemain]);

  const extendSession = () => {
    setSessionRemain(30 * 60); // 30분 연장
    setHasWarned(false);          
    setShowExtendModal(false);
  };

  // 로그아웃 처리
  const logout = () => {
    localStorage.clear();
    setRole(null);
    setSessionRemain(30 * 60); // 초기값으로 복원
    setHasWarned(false);    
    setShowExtendModal(false);
  };

  return (
    <AuthContext.Provider
      value={{ role, setRole, sessionRemain, logout, isAuthReady }}
    >
      {children}
      {showExtendModal && (
      <SessionExtendModal
        remain={sessionRemain}
        onExtend={extendSession}
        onLogout={logout}
      />
    )}
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
