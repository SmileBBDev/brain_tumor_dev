import { api } from './api';

// System Monitor 통계 타입
export type SystemMonitorStats = {
  server: {
    status: 'ok' | 'warning' | 'error';
    database: string;
  };
  resources: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_gb: number;
    memory_total_gb: number;
    disk_percent: number;
  };
  sessions: {
    active_count: number;
  };
  logins: {
    today_total: number;
    today_success: number;
    today_fail: number;
    today_locked: number;
  };
  errors: {
    count: number;
  };
  timestamp: string;
};

export const getSystemMonitorStats = async (): Promise<SystemMonitorStats> => {
  const response = await api.get('/system/monitor/');
  return response.data;
};
