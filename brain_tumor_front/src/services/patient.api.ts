import { api } from './api';
import type {
  Patient,
  PatientListResponse,
  PatientSearchParams,
  PatientCreateData,
  PatientUpdateData,
  PatientStatistics,
} from '@/types/patient';

/**
 * Patient API Service
 */

// Get patient list with pagination and filters
export const getPatients = async (params?: PatientSearchParams): Promise<PatientListResponse> => {
  const response = await api.get<PatientListResponse>('/patients/', { params });
  return response.data;
};

// Get patient detail
export const getPatient = async (patientId: number): Promise<Patient> => {
  const response = await api.get<Patient>(`/patients/${patientId}/`);
  return response.data;
};

// Create new patient
export const createPatient = async (data: PatientCreateData): Promise<Patient> => {
  const response = await api.post<Patient>('/patients/', data);
  return response.data;
};

// Update patient
export const updatePatient = async (
  patientId: number,
  data: PatientUpdateData
): Promise<Patient> => {
  const response = await api.put<Patient>(`/patients/${patientId}/`, data);
  return response.data;
};

// Delete patient (soft delete)
export const deletePatient = async (patientId: number): Promise<void> => {
  await api.delete(`/patients/${patientId}/`);
};

// Search patients (autocomplete)
export const searchPatients = async (query: string): Promise<Patient[]> => {
  const response = await api.get<Patient[]>('/patients/search/', {
    params: { q: query },
  });
  return response.data;
};

// Get patient statistics
export const getPatientStatistics = async (): Promise<PatientStatistics> => {
  const response = await api.get<PatientStatistics>('/patients/statistics/');
  return response.data;
};
