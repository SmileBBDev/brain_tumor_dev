import type { ComponentType } from 'react';

import DashboardPage from '@/pages/dashboard/DashboardPage';
import PatientListPage from '@/pages/patient/PatientListPage';
import PatientDetailPage from '@/pages/patient/PatientDetailPage';
import EncounterListPage from '@/pages/encounter/EncounterListPage';
import ImagingListPage from '@/pages/imaging/ImagingListPage';
import PatientImagingHistoryPage from '@/pages/imaging/PatientImagingHistoryPage';
import AISummaryPage from '@/pages/ai/AISummaryPage';
import RISWorklistPage from '@/pages/ris/RISWorklistPage';
import OrderListPage from '@/pages/orders/OrderListPage';
import OrderCreatePage from '@/pages/orders/OrderCreate';
import { DoctorOrderPage, RISWorklistPage as OCSRISWorklistPage, RISStudyDetailPage, LISWorklistPage, LISStudyDetailPage, RISDashboardPage, LISUploadPage, LISProcessStatusPage } from '@/pages/ocs';
import { NurseReceptionPage } from '@/pages/nurse';
import { AIRequestListPage, AIRequestCreatePage, AIRequestDetailPage } from '@/pages/ai-inference';
import { ComingSoonPage } from '@/pages/common/CommingSoon';
import MenuPermissionPage from '@/pages/admin/MenuPermissionPage';
import UserList from '@/pages/admin/usersManagement/UserList';
import AuditLog from '@/pages/admin/AuditLog';
import SystemMonitorPage from '@/pages/admin/SystemMonitorPage';
import UserDetailPage from '@/pages/admin/usersManagement/UserDetailPage';
import RoleControlPage from '@/pages/admin/roleManagement/RoleControlPage';


/**
 * DB 메뉴 code ↔ React 컴포넌트 매핑 (계약서)
 *
 * 메뉴 그룹 구조:
 * ├── DASHBOARD
 * ├── PATIENT: PATIENT_LIST, PATIENT_DETAIL, PATIENT_CARE
 * ├── ORDER: ORDER_LIST, ORDER_CREATE, OCS_ORDER
 * ├── IMAGING: IMAGE_VIEWER, RIS_WORKLIST, OCS_RIS, OCS_RIS_DETAIL, RIS_DASHBOARD
 * ├── LAB: LAB_RESULT_VIEW, LAB_RESULT_UPLOAD, OCS_LIS, OCS_LIS_DETAIL, LIS_PROCESS_STATUS
 * ├── AI_SUMMARY
 * ├── NURSE_RECEPTION
 * └── ADMIN: ADMIN_USER, ADMIN_USER_DETAIL, ADMIN_ROLE, ADMIN_MENU_PERMISSION, ADMIN_AUDIT_LOG, ADMIN_SYSTEM_MONITOR
 */
export const routeMap: Record<string, ComponentType> = {
  // === DASHBOARD ===
  DASHBOARD: DashboardPage,

  // === PATIENT 그룹 ===
  PATIENT_LIST: PatientListPage,
  PATIENT_DETAIL: PatientDetailPage,
  PATIENT_CARE: EncounterListPage,

  // === ORDER 그룹 ===
  ORDER_LIST: OrderListPage,
  ORDER_CREATE: OrderCreatePage,
  OCS_ORDER: DoctorOrderPage,

  // === IMAGING 그룹 ===
  IMAGE_VIEWER: ImagingListPage,
  PATIENT_IMAGING_HISTORY: PatientImagingHistoryPage,
  RIS_WORKLIST: RISWorklistPage,
  OCS_RIS: OCSRISWorklistPage,
  OCS_RIS_DETAIL: RISStudyDetailPage,
  RIS_DASHBOARD: RISDashboardPage,

  // === LAB 그룹 ===
  LAB_RESULT_VIEW: () => <ComingSoonPage title="검사 결과 조회" />,
  LAB_RESULT_UPLOAD: LISUploadPage,
  OCS_LIS: LISWorklistPage,
  OCS_LIS_DETAIL: LISStudyDetailPage,
  LIS_PROCESS_STATUS: LISProcessStatusPage,

  // === AI ===
  AI_SUMMARY: AISummaryPage,
  AI_REQUEST_LIST: AIRequestListPage,
  AI_REQUEST_CREATE: AIRequestCreatePage,
  AI_REQUEST_DETAIL: AIRequestDetailPage,

  // === NURSE ===
  NURSE_RECEPTION: NurseReceptionPage,

  // === ADMIN 그룹 ===
  ADMIN_USER: UserList,
  ADMIN_USER_DETAIL: UserDetailPage,
  ADMIN_ROLE: RoleControlPage,
  ADMIN_MENU_PERMISSION: MenuPermissionPage,
  ADMIN_AUDIT_LOG: AuditLog,
  ADMIN_SYSTEM_MONITOR: SystemMonitorPage,
};