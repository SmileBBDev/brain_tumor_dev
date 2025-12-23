import { Navigate } from 'react-router-dom';
import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';

// 권한 가이드
interface Props{
    menu : MenuId;
    children : React.ReactNode;
}

export default function ProtectedRoute({menu, children}: Props){
    const token = localStorage.getItem('accessToken');
    const role = localStorage.getItem('role') as Role | null;
    const menus: MenuId[] = JSON.parse(
        localStorage.getItem('menus') || '[]'
    );

    // SYSTEMMANAGER는 무조건 통과
    if (role === 'SYSTEMMANAGER') {
        return children;
    }


    if (!token) {
        return <Navigate to="/login" replace />;
    }

    if(!menus.includes(menu)){
        return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
}