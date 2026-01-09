import type { ComponentType } from 'react';

import DashboardPage from '@/pages/dashboard/DashboardPage';
import PatientListPage from '@/pages/patient/PatientListPage';
import PatientDetailPage from '@/pages/patient/PatientDetailPage';
import EncounterListPage from '@/pages/encounter/EncounterListPage';
import ImagingListPage from '@/pages/imaging/ImagingListPage';
import ImagingReportPage from '@/pages/imaging/ImagingReportPage';
import ImagingWorklistPage from '@/pages/imaging/ImagingWorklistPage';
import AISummaryPage from '@/pages/ai/AISummaryPage';
import RISWorklistPage from '@/pages/ris/RISWorklistPage';
import OrderListPage from '@/pages/orders/OrderListPage';
import OrderCreatePage from '@/pages/orders/OrderCreate';
import { DoctorOrderPage, RISWorklistPage as OCSRISWorklistPage, RISStudyDetailPage, LISWorklistPage } from '@/pages/ocs';
import { ComingSoonPage } from '@/pages/common/CommingSoon';
import MenuPermissionPage from '@/pages/admin/MenuPermissionPage';
import UserList from '@/pages/admin/usersManagement/UserList';
import AuditLog from '@/pages/admin/AuditLog';
import SystemMonitorPage from '@/pages/admin/SystemMonitorPage';
import UserDetailPage from '@/pages/admin/usersManagement/UserDetailPage';
import RoleControlPage from '@/pages/admin/roleManagement/RoleControlPage';


// DB에서 호출된 메뉴명과 react 화면 컴포넌트 연결하는 곳(DB 메뉴 ↔ 화면 계약서)
export const routeMap: Record<string, ComponentType> = {
  DASHBOARD: DashboardPage,

  PATIENT_LIST: PatientListPage,
  PATIENT_DETAIL: PatientDetailPage,
  PATIENT_CARE: EncounterListPage,

  ENCOUNTER_LIST: EncounterListPage,

  IMAGING: ImagingListPage,
  IMAGE_VIEWER: ImagingListPage,
  IMAGING_STUDY_LIST: ImagingListPage,
  IMAGING_REPORT: ImagingReportPage,
  IMAGING_WORKLIST: ImagingWorklistPage,
  OHIF_VIEWER: () => <ComingSoonPage title="OHIF Viewer" />,
  AI_SUMMARY :AISummaryPage,
  ORDER_LIST: OrderListPage,
  ORDER_CREATE: OrderCreatePage,
  OCS_ORDER: DoctorOrderPage,
  OCS_RIS: OCSRISWorklistPage,
  OCS_RIS_DETAIL: RISStudyDetailPage,
  OCS_LIS: LISWorklistPage,
  RIS_WORKLIST : RISWorklistPage,
  
  LAB_RESULT_VIEW: () => <ComingSoonPage title="검사 결과 조회" />,
  LAB_RESULT_UPLOAD: () => <ComingSoonPage title="검사 결과 업로드" />,

  ADMIN_USER: UserList,
  ADMIN_ROLE: RoleControlPage,
  ADMIN_MENU_PERMISSION: MenuPermissionPage,
  ADMIN_AUDIT_LOG: AuditLog,
  ADMIN_SYSTEM_MONITOR: SystemMonitorPage,
  ADMIN_USER_DETAIL: UserDetailPage,

};