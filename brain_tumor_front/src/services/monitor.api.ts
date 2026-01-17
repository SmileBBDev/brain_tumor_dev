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
    login_fail: number;
    login_locked: number;
  };
  acknowledged_alerts: string[];
  timestamp: string;
};

export const getSystemMonitorStats = async (): Promise<SystemMonitorStats> => {
  const response = await api.get('/system/monitor/');
  return response.data;
};

// 모니터링 알림 항목 타입 (배열 형태)
export type MonitorAlertItem = {
  id: string;
  title: string;
  description: string;
  metric?: string;
  threshold?: number | null;
  isBuiltIn: boolean;
  actions: string[];
};

// 모니터링 알림 설정 타입 (배열 형태)
export type MonitorAlertConfig = {
  alerts: MonitorAlertItem[];
};

/**
 * 모니터링 알림 설정 조회
 */
export const getMonitorAlertConfig = async (): Promise<MonitorAlertConfig> => {
  const response = await api.get('/system/config/monitor-alerts/');
  return response.data;
};

/**
 * 모니터링 알림 설정 수정
 */
export const updateMonitorAlertConfig = async (config: MonitorAlertConfig): Promise<void> => {
  await api.put('/system/config/monitor-alerts/', config);
};

/**
 * 경고 확인 처리
 */
export const acknowledgeAlert = async (alertType: string, note?: string): Promise<{
  detail: string;
  alert_type: string;
  acknowledged_at: string;
  acknowledged_by: string;
}> => {
  const response = await api.post('/system/monitor/acknowledge/', {
    alert_type: alertType,
    note: note || '',
  });
  return response.data;
};

/**
 * 경고 확인 취소
 */
export const unacknowledgeAlert = async (alertType: string): Promise<void> => {
  await api.delete('/system/monitor/acknowledge/', {
    params: { alert_type: alertType },
  });
};
