import { Navigate } from 'react-router-dom';
import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';

import type{ MenuNode } from '@/pages/auth/AuthProvider';
import { useAuth } from '@/pages/auth/AuthProvider';

// 권한 가이드
interface Props{
    menuId : MenuId;
    children : React.ReactNode;
}

export default function ProtectedRoute({menuId, children}: Props){
    const token = localStorage.getItem('accessToken');
    const role = localStorage.getItem('role') as Role | null;

    const { menus } = useAuth();

    const hasAccess = checkMenuAccess(menus, menuId);

    function checkMenuAccess(tree: MenuNode[], id: string): boolean {
        for (const m of tree) {
            if (m.id === id) return true;
            if (m.children && checkMenuAccess(m.children, id)) return true;
        }
        return false;
    }

    // const menus: MenuId[] = JSON.parse(
    //     localStorage.getItem('menus') || '[]'
    // );

    // SYSTEMMANAGER는 무조건 통과
    if (role === 'SYSTEMMANAGER') {
        return children;
    }

    // 로그인 안 됨
    if (!token) {
        return <Navigate to="/login" replace />;
    }

    // if(!menus.includes(menuId)){
    //     return <Navigate to="/login" replace />;
    // }
    // 메뉴 권한 없음
    if (!hasAccess) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}