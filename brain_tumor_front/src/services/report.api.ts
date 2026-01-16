import { api } from './api';

// 통합 보고서 타입
export interface UnifiedReport {
  id: string;
  type: string;
  type_display: string;
  sub_type: string;
  patient_id: number | null;
  patient_number: string | null;
  patient_name: string | null;
  title: string;
  status: string;
  status_display: string;
  result: any;
  result_display: string;
  created_at: string | null;
  completed_at: string | null;
  author: string | null;
  doctor: string | null;
  thumbnail: ReportThumbnail;
  link: string;
}

// 채널별 썸네일 정보 (T1, T1C, T2, FLAIR)
export interface ChannelThumbnail {
  channel: 'T1' | 'T1C' | 'T2' | 'FLAIR';
  url: string;
  description: string;
}

export interface ReportThumbnail {
  type: 'image' | 'icon' | 'segmentation' | 'chart' | 'dicom' | 'dicom_multi';
  url?: string;
  icon?: string;
  color?: string;
  job_id?: string;
  api_url?: string;
  chart_type?: string;
  // DICOM 썸네일 관련
  orthanc_study_id?: string;
  thumbnails_url?: string;
  channels?: ChannelThumbnail[];
}

export interface UnifiedReportResponse {
  count: number;
  reports: UnifiedReport[];
}

export interface ReportDashboardParams {
  patient_id?: number;
  report_type?: 'OCS_RIS' | 'OCS_LIS' | 'AI_M1' | 'AI_MG' | 'AI_MM' | 'FINAL';
  date_from?: string;
  date_to?: string;
  limit?: number;
}

// 환자 타임라인 아이템
export interface TimelineItem {
  id: string;
  type: string;
  type_display: string;
  sub_type: string;
  title: string;
  date: string;
  status: string;
  result: string;
  result_flag: 'normal' | 'abnormal' | 'ai' | 'final';
  author: string | null;
  link: string;
}

export interface PatientTimelineResponse {
  patient_id: number;
  patient_number: string;
  patient_name: string;
  count: number;
  timeline: TimelineItem[];
}

// 통합 보고서 대시보드 조회
export async function getReportDashboard(params?: ReportDashboardParams): Promise<UnifiedReportResponse> {
  const response = await api.get('/reports/dashboard/', { params });
  return response.data;
}

// 환자별 보고서 타임라인 조회
export async function getPatientReportTimeline(patientId: number): Promise<PatientTimelineResponse> {
  const response = await api.get(`/reports/patient/${patientId}/timeline/`);
  return response.data;
}
