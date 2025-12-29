import {Routes, Route} from 'react-router-dom';
import LoginPage from '@/pages/auth/LoginPage';
import AppLayout from '@/layout/AppLayout';
import ProtectedRoute from '@/pages/auth/ProtectedRoute';
import PatientListPage from '@/pages/patient/PatientListPage';
import HomeRedirect from '@/app/HomeRedirect';
import ImagingPage from '@/pages/imaging/ImagingPage';
import AISummaryPage from '@/pages/ai/AISummaryPage';
import DashboardPage from '@/pages/dashboard/DashboardPage';
import PatientDetailPage from '@/pages/patient/PatientDetailPage';
import CommingSoon from '@/pages/common/CommingSoon';
import OrdersLayout from '@/layout/OrdersLayout';
import AdminLayout from '@/pages/admin/AdminLayout';
import UserListPage from '@/pages/admin/UserList';
import MenuPermissionPage from '@/pages/admin/MenuPermissionPage';
import AuditLogPage from '@/pages/admin/AuditLog';
import SystemMonitorPage from '@/pages/admin/SystemMonitorPage';
import RISWorklistPage from '@/pages/ris/RISWorklistPage';



export default function App(){
  return (
    <Routes>
      {/* 로그인 */}
      <Route path = "/login" element={<LoginPage />}/>

      {/* 기본 진입 */}
      <Route path="/" element={<HomeRedirect />} />

      <Route element={<AppLayout />}>
        {/* Route 분리 : 
            같은 기능인데 사용자만 다른경우 - 페이지 내부에서 Role에 맞게 분기처리  
        */}
        {/* 대시보드 */}
        <Route path = "/dashboard" 
          element={
            <ProtectedRoute menuId="DASHBOARD">
              <DashboardPage/>
            </ProtectedRoute>
          }
        />

        {/* 환자 목록 */}
        <Route path = "/patients" 
          element={
            <ProtectedRoute menuId="PATIENT_LIST">
              <PatientListPage/>
            </ProtectedRoute>
          }
        />

        {/* 환자 상세 */}
        <Route
          path="/patients/:patientId"
          element={
            <ProtectedRoute menuId="PATIENT_DETAIL">
              <PatientDetailPage />
            </ProtectedRoute>
          }
        />


        {/* RIS */}
        {/* 영상 조회 */}
        <Route
          path="/imaging"
          element={
            <ProtectedRoute menuId="IMAGE_VIEWER">
              <ImagingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ris/worklist"
          element={
            <ProtectedRoute menuId="RIS_WORKLIST">
              <RISWorklistPage />
            </ProtectedRoute>
          }
        />

        {/* AI 요약 */}
        <Route
          path="/ai"
          element={
            <ProtectedRoute menuId="AI_SUMMARY">
              <AISummaryPage />
            </ProtectedRoute>
          }
        />

        {/* 관리자 */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute menuId="ADMIN_USER">
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route path="users" element={<UserListPage />} />
          <Route path="roles" element={<CommingSoon />} />
          <Route path="permissions" element={<MenuPermissionPage />} />
          <Route path="audit" element={<AuditLogPage />} />
          <Route path="monitor" element={<SystemMonitorPage />} />
        </Route>


        {/* 작업해야 될 페이지들 */}
        {/* Orders */}
        <Route
          path="/orders"
          element={
            <ProtectedRoute menuId="ORDER_LIST">
              <OrdersLayout />
            </ProtectedRoute>
          }
        >
          <Route
            path="list"
            element={
              <ProtectedRoute menuId="ORDER_LIST">
                <CommingSoon />
              </ProtectedRoute>
            }
          />
          <Route
            path="create"
            element={
              <ProtectedRoute menuId="ORDER_CREATE">
                <CommingSoon />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* LAB */}
        <Route
          path="/lab"
          element={
            <ProtectedRoute menuId="LAB_RESULT_VIEW">
              <CommingSoon />
            </ProtectedRoute>
          }
        />
        <Route
          path="/lab/upload"
          element={
            <ProtectedRoute menuId="LAB_RESULT_UPLOAD">
              <CommingSoon />
            </ProtectedRoute>
          }
        />
        
      </Route>
    </Routes>
  )
}
