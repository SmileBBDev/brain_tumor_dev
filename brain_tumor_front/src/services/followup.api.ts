import { api } from './api';

// =============================================================================
// Follow-up API Types
// =============================================================================

export interface FollowUp {
  id: number;
  patient: number;
  patient_name: string;
  patient_number: string;
  encounter: number | null;
  treatment_plan: number | null;
  treatment_plan_title: string | null;
  followup_date: string;
  followup_type: 'routine' | 'imaging' | 'lab' | 'symptom' | 'emergency';
  followup_type_display: string;
  clinical_status: 'stable' | 'improved' | 'deteriorated' | 'recurrence' | 'unknown';
  clinical_status_display: string;
  kps_score: number | null; // Karnofsky Performance Status (0-100)
  ecog_score: number | null; // ECOG Performance Status (0-5)
  weight: number | null;
  blood_pressure_systolic: number | null;
  blood_pressure_diastolic: number | null;
  symptoms: string;
  physical_exam: string;
  assessment: string;
  plan: string;
  next_followup_date: string | null;
  recorded_by: number;
  recorded_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface FollowUpCreateData {
  patient_id: number;
  encounter_id?: number;
  treatment_plan_id?: number;
  followup_date: string;
  followup_type: string;
  clinical_status: string;
  kps_score?: number;
  ecog_score?: number;
  weight?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  symptoms?: string;
  physical_exam?: string;
  assessment?: string;
  plan?: string;
  next_followup_date?: string;
}

// =============================================================================
// API Functions
// =============================================================================

// 경과 기록 목록
export const getFollowUps = async (params?: {
  patient_id?: number;
  clinical_status?: string;
  followup_type?: string;
}): Promise<FollowUp[]> => {
  const response = await api.get<FollowUp[]>('/followup/', { params });
  return response.data;
};

// 경과 기록 상세
export const getFollowUp = async (id: number): Promise<FollowUp> => {
  const response = await api.get<FollowUp>(`/followup/${id}/`);
  return response.data;
};

// 경과 기록 생성
export const createFollowUp = async (data: FollowUpCreateData): Promise<FollowUp> => {
  const response = await api.post<FollowUp>('/followup/', data);
  return response.data;
};

// 경과 기록 수정
export const updateFollowUp = async (
  id: number,
  data: Partial<FollowUpCreateData>
): Promise<FollowUp> => {
  const response = await api.patch<FollowUp>(`/followup/${id}/`, data);
  return response.data;
};

// 경과 기록 삭제
export const deleteFollowUp = async (id: number): Promise<void> => {
  await api.delete(`/followup/${id}/`);
};

// 환자별 경과 기록 조회
export const getPatientFollowUps = async (patientId: number): Promise<FollowUp[]> => {
  const response = await api.get<FollowUp[]>('/followup/', {
    params: { patient_id: patientId },
  });
  return response.data;
};
