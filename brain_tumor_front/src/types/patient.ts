// Patient types

export type Gender = 'M' | 'F' | 'O';

export type PatientStatus = 'active' | 'inactive' | 'deceased';

export type BloodType = 'A+' | 'A-' | 'B+' | 'B-' | 'O+' | 'O-' | 'AB+' | 'AB-';

export interface Patient {
  id: number;
  patient_number: string;
  name: string;
  birth_date: string;
  gender: Gender;
  phone: string;
  email: string | null;
  address: string;
  blood_type: BloodType | null;
  allergies: string[];
  chronic_diseases: string[];
  status: PatientStatus;
  age: number;
  registered_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface PatientListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Patient[];
}

export interface PatientSearchParams {
  q?: string;
  status?: PatientStatus;
  gender?: Gender;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface PatientCreateData {
  name: string;
  birth_date: string;
  gender: Gender;
  phone: string;
  email?: string;
  address?: string;
  ssn: string;
  blood_type?: BloodType;
  allergies?: string[];
  chronic_diseases?: string[];
}

export interface PatientUpdateData {
  name?: string;
  phone?: string;
  email?: string;
  address?: string;
  blood_type?: BloodType;
  allergies?: string[];
  chronic_diseases?: string[];
  status?: PatientStatus;
}

export interface PatientStatistics {
  total: number;
  active: number;
  inactive: number;
  by_gender: {
    gender: Gender;
    count: number;
  }[];
}
