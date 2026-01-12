import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/pages/auth/AuthProvider';
import ProtectedRoute from '@/pages/auth/ProtectedRoute';
import { routeMap } from './routeMap';
import type { MenuNode } from '@/types/menu';
import FullScreenLoader from '@/pages/common/FullScreenLoader';

// Lazy loaded pages
const OCSCreatePage = lazy(() => import('@/pages/ocs/OCSCreatePage'));
const OCSResultReportPage = lazy(() => import('@/pages/ocs/OCSResultReportPage'));
const LISStudyDetailPage = lazy(() => import('@/pages/ocs/LISStudyDetailPage'));
const RISStudyDetailPage = lazy(() => import('@/pages/ocs/RISStudyDetailPage'));
const MyPage = lazy(() => import('@/pages/mypage/MyPage'));
const PatientDashboard = lazy(() => import('@/pages/patient/PatientDashboard'));

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

export default function AppRoutes() {
  const { menus, permissions, isAuthReady, role } = useAuth();

  // PATIENT 역할은 메뉴/권한 없이도 대시보드 접근 가능
  if (!isAuthReady) {
    return <FullScreenLoader />;
  }

  // PATIENT 역할은 전용 대시보드로 이동
  if (role === 'PATIENT') {
    return (
      <Suspense fallback={<FullScreenLoader />}>
        <Routes>
          <Route index element={<Navigate to="/patient/dashboard" replace />} />
          <Route
            path="/patient/dashboard"
            element={
              <ProtectedRoute allowedRoles={['PATIENT']}>
                <PatientDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mypage"
            element={
              <ProtectedRoute>
                <MyPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/patient/dashboard" replace />} />
        </Routes>
      </Suspense>
    );
  }

  // 준비 전엔 로딩 (PATIENT 외 역할)
  if (menus.length === 0 || permissions.length === 0) {
    return <FullScreenLoader />;
  }

  // 기본 홈 경로는 Dashboard로 고정
  const homePath = '/dashboard';

  // 라우트 등록용: breadcrumbOnly 메뉴도 포함
  const accessibleMenus = flattenAccessibleMenus(menus, permissions, true);

  return (
    <Suspense fallback={<FullScreenLoader />}>
      <Routes>
        {/* 홈 */}
        <Route index element={<Navigate to={homePath} replace />} />

        {/* OCS 생성 페이지 (메뉴에 없지만 직접 접근 필요) */}
        <Route
          path="/ocs/create"
          element={
            <ProtectedRoute>
              <OCSCreatePage />
            </ProtectedRoute>
          }
        />

        {/* OCS 결과 보고서 페이지 */}
        <Route
          path="/ocs/report/:ocsId"
          element={
            <ProtectedRoute>
              <OCSResultReportPage />
            </ProtectedRoute>
          }
        />

        {/* LIS 검사 상세 페이지 (메뉴에 없지만 직접 접근 필요) */}
        <Route
          path="/ocs/lis/:ocsId"
          element={
            <ProtectedRoute>
              <LISStudyDetailPage />
            </ProtectedRoute>
          }
        />

        {/* RIS 영상 상세 페이지 (메뉴에 없지만 직접 접근 필요) */}
        <Route
          path="/ocs/ris/:ocsId"
          element={
            <ProtectedRoute>
              <RISStudyDetailPage />
            </ProtectedRoute>
          }
        />

        {/* 마이페이지 (모든 로그인 사용자 접근 가능) */}
        <Route
          path="/mypage"
          element={
            <ProtectedRoute>
              <MyPage />
            </ProtectedRoute>
          }
        />

        {/* 환자 포털 (PATIENT 역할만 접근 가능) */}
        <Route
          path="/patient/dashboard"
          element={
            <ProtectedRoute allowedRoles={['PATIENT']}>
              <PatientDashboard />
            </ProtectedRoute>
          }
        />

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
    </Suspense>
  );
}