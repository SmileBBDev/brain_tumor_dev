import { createContext, useContext, useEffect, useState, useRef } from 'react';
import SessionExtendModal from './SessionExtendModal';
import { connectPermissionSocket } from '@/socket/permissionSocket'
import type { MenuNode } from '@/types/menu';
import { fetchMe, fetchMenu } from '../../services/auth.api';
import type { User } from '@/types/user';

interface AuthContextValue {
  user : User | null;
  role: string | null;
  menus: MenuNode[];

  sessionRemain: number;
  isAuthReady: boolean;
  isAuthenticated: boolean;

  logout: () => void;
  refreshAuth: () => Promise<void>;
  hasPermission: (menuId: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);


export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [menus, setMenus] = useState<MenuNode[]>([]);

  const [isAuthReady, setIsAuthReady] = useState(false);
  const [sessionRemain, setSessionRemain] = useState(30 * 60);

   // WebSocket을 저장할 ref
  const wsRef = useRef<WebSocket | null>(null);

  // 내 정보, 메뉴 조회
  const refreshAuth = async () => {
  try {
    const meRes = await fetchMe();
    const menuRes = await fetchMenu();

    setUser(meRes.data);
    setRole(meRes.data.role.code);
    setMenus(menuRes.data.menus);
  } catch (e) {
    logout();
    throw e;
  }
};


  // 앱 최초 1회: 서버 기준 인증 초기화
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setIsAuthReady(true);
        return;
      }

      try {
        await refreshAuth();
      } finally {
        setIsAuthReady(true);
      }

    };

    initAuth();
  }, []);


  const isAuthenticated = !!user;

  
  // WebSocket 연결 (세션 동안 유지)
  useEffect(() => {
    if (!isAuthenticated) return;
    
    // 이미 연결된 WebSocket이 있으면 닫고 새로 연결
    if (wsRef.current) {
      wsRef.current.close();
    }

    wsRef.current = connectPermissionSocket(async () => {
      const menuRes = await fetchMenu();
      setMenus(menuRes.data.menus);
    });
  }, [isAuthenticated]);

  /** ⏱ 세션 타이머 */
  useEffect(() => {
    if (!isAuthenticated) return;

    const timer = setInterval(() => {
      setSessionRemain((prev) => Math.max(prev - 1, 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [isAuthenticated]);

  /** 만료 시 연장 또는 로그아웃 */
  // 로그아웃 처리
  const logout = async () => {
    setUser(null);
    setRole(null);
    setMenus([]);
    await refreshAuth(); // ← 서버 기준 세션 재확인
    setSessionRemain(30 * 60); // 초기값으로 복원
    setHasWarned(false);    
    setShowExtendModal(false);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');

    // WebSocket 닫기
    if (wsRef.current) {
      wsRef.current.close();
    }

  };

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


  const hasPermission = (menuId: string) => {
    const walk = (tree: MenuNode[]): boolean =>
      tree.some(m => m.id === menuId || (m.children && walk(m.children)));

    return walk(menus);
  };

  return (
    <AuthContext.Provider
      value={{ 
        user, role, sessionRemain, 
        logout, isAuthReady, 
        menus,
        isAuthenticated,refreshAuth,
        hasPermission,
      }}
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