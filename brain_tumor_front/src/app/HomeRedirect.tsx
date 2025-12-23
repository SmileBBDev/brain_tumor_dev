import { Navigate } from 'react-router-dom';
import { Role_Home } from '@/pages/auth/roleHome';
import type { Role } from '@/types/role';

export default function HomeRedirect() {
    const token = localStorage.getItem('accessToken');
    const role = localStorage.getItem('role') as Role;
    
    if (!token || !role) {
        return <Navigate to="/login" replace />;
    }
    return <Navigate to={Role_Home[role]} replace />;
}
