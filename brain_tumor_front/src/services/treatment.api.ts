import { api } from './api';

// =============================================================================
// Treatment API Types
// =============================================================================

export interface TreatmentPlan {
  id: number;
  patient: number;
  patient_name: string;
  patient_number: string;
  encounter: number | null;
  ai_request: number | null;
  treatment_type: 'surgery' | 'radiation' | 'chemotherapy' | 'observation' | 'combined';
  treatment_type_display: string;
  title: string;
  description: string;
  goals: string;
  start_date: string | null;
  end_date: string | null;
  status: 'draft' | 'planned' | 'active' | 'completed' | 'cancelled';
  status_display: string;
  created_by: number;
  created_by_name: string;
  approved_by: number | null;
  approved_by_name: string | null;
  approved_at: string | null;
  notes: string;
  sessions?: TreatmentSession[];
  created_at: string;
  updated_at: string;
}

export interface TreatmentSession {
  id: number;
  treatment_plan: number;
  ocs: number | null;
  session_number: number;
  scheduled_date: string;
  actual_date: string | null;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'missed';
  status_display: string;
  performed_by: number | null;
  performed_by_name: string | null;
  vital_signs: Record<string, unknown>;
  medications: Record<string, unknown>[];
  notes: string;
  complications: string;
  created_at: string;
  updated_at: string;
}

export interface TreatmentPlanCreateData {
  patient_id: number;
  encounter_id?: number;
  ai_request_id?: number;
  treatment_type: string;
  title: string;
  description?: string;
  goals?: string;
  start_date?: string;
  end_date?: string;
  notes?: string;
}

export interface TreatmentSessionCreateData {
  treatment_plan_id: number;
  scheduled_date: string;
  notes?: string;
}

// =============================================================================
// API Functions
// =============================================================================

// 치료 계획 목록
export const getTreatmentPlans = async (params?: {
  patient_id?: number;
  status?: string;
  treatment_type?: string;
}): Promise<TreatmentPlan[]> => {
  const response = await api.get<TreatmentPlan[]>('/treatment/plans/', { params });
  return response.data;
};

// 치료 계획 상세
export const getTreatmentPlan = async (id: number): Promise<TreatmentPlan> => {
  const response = await api.get<TreatmentPlan>(`/treatment/plans/${id}/`);
  return response.data;
};

// 치료 계획 생성
export const createTreatmentPlan = async (data: TreatmentPlanCreateData): Promise<TreatmentPlan> => {
  const response = await api.post<TreatmentPlan>('/treatment/plans/', data);
  return response.data;
};

// 치료 계획 수정
export const updateTreatmentPlan = async (
  id: number,
  data: Partial<TreatmentPlanCreateData>
): Promise<TreatmentPlan> => {
  const response = await api.patch<TreatmentPlan>(`/treatment/plans/${id}/`, data);
  return response.data;
};

// 치료 계획 시작
export const startTreatmentPlan = async (id: number): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/treatment/plans/${id}/start/`);
  return response.data;
};

// 치료 계획 완료
export const completeTreatmentPlan = async (id: number): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/treatment/plans/${id}/complete/`);
  return response.data;
};

// 치료 계획 취소
export const cancelTreatmentPlan = async (id: number): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/treatment/plans/${id}/cancel/`);
  return response.data;
};

// 세션 목록
export const getTreatmentSessions = async (planId: number): Promise<TreatmentSession[]> => {
  const response = await api.get<TreatmentSession[]>(`/treatment/plans/${planId}/sessions/`);
  return response.data;
};

// 세션 생성
export const createTreatmentSession = async (
  planId: number,
  data: TreatmentSessionCreateData
): Promise<TreatmentSession> => {
  const response = await api.post<TreatmentSession>(`/treatment/sessions/`, {
    ...data,
    treatment_plan_id: planId,
  });
  return response.data;
};

// 세션 완료
export const completeTreatmentSession = async (
  sessionId: number,
  data: { notes?: string; complications?: string }
): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/treatment/sessions/${sessionId}/complete/`, data);
  return response.data;
};

// 환자별 치료 계획 조회
export const getPatientTreatmentPlans = async (patientId: number): Promise<TreatmentPlan[]> => {
  const response = await api.get<TreatmentPlan[]>(`/treatment/plans/`, {
    params: { patient_id: patientId },
  });
  return response.data;
};
