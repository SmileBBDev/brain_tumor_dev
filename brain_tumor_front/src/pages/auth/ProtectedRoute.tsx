import { Navigate } from 'react-router-dom';
import type { MenuId } from '@/types/menu';

// 권한 가이드
interface Props{
    menu : MenuId;
    children : React.ReactNode;
}

export default function ProtectedRoute({menu, children}: Props){
    const token = localStorage.getItem('accessToken');
    const menus: MenuId[] = JSON.parse(
        localStorage.getItem('menus') || '[]'
    );

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    if(!menus.includes(menu)){
        return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
}