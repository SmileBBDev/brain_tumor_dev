import { useLocation, useNavigate } from 'react-router-dom';
import type { Role } from '@/types/role';
import { ROLE_ICON_MAP } from './header.constants';
import { useAuth } from '@/pages/auth/AuthProvider';
import brainIcon from '@/assets/icon/mri-brain.png';

interface AppHeaderProps {
  role: Role;
  onToggleSidebar: () => void;
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

/* 초 → mm:ss */
function formatTime(sec: number) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function AppHeader({ role, onToggleSidebar }: AppHeaderProps) {
  const location = useLocation();
  const currentMenu = MENU_LABEL_MAP[location.pathname] ?? 'Unknown';
  
  const navigator = useNavigate();
  const isLoggedIn = Boolean(role);

  
  const { sessionRemain, logout } = useAuth();

  const handleLogout = () => {
    // 로그아웃 처리 로직 (예: 토큰 삭제, 리다이렉트 등)
    localStorage.removeItem('role');
    localStorage.removeItem('menus');
    navigator('/login');
  }

  const tenant = {
    hospitalName: 'OO대학교병원',
    systemName: 'Brain CDSS',
  };

  return (
    <header className="app-header">
      {/* 좌측: 시스템명 (Home) */}
      <div className="header-left">
          
        <button className="hamburger-btn" onClick={onToggleSidebar}>
          ☰
        </button>
        <img src={brainIcon} className="system-logo" />
        <div className="system-title">
          <a href="/dashboard" className="system-name">
            <span>{tenant.hospitalName}</span>&nbsp;
            <strong>{tenant.systemName}</strong>
          </a>
          
        </div>
      </div>

      {/* 중앙 : 현재 메뉴 표시 */}
      <div className="header-center">
          <h1>{currentMenu}</h1>
      </div>

      

      {/* 우측 : 사용자 정보 */}
      <div className="header-right">
        <div className="user-info">
            <span className="role">{ROLE_LABEL[role]}</span>
            <span className="divider">|</span>
            <span className="userIcon">
            <a>
                <i className={`fa-solid ${ROLE_ICON_MAP[role]}`} /> 
            </a>
            </span>
            <span className="divider">|</span>
            <a onClick={handleLogout}>
                <i className="fa-solid fa-lock"/>&nbsp;로그아웃
            </a>
        </div>
        <div className="timer-display">            
            <span className="current-time">
                <strong>{new Date().toLocaleTimeString()}</strong>
            </span>
            <span className="divider">|</span>
            <span className={`session-timer ${sessionRemain < 300 ? 'danger' : ''}`}>
                ⏱ {formatTime(sessionRemain)}
            </span>
        </div>

        </div>
    </header>
  );
}
