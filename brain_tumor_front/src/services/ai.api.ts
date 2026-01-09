import { api } from './api';

// =============================================================================
// AI Inference API
// =============================================================================

export interface AIModel {
  id: number;
  code: string;
  name: string;
  description: string;
  ocs_sources: string[];
  required_keys: Record<string, string[]>;
  version: string;
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AIInferenceRequest {
  id: number;
  request_id: string;
  patient: number;
  patient_name: string;
  patient_number: string;
  model: number;
  model_code: string;
  model_name: string;
  requested_by: number;
  requested_by_name: string;
  ocs_references: number[];
  input_data: Record<string, unknown>;
  status: 'PENDING' | 'VALIDATING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  status_display: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  priority_display: string;
  requested_at: string;
  started_at: string | null;
  completed_at: string | null;
  processing_time: number | null;
  error_message: string | null;
  has_result: boolean;
  result?: AIInferenceResult;
  logs?: AIInferenceLog[];
  created_at: string;
  updated_at: string;
}

export interface AIInferenceResult {
  id: number;
  result_data: Record<string, unknown>;
  confidence_score: number | null;
  visualization_paths: string[];
  reviewed_by: number | null;
  reviewed_by_name: string | null;
  review_status: 'pending' | 'approved' | 'rejected';
  review_status_display: string;
  review_comment: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIInferenceLog {
  id: number;
  action: string;
  action_display: string;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface DataValidationResult {
  valid: boolean;
  patient_id: number;
  model_code: string;
  available_keys: string[];
  missing_keys: string[];
  ocs_info: Record<string, {
    has_ocs: boolean;
    ocs_id: number | null;
    ocs_status: string | null;
  }>;
}

export interface AvailableModel {
  code: string;
  name: string;
  description: string;
  is_available: boolean;
  available_keys: string[];
  missing_keys: string[];
}

// =============================================================================
// API 함수
// =============================================================================

// 모델 목록 조회
export const getAIModels = async (): Promise<AIModel[]> => {
  const response = await api.get<AIModel[]>('/ai/models/');
  return response.data;
};

// 모델 상세 조회
export const getAIModel = async (code: string): Promise<AIModel> => {
  const response = await api.get<AIModel>(`/ai/models/${code}/`);
  return response.data;
};

// 추론 요청 목록
export const getAIRequests = async (params?: {
  patient_id?: number;
  model_code?: string;
  status?: string;
  my_only?: boolean;
}): Promise<AIInferenceRequest[]> => {
  const response = await api.get<AIInferenceRequest[]>('/ai/requests/', { params });
  return response.data;
};

// 추론 요청 상세
export const getAIRequest = async (id: number): Promise<AIInferenceRequest> => {
  const response = await api.get<AIInferenceRequest>(`/ai/requests/${id}/`);
  return response.data;
};

// 추론 요청 생성
export const createAIRequest = async (data: {
  patient_id: number;
  model_code: string;
  priority?: string;
  ocs_ids?: number[];
}): Promise<AIInferenceRequest> => {
  const response = await api.post<AIInferenceRequest>('/ai/requests/', data);
  return response.data;
};

// 추론 요청 취소
export const cancelAIRequest = async (id: number): Promise<{ message: string }> => {
  const response = await api.post<{ message: string }>(`/ai/requests/${id}/cancel/`);
  return response.data;
};

// 추론 요청 상태 조회
export const getAIRequestStatus = async (id: number): Promise<{
  request_id: string;
  status: string;
  status_display: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  has_result: boolean;
}> => {
  const response = await api.get(`/ai/requests/${id}/status/`);
  return response.data;
};

// 데이터 검증
export const validateAIData = async (data: {
  patient_id: number;
  model_code: string;
}): Promise<DataValidationResult> => {
  const response = await api.post<DataValidationResult>('/ai/requests/validate/', data);
  return response.data;
};

// 결과 검토
export const reviewAIResult = async (resultId: number, data: {
  review_status: 'approved' | 'rejected';
  review_comment?: string;
}): Promise<{ message: string; review_status: string; review_status_display: string }> => {
  const response = await api.post(`/ai/results/${resultId}/review/`, data);
  return response.data;
};

// 환자별 추론 요청 이력
export const getPatientAIRequests = async (patientId: number): Promise<AIInferenceRequest[]> => {
  const response = await api.get<AIInferenceRequest[]>(`/ai/patients/${patientId}/requests/`);
  return response.data;
};

// 환자별 사용 가능한 모델
export const getPatientAvailableModels = async (patientId: number): Promise<AvailableModel[]> => {
  const response = await api.get<AvailableModel[]>(`/ai/patients/${patientId}/available-models/`);
  return response.data;
};
