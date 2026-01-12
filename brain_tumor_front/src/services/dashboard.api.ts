import { api } from './api';

// Admin Dashboard 통계
export type AdminStats = {
  users: {
    total: number;
    by_role: Record<string, number>;
    recent_logins: number;
  };
  patients: {
    total: number;
    new_this_month: number;
  };
  ocs: {
    total: number;
    by_status: Record<string, number>;
    pending_count: number;
  };
}

// External Dashboard 통계
export type ExternalStats = {
  lis_uploads: {
    pending: number;
    completed: number;
    total_this_week: number;
  };
  ris_uploads: {
    pending: number;
    completed: number;
    total_this_week: number;
  };
  recent_uploads: Array<{
    id: number;
    ocs_id: string;
    job_role: string;
    status: string;
    uploaded_at: string;
    patient_name: string;
  }>;
}

export const getAdminStats = async (): Promise<AdminStats> => {
  const response = await api.get('/dashboard/admin/stats/');
  return response.data;
};

export const getExternalStats = async (): Promise<ExternalStats> => {
  const response = await api.get('/dashboard/external/stats/');
  return response.data;
};
