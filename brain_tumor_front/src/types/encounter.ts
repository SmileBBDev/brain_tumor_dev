// Encounter types

export type EncounterType = 'outpatient' | 'inpatient' | 'emergency';

export type EncounterStatus = 'scheduled' | 'in-progress' | 'completed' | 'cancelled';

export type Department = 'neurology' | 'neurosurgery';

export interface Encounter {
  id: number;
  patient: number;
  patient_name: string;
  patient_number: string;
  patient_gender?: string;
  patient_age?: number;
  encounter_type: EncounterType;
  encounter_type_display: string;
  status: EncounterStatus;
  status_display: string;
  attending_doctor: number;
  attending_doctor_name: string;
  department: Department;
  department_display: string;
  admission_date: string;
  discharge_date: string | null;
  duration_days: number | null;
  chief_complaint: string;
  primary_diagnosis: string;
  secondary_diagnoses: string[];
  is_active?: boolean;
  created_at: string;
  updated_at: string;
}

export interface EncounterListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Encounter[];
}

export interface EncounterSearchParams {
  q?: string;
  encounter_type?: EncounterType;
  status?: EncounterStatus;
  department?: Department;
  attending_doctor?: number;
  patient?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface EncounterCreateData {
  patient: number;
  encounter_type: EncounterType;
  status: EncounterStatus;
  attending_doctor: number;
  department: Department;
  admission_date: string;
  discharge_date?: string | null;
  chief_complaint: string;
  primary_diagnosis?: string;
  secondary_diagnoses?: string[];
}

export interface EncounterUpdateData {
  status?: EncounterStatus;
  attending_doctor?: number;
  department?: Department;
  admission_date?: string;
  discharge_date?: string | null;
  chief_complaint?: string;
  primary_diagnosis?: string;
  secondary_diagnoses?: string[];
}

export interface EncounterStatistics {
  total: number;
  by_type: {
    [key in EncounterType]: {
      label: string;
      count: number;
    };
  };
  by_status: {
    [key in EncounterStatus]: {
      label: string;
      count: number;
    };
  };
  by_department: {
    [key in Department]: {
      label: string;
      count: number;
    };
  };
}
