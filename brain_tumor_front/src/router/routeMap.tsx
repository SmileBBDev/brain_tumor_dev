import { lazy, type ComponentType } from 'react';

// Lazy loading으로 코드 스플리팅
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const PatientListPage = lazy(() => import('@/pages/patient/PatientListPage'));
const PatientDetailPage = lazy(() => import('@/pages/patient/PatientDetailPage'));
// 레거시: OCS RIS 워크리스트로 대체됨
// const ImagingListPage = lazy(() => import('@/pages/imaging/ImagingListPage'));
const PatientImagingHistoryPage = lazy(() => import('@/pages/imaging/PatientImagingHistoryPage'));
const MenuPermissionPage = lazy(() => import('@/pages/admin/MenuPermissionPage'));
const UserList = lazy(() => import('@/pages/admin/usersManagement/UserList'));
const AuditLog = lazy(() => import('@/pages/admin/AuditLog'));
const SystemMonitorPage = lazy(() => import('@/pages/admin/SystemMonitorPage'));
const UserDetailPage = lazy(() => import('@/pages/admin/usersManagement/UserDetailPage'));
const RoleControlPage = lazy(() => import('@/pages/admin/roleManagement/RoleControlPage'));

// OCS 페이지들 (통합됨)
const OCSCreatePage = lazy(() => import('@/pages/ocs/OCSCreatePage'));
const OCSStatusPage = lazy(() => import('@/pages/ocs/OCSStatusPage'));
const OCSManagePage = lazy(() => import('@/pages/ocs/OCSManagePage'));
const OCSRISWorklistPage = lazy(() => import('@/pages/ocs/RISWorklistPage'));
const RISStudyDetailPage = lazy(() => import('@/pages/ocs/RISStudyDetailPage'));
const LISWorklistPage = lazy(() => import('@/pages/ocs/LISWorklistPage'));
const LISStudyDetailPage = lazy(() => import('@/pages/ocs/LISStudyDetailPage'));
const RISProcessStatusPage = lazy(() => import('@/pages/ocs/RISProcessStatusPage'));
const LISUploadPage = lazy(() => import('@/pages/ocs/LISUploadPage'));
const LISProcessStatusPage = lazy(() => import('@/pages/ocs/LISProcessStatusPage'));
const RISUploadPage = lazy(() => import('@/pages/ocs/RISUploadPage'));
const OCSProcessStatusPage = lazy(() => import('@/pages/ocs/OCSProcessStatusPage'));

// Lab, Clinic
// 레거시: OCS LIS 워크리스트로 대체됨
// const LabListPage = lazy(() => import('@/pages/lab/LabListPage'));
const ClinicPage = lazy(() => import('@/pages/clinic/ClinicPage'));

// Encounter
const EncounterListPage = lazy(() => import('@/pages/encounter/EncounterListPage'));
const EncounterDetailPage = lazy(() => import('@/pages/encounter/EncounterDetailPage'));

// AI Inference
const AIRequestListPage = lazy(() => import('@/pages/ai-inference/AIRequestListPage'));
const AIRequestCreatePage = lazy(() => import('@/pages/ai-inference/AIRequestCreatePage'));
const AIRequestDetailPage = lazy(() => import('@/pages/ai-inference/AIRequestDetailPage'));
const AIProcessStatusPage = lazy(() => import('@/pages/ai-inference/AIProcessStatusPage'));
const AIModelsPage = lazy(() => import('@/pages/ai-inference/AIModelsPage'));
const AISummaryPage = lazy(() => import('@/pages/ai/AISummaryPage'));

// Patient Portal (환자 전용 - MY_CARE)
const MySummaryPage = lazy(() => import('@/pages/patient-portal/MySummaryPage'));
const MyVisitsPage = lazy(() => import('@/pages/patient-portal/MyVisitsPage'));
const MyImagingPage = lazy(() => import('@/pages/patient-portal/MyImagingPage'));
const MyLabPage = lazy(() => import('@/pages/patient-portal/MyLabPage'));
const AboutHospitalPage = lazy(() => import('@/pages/patient-portal/AboutHospitalPage'));

// Report (보고서 대시보드)
const ReportDashboardPage = lazy(() => import('@/pages/report/ReportDashboardPage'));


/**
 * DB 메뉴 code ↔ React 컴포넌트 매핑 (계약서)
 *
 * 메뉴 그룹 구조:
 * ├── DASHBOARD
 * ├── PATIENT: PATIENT_LIST, PATIENT_DETAIL, PATIENT_CARE, ENCOUNTER_LIST
 * ├── OCS: OCS_STATUS, OCS_CREATE, OCS_MANAGE
 * ├── IMAGING: IMAGE_VIEWER, OCS_RIS, OCS_RIS_DETAIL, RIS_DASHBOARD, RIS_RESULT_UPLOAD
 * ├── LAB: LAB_RESULT_VIEW, LAB_RESULT_UPLOAD, OCS_LIS, OCS_LIS_DETAIL, LIS_PROCESS_STATUS
 * ├── AI: AI_REQUEST_LIST, AI_REQUEST_CREATE, AI_REQUEST_DETAIL, AI_PROCESS_STATUS, AI_MODELS
 * ├── REPORT: REPORT_DASHBOARD, REPORT_LIST, REPORT_CREATE, REPORT_DETAIL
 * ├── ADMIN: ADMIN_USER, ADMIN_USER_DETAIL, ADMIN_ROLE, ADMIN_MENU_PERMISSION, ADMIN_AUDIT_LOG, ADMIN_SYSTEM_MONITOR
 * └── MY_CARE (환자 전용): MY_SUMMARY, MY_VISITS, MY_IMAGING, MY_LAB
 */
export const routeMap: Record<string, ComponentType> = {
  // === DASHBOARD ===
  DASHBOARD: DashboardPage,

  // === PATIENT 그룹 ===
  PATIENT_LIST: PatientListPage,
  PATIENT_DETAIL: PatientDetailPage,
  PATIENT_CARE: ClinicPage,
  ENCOUNTER_LIST: EncounterListPage,
  ENCOUNTER_DETAIL: EncounterDetailPage,

  // === OCS 그룹 ===
  OCS_STATUS: OCSStatusPage,       // OCS 현황 (간호사/관리자용)
  OCS_CREATE: OCSCreatePage,       // OCS 생성
  OCS_MANAGE: OCSManagePage,       // OCS 관리 (의사용)
  OCS_PROCESS_STATUS: OCSProcessStatusPage, // OCS 통합 처리 현황

  // === IMAGING 그룹 ===
  // IMAGE_VIEWER: OCS RIS 워크리스트로 통합 (레거시 ImagingListPage 대체)
  IMAGE_VIEWER: OCSRISWorklistPage,
  PATIENT_IMAGING_HISTORY: PatientImagingHistoryPage,
  OCS_RIS: OCSRISWorklistPage,
  OCS_RIS_DETAIL: RISStudyDetailPage,
  RIS_DASHBOARD: RISProcessStatusPage,
  RIS_RESULT_UPLOAD: RISUploadPage,

  // === LAB 그룹 ===
  // LAB_RESULT_VIEW: OCS LIS 워크리스트로 통합 (레거시 LabListPage 대체)
  LAB_RESULT_VIEW: LISWorklistPage,
  LAB_RESULT_UPLOAD: LISUploadPage,
  OCS_LIS: LISWorklistPage,
  OCS_LIS_DETAIL: LISStudyDetailPage,
  LIS_PROCESS_STATUS: LISProcessStatusPage,

  // === AI 그룹 ===
  AI_VIEWER: AISummaryPage,
  AI_REQUEST_LIST: AIRequestListPage,
  AI_REQUEST_CREATE: AIRequestCreatePage,
  AI_REQUEST_DETAIL: AIRequestDetailPage,
  AI_PROCESS_STATUS: AIProcessStatusPage,
  AI_MODELS: AIModelsPage,

  // === ADMIN 그룹 ===
  ADMIN_USER: UserList,
  ADMIN_USER_DETAIL: UserDetailPage,
  ADMIN_ROLE: RoleControlPage,
  ADMIN_MENU_PERMISSION: MenuPermissionPage,
  ADMIN_AUDIT_LOG: AuditLog,
  ADMIN_SYSTEM_MONITOR: SystemMonitorPage,

  // === MY_CARE 그룹 (환자 전용) ===
  MY_SUMMARY: MySummaryPage,
  MY_VISITS: MyVisitsPage,
  MY_IMAGING: MyImagingPage,
  MY_LAB: MyLabPage,
  ABOUT_HOSPITAL: AboutHospitalPage,

  // === REPORT 그룹 ===
  REPORT_DASHBOARD: ReportDashboardPage,
};