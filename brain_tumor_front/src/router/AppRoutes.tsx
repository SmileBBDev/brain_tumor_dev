import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/pages/auth/AuthProvider';
import ProtectedRoute from '@/pages/auth/ProtectedRoute';
import { routeMap } from './routeMap';
import type { MenuNode } from '@/types/menu';

function flattenMenus(menus: MenuNode[]): MenuNode[] {
  return menus.flatMap(menu => [
    menu,
    ...(menu.children?.length ? flattenMenus(menu.children) : []),
  ]);
}

export default function AppRoutes() {
  const { menus, isAuthReady } = useAuth();

  if (!isAuthReady) return null;

  const flatMenus = flattenMenus(menus);

  return (
    <Routes>
      {/* 환자 상세 페이지 동적 라우트 - 먼저 매칭되도록 */}
      <Route
        path="/patients/:patientId"
        element={
          <ProtectedRoute menuId="PATIENT_DETAIL">
            {(() => {
              const Component = routeMap['PATIENT_DETAIL'];
              return Component ? <Component /> : <Navigate to="/403" replace />;
            })()}
          </ProtectedRoute>
        }
      />

      {flatMenus.map(menu => {
        if (!menu.path) return null;

        const Component = routeMap[menu.id];

        if (!Component) {
          console.warn(`routeMap에 없는 메뉴: ${menu.id}`);
          return null;
        }

        return (
          <Route
            key={menu.id}
            path={menu.path}
            element={
              <ProtectedRoute menuId={menu.id}>
                <Component />
              </ProtectedRoute>
            }
          />
        );
      })}

      {/* 기본 홈 경로 */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 없는 경로 */}
      <Route path="*" element={<Navigate to="/403" replace />} />
    </Routes>
  );
}
