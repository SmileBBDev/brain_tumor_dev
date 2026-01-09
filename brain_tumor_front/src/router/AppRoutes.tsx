import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/pages/auth/AuthProvider';
import ProtectedRoute from '@/pages/auth/ProtectedRoute';
import { routeMap } from './routeMap';
import type { MenuNode } from '@/types/menu';
import FullScreenLoader from '@/pages/common/FullScreenLoader';

// 접근 가능한 메뉴만 flatten (라우트 등록용 - breadcrumbOnly 포함)
function flattenAccessibleMenus(
  menus: MenuNode[],
  permissions: string[],
  includeHidden: boolean = false
): MenuNode[] {
  return menus.flatMap(menu => {
    const hasPermission = permissions.includes(menu.code);

    const children = menu.children
      ? flattenAccessibleMenus(menu.children, permissions, includeHidden)
      : [];

    // path가 있고 접근 가능하면 포함
    // includeHidden=true면 breadcrumbOnly도 포함 (라우트 등록용)
    if (menu.path && hasPermission) {
      if (!menu.breadcrumbOnly || includeHidden) {
        return [menu, ...children];
      }
    }

    // path가 없거나 접근 불가 → children만 포함
    return children;
  });
}

// 첫 접근 가능한 path 찾기
function findFirstAccessiblePath(
  menus: MenuNode[],
  permissions: string[]
): string | null {
  for (const menu of menus) {
    // path가 있고 접근 가능하면 바로 반환
    if (
      menu.path &&
      !menu.breadcrumbOnly &&
      permissions.includes(menu.code)
    ) {
      return menu.path;
    }

    // path가 없거나 접근 불가 → children 탐색
    if (menu.children?.length) {
      const childPath = findFirstAccessiblePath(menu.children, permissions);
      if (childPath) return childPath;
    }
  }
  return null;
}

export default function AppRoutes() {
  const { menus, permissions, isAuthReady } = useAuth();

  // 준비 전엔 로딩
  if (!isAuthReady || menus.length === 0 || permissions.length === 0) {
    return <FullScreenLoader />;
  }

  const homePath = findFirstAccessiblePath(menus, permissions);
  if (!homePath) {
    return <FullScreenLoader />;
  }

  // 라우트 등록용: breadcrumbOnly 메뉴도 포함
  const accessibleMenus = flattenAccessibleMenus(menus, permissions, true);

  return (
    <Routes>
      {/* 홈 */}
      <Route index element={<Navigate to={homePath} replace />} />

      {accessibleMenus.map(menu => {
        const Component = routeMap[menu.code];
        if (!Component) return null;

        return (
          <Route
            key={menu.code}
            path={menu.path!}
            element={
              <ProtectedRoute>
                <Component />
              </ProtectedRoute>
            }
          />
        );
      })}

      <Route path="*" element={<Navigate to="/403" replace />} />
    </Routes>
  );
}