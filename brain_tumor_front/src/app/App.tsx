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
import UserListPage from '@/pages/admin/UserList';

export default function App(){
  return (
    <Routes>
      {/* 로그인 */}
      <Route path = "/login" element={<LoginPage />}/>

      <Route element={<AppLayout />}>
        {/* 기본 진입 */}
        <Route path="/" element={<HomeRedirect />} />


        {/* Route 분리 : 
            같은 기능인데 사용자만 다른경우 - 페이지 내부에서 Role에 맞게 분기처리  
        */}
        {/* 대시보드 */}
        <Route path = "/dashboard" 
          element={
            <ProtectedRoute menu="DASHBOARD">
              <DashboardPage/>
            </ProtectedRoute>
          }
        />

        {/* 환자 목록 */}
        <Route path = "/patients" 
          element={
            <ProtectedRoute menu="PATIENT_LIST">
              <PatientListPage/>
            </ProtectedRoute>
          }
        />

        {/* 환자 상세 */}
        <Route
          path="/patients/:patientId"
          element={
            <ProtectedRoute menu="PATIENT_DETAIL">
              <PatientDetailPage />
            </ProtectedRoute>
          }
        />

        {/* 영상 조회 */}
        <Route
          path="/imaging"
          element={
            <ProtectedRoute menu="IMAGE_VIEWER">
              <ImagingPage />
            </ProtectedRoute>
          }
        />

        {/* AI 요약 */}
        <Route
          path="/ai"
          element={
            <ProtectedRoute menu="AI_SUMMARY">
              <AISummaryPage />
            </ProtectedRoute>
          }
        />

        {/* 관리자 */}
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute menu="ADMIN_USER">
              <UserListPage />
            </ProtectedRoute>
          }
        />
        
      </Route>
    </Routes>
  )
}
