import { useLocation } from 'react-router-dom';
import type { Role } from '@/types/role';
import { ROLE_ICON_MAP } from './header.constants';
import { useNavigate } from 'react-router-dom';

interface AppHeaderProps {
  role: Role;
}

const ROLE_LABEL: Record<Role, string> = {
    DOCTOR: 'Doctor',
    NURSE: 'Nurse',
    ADMIN: 'Admin',
    PATIENT: 'Patient',
    LIS : 'LIS',
    RIS : 'RIS',
    SYSTEMMANAGER: 'System Manager',
};

/* 경로 → 메뉴명 매핑 */
const MENU_LABEL_MAP: Record<string, string> = {
  '/patients': '환자관리',
  '/orders': '검사관리',
  '/dashboard': '대시보드',
};

export default function AppHeader({ role }: AppHeaderProps) {
  const location = useLocation();
  const currentMenu = MENU_LABEL_MAP[location.pathname] ?? 'Unknown';
  
  const navigator = useNavigate();
  const isLoggedIn = Boolean(role);

  const handleLogout = () => {
    // 로그아웃 처리 로직 (예: 토큰 삭제, 리다이렉트 등)
    localStorage.removeItem('role');
    localStorage.removeItem('menus');
    navigator('/login');
  }


  return (
    <header className="app-header">
        {/* 현재 메뉴 표시 */}
        <div className="header-left">
            <h1>{currentMenu}</h1>
        </div>

        <div className="header-right">
            <div className="user-info">
            {/* 로그인 사용자 */}
            {isLoggedIn && (
                <>
                    <span className="role">{ROLE_LABEL[role]}</span>
                    <span className="divider">|</span>
                    <span className="userIcon">
                        <i className={`fa-solid ${ROLE_ICON_MAP[role]}`} /> 
                    </span>
                    <span className="divider">|</span>
                        <i className="fa-solid fa-lock"></i>
                    <button className="btn logout-btn"onClick={handleLogout}>로그아웃</button>
                    
                </>
                )
            }
            </div>
        </div>
    </header>
  );
}
