import { createContext, useContext, useEffect, useState } from 'react';
import type { Role } from '@/types/role';
import SessionExtendModal from './SessionExtendModal';
import type { MenuId } from '@/types/menu';
import { connectPermissionSocket } from '@/socket/permissionSocket'

export interface MenuNode {
  id: string;
  label: string;
  path?: string;
  children?: MenuNode[];
}

interface AuthContextValue {
  role: Role | null;
  // setRole: (role: Role | null) => void;
  sessionRemain: number;
  logout: () => void;
  isAuthReady: boolean;
  // menus : MenuId[];
  // setMenus : (menus : MenuId[]) => void;
  menus: MenuNode[];
  // setMenus: (menus: MenuNode[]) => void;

  setAuth: (payload: {
    role: Role;
    menus: MenuNode[];
  }) => void;

}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [menus, setMenus] = useState<MenuNode[]>([]);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [sessionRemain, setSessionRemain] = useState(30 * 60);

  // 로그인 후 메뉴 로딩 호출

  /** 로그인 성공 시 단일 진입점 */
  const setAuth = ({role, menus,}: {
    role: Role;
    menus: MenuNode[];
  }) => {
    setRole(role);
    setMenus(menus);
    setIsAuthReady(true);
  };


  /** 앱 시작 시 role과 메뉴 복원 | localStorage → state 복원 */
  useEffect(() => {
    const role = localStorage.getItem('role') as Role | null;
    const menus = JSON.parse(localStorage.getItem('menus') || '[]');

    if (role) {
      // setRole(savedRole);
      setAuth({ role, menus });
    }
    setIsAuthReady(true);
  }, []);

  // WebSocket 메뉴 갱신
  useEffect(() => {
    const ws = connectPermissionSocket(() => {
      fetch('/api/menus')
        .then(res => res.json())
        .then(setMenus);
    });

    return () => ws.close();
  }, []);


  /** ⏱ 세션 타이머 */
  useEffect(() => {
    if (!role) {
      setShowExtendModal(false);
      return;
    }

    const timer = setInterval(() => {
      setSessionRemain((prev) => Math.max(prev - 1, 0));
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
    setMenus([]);
    setSessionRemain(30 * 60); // 초기값으로 복원
    setHasWarned(false);    
    setShowExtendModal(false);
  };


  // 권한 변경 시 Sidebar 메뉴 변경
  // const [menus, setMenus] = useState<MenuId[]>([]);
  // useEffect(() => {
  //   const savedNewMenu = JSON.parse(
  //     localStorage.getItem('menus')  || '[]'
  //   );
  //   setMenus(savedNewMenu);
  // }, []); 
  return (
    <AuthContext.Provider
      value={{ role, sessionRemain, logout, isAuthReady, menus, setAuth }}
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

// Context를 안전하게 가져오는 훅
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
