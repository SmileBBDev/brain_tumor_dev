import { Navigate } from 'react-router-dom';
import { useAuth } from '@/pages/auth/AuthProvider';

// 권한 가이드
interface Props{
    children : React.ReactNode;
}

export default function ProtectedRoute({ children }: Props){
    const { isAuthReady, isAuthenticated } = useAuth();
    
    // Auth 초기화 대기
    if (!isAuthReady) return null;
    
    // 인증 정보 없음
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}