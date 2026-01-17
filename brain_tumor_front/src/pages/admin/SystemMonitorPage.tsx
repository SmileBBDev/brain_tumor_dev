import { useEffect, useState } from 'react';
import {
  getSystemMonitorStats,
  getMonitorAlertConfig,
  updateMonitorAlertConfig,
  acknowledgeAlert,
  type SystemMonitorStats,
  type MonitorAlertConfig,
  type MonitorAlertItem
} from '@/services/monitor.api';
import '@/assets/style/adminPageStyle.css';

type DetailModalType = 'server' | 'cpu' | 'memory' | 'disk' | 'session' | 'login' | 'error' | null;

export default function SystemMonitorPage() {
  const [stats, setStats] = useState<SystemMonitorStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 알림 설정 상태
  const [alertConfig, setAlertConfig] = useState<MonitorAlertConfig | null>(null);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<MonitorAlertConfig | null>(null);
  const [saving, setSaving] = useState(false);

  // 상세 모달 상태
  const [detailModal, setDetailModal] = useState<DetailModalType>(null);

  // 새 경고 추가 모달 상태
  const [showAddAlertModal, setShowAddAlertModal] = useState(false);
  const [newAlert, setNewAlert] = useState<MonitorAlertItem>({
    id: '',
    title: '',
    description: '',
    metric: '',
    threshold: null,
    isBuiltIn: false,
    actions: []
  });

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSystemMonitorStats();
      setStats(data);
    } catch (err) {
      setError('시스템 모니터링 데이터를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlertConfig = async () => {
    try {
      const config = await getMonitorAlertConfig();
      setAlertConfig(config);
    } catch (err) {
      console.error('Failed to fetch alert config:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchAlertConfig();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ok': return '정상';
      case 'warning': return '주의';
      case 'error': return '오류';
      default: return status;
    }
  };

  // 알림 항목 찾기 헬퍼
  const findAlert = (alertId: string): MonitorAlertItem | undefined => {
    return alertConfig?.alerts.find(a => a.id === alertId);
  };

  // 현재 활성화된 알림 목록 계산
  const getActiveAlerts = (): { id: string; alert: MonitorAlertItem; currentValue: number | string; isAcknowledged: boolean }[] => {
    if (!stats || !alertConfig) return [];

    const alerts: { id: string; alert: MonitorAlertItem; currentValue: number | string; isAcknowledged: boolean }[] = [];
    const acknowledgedList = stats.acknowledged_alerts || [];

    // 서버 상태 체크
    if (stats.server.status === 'error') {
      const alert = findAlert('server_error');
      if (alert) {
        alerts.push({
          id: 'server_error',
          alert,
          currentValue: 'DB 연결 실패',
          isAcknowledged: acknowledgedList.includes('server_error')
        });
      }
    } else if (stats.server.status === 'warning') {
      const alert = findAlert('server_warning');
      if (alert) {
        alerts.push({
          id: 'server_warning',
          alert,
          currentValue: '주의',
          isAcknowledged: acknowledgedList.includes('server_warning')
        });
      }
    }

    // CPU 체크
    const cpuAlert = findAlert('cpu_warning');
    if (cpuAlert && cpuAlert.threshold && stats.resources.cpu_percent > cpuAlert.threshold) {
      alerts.push({
        id: 'cpu_warning',
        alert: cpuAlert,
        currentValue: stats.resources.cpu_percent,
        isAcknowledged: acknowledgedList.includes('cpu_warning')
      });
    }

    // 메모리 체크
    const memoryAlert = findAlert('memory_warning');
    if (memoryAlert && memoryAlert.threshold && stats.resources.memory_percent > memoryAlert.threshold) {
      alerts.push({
        id: 'memory_warning',
        alert: memoryAlert,
        currentValue: stats.resources.memory_percent,
        isAcknowledged: acknowledgedList.includes('memory_warning')
      });
    }

    // 디스크 체크
    const diskAlert = findAlert('disk_warning');
    if (diskAlert && diskAlert.threshold && stats.resources.disk_percent > diskAlert.threshold) {
      alerts.push({
        id: 'disk_warning',
        alert: diskAlert,
        currentValue: stats.resources.disk_percent,
        isAcknowledged: acknowledgedList.includes('disk_warning')
      });
    }

    // 오류 발생 체크
    const errorAlert = findAlert('error_warning');
    if (errorAlert && errorAlert.threshold && stats.errors.count > errorAlert.threshold) {
      alerts.push({
        id: 'error_warning',
        alert: errorAlert,
        currentValue: stats.errors.count,
        isAcknowledged: acknowledgedList.includes('error_warning')
      });
    }

    return alerts;
  };

  const openSettingsModal = () => {
    if (alertConfig) {
      setEditingConfig(JSON.parse(JSON.stringify(alertConfig)));
      setShowSettingsModal(true);
    }
  };

  const handleSaveSettings = async () => {
    if (!editingConfig) return;

    setSaving(true);
    try {
      await updateMonitorAlertConfig(editingConfig);
      setAlertConfig(editingConfig);
      setShowSettingsModal(false);
    } catch (err) {
      console.error('Failed to save config:', err);
      alert('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const updateAlertItemInArray = (
    alertId: string,
    field: keyof MonitorAlertItem,
    value: string | number | null | string[] | boolean
  ) => {
    if (!editingConfig) return;
    setEditingConfig({
      ...editingConfig,
      alerts: editingConfig.alerts.map(alert =>
        alert.id === alertId ? { ...alert, [field]: value } : alert
      )
    });
  };

  const handleAddAlert = () => {
    if (!newAlert.id || !newAlert.title) {
      alert('ID와 제목은 필수입니다.');
      return;
    }

    if (editingConfig?.alerts.some(a => a.id === newAlert.id)) {
      alert('이미 존재하는 ID입니다.');
      return;
    }

    if (editingConfig) {
      setEditingConfig({
        ...editingConfig,
        alerts: [...editingConfig.alerts, { ...newAlert }]
      });
    }

    setNewAlert({
      id: '',
      title: '',
      description: '',
      metric: '',
      threshold: null,
      isBuiltIn: false,
      actions: []
    });
    setShowAddAlertModal(false);
  };

  const handleDeleteAlert = (alertId: string) => {
    if (!editingConfig) return;
    const alert = editingConfig.alerts.find(a => a.id === alertId);
    if (alert?.isBuiltIn) {
      window.alert('기본 알림은 삭제할 수 없습니다.');
      return;
    }
    if (window.confirm('이 알림을 삭제하시겠습니까?')) {
      setEditingConfig({
        ...editingConfig,
        alerts: editingConfig.alerts.filter(a => a.id !== alertId)
      });
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId);
      await fetchStats(); // 새로고침
    } catch (err) {
      console.error('Failed to acknowledge:', err);
      alert('확인 처리에 실패했습니다.');
    }
  };

  const activeAlerts = getActiveAlerts();
  const unacknowledgedAlerts = activeAlerts.filter(a => !a.isAcknowledged);

  // 알림에 대한 임계값 가져오기
  const getThreshold = (alertId: string): number => {
    const alert = findAlert(alertId);
    return alert?.threshold || 90;
  };

  if (loading && !stats) {
    return (
      <div className="admin-page">
        <div className="monitor-loading">데이터를 불러오는 중...</div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="admin-page">
        <div className="monitor-error">
          <p>{error}</p>
          <button onClick={fetchStats}>다시 시도</button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      {/* 헤더 */}
      <div className="monitor-header">
        <h2>시스템 모니터링</h2>
        <div className="header-buttons">
          <button className="settings-btn" onClick={openSettingsModal}>
            설정
          </button>
        </div>
      </div>

      {/* 모니터링 그리드 */}
      <div className="monitor-grid">
        {/* 서버 상태 */}
        <div
          className={`monitor-card clickable ${stats?.server.status || 'ok'}`}
          onClick={() => setDetailModal('server')}
        >
          <h3>서버 상태</h3>
          <p>{getStatusText(stats?.server.status || 'ok')}</p>
          <span className="sub-text">DB: {stats?.server.database || '-'}</span>
        </div>

        {/* CPU */}
        <div
          className={`monitor-card clickable ${(stats?.resources.cpu_percent || 0) > getThreshold('cpu_warning') ? 'warning' : 'ok'}`}
          onClick={() => setDetailModal('cpu')}
        >
          <h3>CPU 사용률</h3>
          <p>{stats?.resources.cpu_percent || 0}%</p>
          <span className="sub-text">기준: {getThreshold('cpu_warning')}%</span>
        </div>

        {/* Memory */}
        <div
          className={`monitor-card clickable ${(stats?.resources.memory_percent || 0) > getThreshold('memory_warning') ? 'warning' : 'ok'}`}
          onClick={() => setDetailModal('memory')}
        >
          <h3>메모리 사용률</h3>
          <p>{stats?.resources.memory_percent || 0}%</p>
          <span className="sub-text">
            {stats?.resources.memory_used_gb || 0}GB / {stats?.resources.memory_total_gb || 0}GB
          </span>
        </div>

        {/* 디스크 */}
        <div
          className={`monitor-card clickable ${(stats?.resources.disk_percent || 0) > getThreshold('disk_warning') ? 'warning' : 'ok'}`}
          onClick={() => setDetailModal('disk')}
        >
          <h3>디스크 사용률</h3>
          <p>{stats?.resources.disk_percent || 0}%</p>
          <span className="sub-text">기준: {getThreshold('disk_warning')}%</span>
        </div>

        {/* 활성 세션 */}
        <div
          className="monitor-card clickable"
          onClick={() => setDetailModal('session')}
        >
          <h3>활성 세션</h3>
          <p>{stats?.sessions.active_count || 0}</p>
          <span className="sub-text">최근 30분 기준</span>
        </div>

        {/* 금일 로그인 */}
        <div
          className="monitor-card clickable"
          onClick={() => setDetailModal('login')}
        >
          <h3>금일 로그인</h3>
          <p>{stats?.logins.today_total || 0}</p>
          <span className="sub-text">
            성공 {stats?.logins.today_success || 0} / 실패 {stats?.logins.today_fail || 0}
          </span>
        </div>

        {/* 오류 발생 */}
        <div
          className={`monitor-card clickable ${(stats?.errors.count || 0) > getThreshold('error_warning') ? 'warning' : 'ok'}`}
          onClick={() => setDetailModal('error')}
        >
          <h3>오류 발생</h3>
          <p>{stats?.errors.count || 0}건</p>
          <span className="sub-text">기준: {getThreshold('error_warning')}건</span>
        </div>

        {/* 마지막 갱신 */}
        <div className="monitor-card">
          <h3>마지막 갱신</h3>
          <p style={{ fontSize: '14px' }}>
            {stats?.timestamp
              ? new Date(stats.timestamp).toLocaleTimeString('ko-KR')
              : '-'}
          </p>
          <span className="sub-text">30초마다 자동 갱신</span>
        </div>
      </div>

      {/* 활성 알림 표시 (확인되지 않은 것만) */}
      {unacknowledgedAlerts.length > 0 && (
        <div className="alert-section">
          <h3>주의/경고 상태 안내</h3>
          {unacknowledgedAlerts.map(({ id, alert, currentValue }) => (
            <div key={id} className="alert-box">
              <div className="alert-header">
                <div className="alert-title">{alert.title}</div>
                <button
                  className="acknowledge-btn"
                  onClick={() => handleAcknowledge(id)}
                >
                  확인 완료
                </button>
              </div>
              <div className="alert-description">
                {/* 현재 수치와 임계값 표시 */}
                {id === 'cpu_warning' && (
                  <>현재 CPU 사용률: <strong>{currentValue}%</strong> (기준: {alert.threshold}%)</>
                )}
                {id === 'memory_warning' && (
                  <>현재 메모리 사용률: <strong>{currentValue}%</strong> ({stats?.resources.memory_used_gb}GB / {stats?.resources.memory_total_gb}GB, 기준: {alert.threshold}%)</>
                )}
                {id === 'disk_warning' && (
                  <>현재 디스크 사용률: <strong>{currentValue}%</strong> (기준: {alert.threshold}%)</>
                )}
                {id === 'error_warning' && (
                  <>로그인 실패 {stats?.errors.login_fail}건 + 계정 잠금 {stats?.errors.login_locked}건 = 총 <strong>{currentValue}건</strong> (기준: {alert.threshold}건)</>
                )}
                {(id === 'server_warning' || id === 'server_error') && (
                  <>{alert.description}</>
                )}
              </div>
              <ul className="alert-actions">
                {alert.actions.map((action, idx) => (
                  <li key={idx}>{action}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* 상세 모달 - 서버 */}
      {detailModal === 'server' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>서버 상태 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>상태</label>
                <span className={`status-badge ${stats?.server.status}`}>
                  {getStatusText(stats?.server.status || 'ok')}
                </span>
              </div>
              <div className="detail-item">
                <label>데이터베이스</label>
                <span>{stats?.server.database === 'connected' ? '연결됨' : '연결 끊김'}</span>
              </div>
              <div className="detail-item">
                <label>마지막 확인</label>
                <span>{stats?.timestamp ? new Date(stats.timestamp).toLocaleString('ko-KR') : '-'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - CPU */}
      {detailModal === 'cpu' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>CPU 상태 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>현재 사용률</label>
                <span className="value-large">{stats?.resources.cpu_percent || 0}%</span>
              </div>
              <div className="detail-item">
                <label>경고 임계값</label>
                <span>{getThreshold('cpu_warning')}%</span>
              </div>
              <div className="detail-item">
                <label>상태</label>
                <span className={`status-badge ${(stats?.resources.cpu_percent || 0) > getThreshold('cpu_warning') ? 'warning' : 'ok'}`}>
                  {(stats?.resources.cpu_percent || 0) > getThreshold('cpu_warning') ? '주의' : '정상'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - 메모리 */}
      {detailModal === 'memory' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>메모리 상태 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>현재 사용률</label>
                <span className="value-large">{stats?.resources.memory_percent || 0}%</span>
              </div>
              <div className="detail-item">
                <label>사용량</label>
                <span>{stats?.resources.memory_used_gb || 0}GB / {stats?.resources.memory_total_gb || 0}GB</span>
              </div>
              <div className="detail-item">
                <label>경고 임계값</label>
                <span>{getThreshold('memory_warning')}%</span>
              </div>
              <div className="detail-item">
                <label>상태</label>
                <span className={`status-badge ${(stats?.resources.memory_percent || 0) > getThreshold('memory_warning') ? 'warning' : 'ok'}`}>
                  {(stats?.resources.memory_percent || 0) > getThreshold('memory_warning') ? '주의' : '정상'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - 디스크 */}
      {detailModal === 'disk' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>디스크 상태 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>현재 사용률</label>
                <span className="value-large">{stats?.resources.disk_percent || 0}%</span>
              </div>
              <div className="detail-item">
                <label>경고 임계값</label>
                <span>{getThreshold('disk_warning')}%</span>
              </div>
              <div className="detail-item">
                <label>상태</label>
                <span className={`status-badge ${(stats?.resources.disk_percent || 0) > getThreshold('disk_warning') ? 'warning' : 'ok'}`}>
                  {(stats?.resources.disk_percent || 0) > getThreshold('disk_warning') ? '주의' : '정상'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - 세션 */}
      {detailModal === 'session' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>활성 세션 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>현재 활성 세션</label>
                <span className="value-large">{stats?.sessions.active_count || 0}명</span>
              </div>
              <div className="detail-item">
                <label>기준</label>
                <span>최근 30분 이내 활동한 사용자</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - 로그인 */}
      {detailModal === 'login' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>금일 로그인 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>총 로그인 시도</label>
                <span className="value-large">{stats?.logins.today_total || 0}건</span>
              </div>
              <div className="detail-item">
                <label>로그인 성공</label>
                <span className="success">{stats?.logins.today_success || 0}건</span>
              </div>
              <div className="detail-item">
                <label>로그인 실패</label>
                <span className="fail">{stats?.logins.today_fail || 0}건</span>
              </div>
              <div className="detail-item">
                <label>계정 잠금</label>
                <span className="fail">{stats?.logins.today_locked || 0}건</span>
              </div>
              <div className="detail-info">
                금일 00:00 기준으로 집계됩니다.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상세 모달 - 오류 발생 */}
      {detailModal === 'error' && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>오류 발생 상세</h3>
              <button className="close-btn" onClick={() => setDetailModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-item">
                <label>총 오류 발생</label>
                <span className="value-large">{stats?.errors.count || 0}건</span>
              </div>
              <div className="detail-item">
                <label>로그인 실패</label>
                <span>{stats?.errors.login_fail || 0}건</span>
              </div>
              <div className="detail-item">
                <label>계정 잠금</label>
                <span>{stats?.errors.login_locked || 0}건</span>
              </div>
              <div className="detail-item">
                <label>경고 임계값</label>
                <span>{getThreshold('error_warning')}건 초과 시 경고</span>
              </div>
              <div className="detail-item">
                <label>상태</label>
                <span className={`status-badge ${(stats?.errors.count || 0) > getThreshold('error_warning') ? 'warning' : 'ok'}`}>
                  {(stats?.errors.count || 0) > getThreshold('error_warning') ? '주의' : '정상'}
                </span>
              </div>
              <div className="detail-info">
                금일 00:00 기준으로 집계됩니다.
              </div>
              {(stats?.errors.count || 0) > getThreshold('error_warning') && (
                <div className="detail-actions">
                  <button
                    className="acknowledge-btn"
                    onClick={() => {
                      handleAcknowledge('error_warning');
                      setDetailModal(null);
                    }}
                  >
                    확인 완료 (경고 해제)
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 설정 모달 */}
      {showSettingsModal && editingConfig && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-content settings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>알림 설정</h3>
              <button className="close-btn" onClick={() => setShowSettingsModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="settings-actions">
                <button className="add-alert-btn" onClick={() => setShowAddAlertModal(true)}>
                  + 새 경고 추가
                </button>
              </div>
              {editingConfig.alerts.map((alert) => (
                <div key={alert.id} className="alert-config-item">
                  <div className="config-header">
                    <h4>{alert.title}</h4>
                    {!alert.isBuiltIn && (
                      <button
                        className="delete-alert-btn"
                        onClick={() => handleDeleteAlert(alert.id)}
                      >
                        삭제
                      </button>
                    )}
                  </div>
                  <div className="config-field">
                    <label>제목</label>
                    <input
                      type="text"
                      value={alert.title}
                      onChange={(e) => updateAlertItemInArray(alert.id, 'title', e.target.value)}
                    />
                  </div>
                  <div className="config-field">
                    <label>설명</label>
                    <textarea
                      value={alert.description}
                      onChange={(e) => updateAlertItemInArray(alert.id, 'description', e.target.value)}
                    />
                  </div>
                  {alert.threshold !== null && alert.threshold !== undefined && (
                    <div className="config-field">
                      <label>임계값 {alert.metric === 'error_count' ? '(건)' : '(%)'}</label>
                      <input
                        type="number"
                        value={alert.threshold}
                        onChange={(e) => updateAlertItemInArray(alert.id, 'threshold', parseInt(e.target.value) || 0)}
                      />
                    </div>
                  )}
                  <div className="config-field">
                    <label>대처 방안 (줄바꿈으로 구분)</label>
                    <textarea
                      value={alert.actions.join('\n')}
                      onChange={(e) => updateAlertItemInArray(alert.id, 'actions', e.target.value.split('\n').filter(a => a.trim()))}
                      rows={3}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setShowSettingsModal(false)}>
                취소
              </button>
              <button className="save-btn" onClick={handleSaveSettings} disabled={saving}>
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 새 경고 추가 모달 */}
      {showAddAlertModal && (
        <div className="modal-overlay" onClick={() => setShowAddAlertModal(false)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>새 경고 추가</h3>
              <button className="close-btn" onClick={() => setShowAddAlertModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="config-field">
                <label>ID (고유값)</label>
                <input
                  type="text"
                  value={newAlert.id}
                  onChange={(e) => setNewAlert({ ...newAlert, id: e.target.value })}
                  placeholder="예: custom_warning_1"
                />
              </div>
              <div className="config-field">
                <label>제목</label>
                <input
                  type="text"
                  value={newAlert.title}
                  onChange={(e) => setNewAlert({ ...newAlert, title: e.target.value })}
                  placeholder="예: 사용자 정의 경고"
                />
              </div>
              <div className="config-field">
                <label>설명</label>
                <textarea
                  value={newAlert.description}
                  onChange={(e) => setNewAlert({ ...newAlert, description: e.target.value })}
                  placeholder="경고 설명..."
                />
              </div>
              <div className="config-field">
                <label>대처 방안 (줄바꿈으로 구분)</label>
                <textarea
                  value={newAlert.actions.join('\n')}
                  onChange={(e) => setNewAlert({ ...newAlert, actions: e.target.value.split('\n').filter(a => a.trim()) })}
                  rows={3}
                  placeholder="각 줄에 하나씩 입력"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-btn" onClick={() => setShowAddAlertModal(false)}>
                취소
              </button>
              <button className="save-btn" onClick={handleAddAlert}>
                추가
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
