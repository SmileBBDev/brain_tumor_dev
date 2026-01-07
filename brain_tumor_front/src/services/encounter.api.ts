import { api } from './api';
import type {
  Encounter,
  EncounterListResponse,
  EncounterSearchParams,
  EncounterCreateData,
  EncounterUpdateData,
  EncounterStatistics,
} from '@/types/encounter';

/**
 * 진료 목록 조회
 */
export const getEncounters = async (params?: EncounterSearchParams): Promise<EncounterListResponse> => {
  const response = await api.get<EncounterListResponse>('/encounters/', { params });
  return response.data;
};

/**
 * 진료 상세 조회
 */
export const getEncounter = async (encounterId: number): Promise<Encounter> => {
  const response = await api.get<Encounter>(`/encounters/${encounterId}/`);
  return response.data;
};

/**
 * 진료 등록
 */
export const createEncounter = async (data: EncounterCreateData): Promise<Encounter> => {
  const response = await api.post<Encounter>('/encounters/', data);
  return response.data;
};

/**
 * 진료 수정
 */
export const updateEncounter = async (
  encounterId: number,
  data: EncounterUpdateData
): Promise<Encounter> => {
  const response = await api.patch<Encounter>(`/encounters/${encounterId}/`, data);
  return response.data;
};

/**
 * 진료 삭제 (Soft Delete)
 */
export const deleteEncounter = async (encounterId: number): Promise<void> => {
  await api.delete(`/encounters/${encounterId}/`);
};

/**
 * 진료 완료 처리
 */
export const completeEncounter = async (encounterId: number): Promise<Encounter> => {
  const response = await api.post<Encounter>(`/encounters/${encounterId}/complete/`);
  return response.data;
};

/**
 * 진료 취소
 */
export const cancelEncounter = async (encounterId: number): Promise<Encounter> => {
  const response = await api.post<Encounter>(`/encounters/${encounterId}/cancel/`);
  return response.data;
};

/**
 * 진료 통계 조회
 */
export const getEncounterStatistics = async (): Promise<EncounterStatistics> => {
  const response = await api.get<EncounterStatistics>('/encounters/statistics/');
  return response.data;
};
