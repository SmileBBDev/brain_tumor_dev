import { api } from './api';
import type {
  OCSListItem,
  OCSDetail,
  OCSListResponse,
  OCSSearchParams,
  OCSCreateData,
  OCSUpdateData,
  OCSSaveResultRequest,
  OCSSubmitResultRequest,
  OCSConfirmRequest,
  OCSCancelRequest,
  OCSHistory,
} from '@/types/ocs';

/**
 * OCS (Order Communication System) API Service
 */

// =============================================================================
// 기본 CRUD
// =============================================================================

// OCS 목록 조회
export const getOCSList = async (params?: OCSSearchParams): Promise<OCSListResponse> => {
  const response = await api.get<OCSListResponse>('/ocs/', { params });
  return response.data;
};

// OCS 상세 조회
export const getOCS = async (ocsId: number): Promise<OCSDetail> => {
  const response = await api.get<OCSDetail>(`/ocs/${ocsId}/`);
  return response.data;
};

// OCS 생성
export const createOCS = async (data: OCSCreateData): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>('/ocs/', data);
  return response.data;
};

// OCS 수정
export const updateOCS = async (ocsId: number, data: OCSUpdateData): Promise<OCSDetail> => {
  const response = await api.patch<OCSDetail>(`/ocs/${ocsId}/`, data);
  return response.data;
};

// OCS 삭제 (Soft Delete)
export const deleteOCS = async (ocsId: number): Promise<void> => {
  await api.delete(`/ocs/${ocsId}/`);
};

// =============================================================================
// 추가 조회 API
// =============================================================================

// ocs_id로 조회 (예: ocs_0001)
export const getOCSByOcsId = async (ocsId: string): Promise<OCSDetail> => {
  const response = await api.get<OCSDetail>('/ocs/by_ocs_id/', {
    params: { ocs_id: ocsId },
  });
  return response.data;
};

// 미완료 OCS 목록
export const getPendingOCS = async (): Promise<OCSListItem[]> => {
  const response = await api.get<OCSListItem[]>('/ocs/pending/');
  return response.data;
};

// 환자별 OCS 목록
export const getOCSByPatient = async (patientId: number): Promise<OCSListItem[]> => {
  const response = await api.get<OCSListItem[]>('/ocs/by_patient/', {
    params: { patient_id: patientId },
  });
  return response.data;
};

// 의사별 OCS 목록
export const getOCSByDoctor = async (doctorId: number): Promise<OCSListItem[]> => {
  const response = await api.get<OCSListItem[]>('/ocs/by_doctor/', {
    params: { doctor_id: doctorId },
  });
  return response.data;
};

// 작업자별 OCS 목록
export const getOCSByWorker = async (workerId: number): Promise<OCSListItem[]> => {
  const response = await api.get<OCSListItem[]>('/ocs/by_worker/', {
    params: { worker_id: workerId },
  });
  return response.data;
};

// =============================================================================
// 상태 변경 API
// =============================================================================

// 오더 접수 (ORDERED → ACCEPTED)
export const acceptOCS = async (ocsId: number): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/accept/`);
  return response.data;
};

// 작업 시작 (ACCEPTED → IN_PROGRESS)
export const startOCS = async (ocsId: number): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/start/`);
  return response.data;
};

// 결과 임시 저장
export const saveOCSResult = async (
  ocsId: number,
  data: OCSSaveResultRequest
): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/save_result/`, data);
  return response.data;
};

// 결과 제출 (IN_PROGRESS → RESULT_READY)
export const submitOCSResult = async (
  ocsId: number,
  data: OCSSubmitResultRequest
): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/submit_result/`, data);
  return response.data;
};

// 확정 (RESULT_READY → CONFIRMED)
export const confirmOCS = async (ocsId: number, data: OCSConfirmRequest): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/confirm/`, data);
  return response.data;
};

// 취소
export const cancelOCS = async (ocsId: number, data?: OCSCancelRequest): Promise<OCSDetail> => {
  const response = await api.post<OCSDetail>(`/ocs/${ocsId}/cancel/`, data || {});
  return response.data;
};

// =============================================================================
// 이력 조회 API
// =============================================================================

// OCS 이력 조회
export const getOCSHistory = async (ocsId: number): Promise<OCSHistory[]> => {
  const response = await api.get<OCSHistory[]>(`/ocs/${ocsId}/history/`);
  return response.data;
};

// =============================================================================
// localStorage 유틸리티
// =============================================================================

const STORAGE_PREFIX = 'CDSS_LOCAL_STORAGE';

// localStorage 키 생성
export const getLocalStorageKey = (
  jobRole: string,
  ocsId: string,
  type: 'request' | 'result' | 'files' | 'meta'
): string => {
  const role = type === 'request' ? 'DOCTOR' : jobRole;
  return `${STORAGE_PREFIX}:${role}:${ocsId}:${type}`;
};

// Draft 저장
export const saveDraft = <T>(key: string, data: T): void => {
  localStorage.setItem(key, JSON.stringify(data));
};

// Draft 조회
export const getDraft = <T>(key: string): T | null => {
  const data = localStorage.getItem(key);
  return data ? JSON.parse(data) : null;
};

// Draft 삭제
export const removeDraft = (key: string): void => {
  localStorage.removeItem(key);
};

// OCS 관련 모든 Draft 삭제
export const clearOCSDrafts = (jobRole: string, ocsId: string): void => {
  const types: ('request' | 'result' | 'files' | 'meta')[] = ['request', 'result', 'files', 'meta'];
  types.forEach(type => {
    const key = getLocalStorageKey(jobRole, ocsId, type);
    removeDraft(key);
  });
};
