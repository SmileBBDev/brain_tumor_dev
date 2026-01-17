import { useEffect, useState } from 'react';
import { getSystemMonitorStats, type SystemMonitorStats } from '@/services/monitor.api';

export default function SystemMonitorPage() {
  const [stats, setStats] = useState<SystemMonitorStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchStats();
    // 30초마다 자동 갱신
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
      <div className="monitor-grid">
        {/* 서버 상태 */}
        <div className={`monitor-card ${stats?.server.status || 'ok'}`}>
          <h3>서버 상태</h3>
          <p>{getStatusText(stats?.server.status || 'ok')}</p>
          <span className="sub-text">DB: {stats?.server.database || '-'}</span>
        </div>

        {/* CPU */}
        <div className={`monitor-card ${(stats?.resources.cpu_percent || 0) > 90 ? 'warning' : 'ok'}`}>
          <h3>CPU 사용률</h3>
          <p>{stats?.resources.cpu_percent || 0}%</p>
        </div>

        {/* Memory */}
        <div className={`monitor-card ${(stats?.resources.memory_percent || 0) > 90 ? 'warning' : 'ok'}`}>
          <h3>메모리 사용률</h3>
          <p>{stats?.resources.memory_percent || 0}%</p>
          <span className="sub-text">
            {stats?.resources.memory_used_gb || 0}GB / {stats?.resources.memory_total_gb || 0}GB
          </span>
        </div>

        {/* 디스크 */}
        <div className={`monitor-card ${(stats?.resources.disk_percent || 0) > 90 ? 'warning' : 'ok'}`}>
          <h3>디스크 사용률</h3>
          <p>{stats?.resources.disk_percent || 0}%</p>
        </div>

        {/* 활성 세션 */}
        <div className="monitor-card">
          <h3>활성 세션</h3>
          <p>{stats?.sessions.active_count || 0}</p>
          <span className="sub-text">최근 30분 기준</span>
        </div>

        {/* 금일 로그인 */}
        <div className="monitor-card">
          <h3>금일 로그인</h3>
          <p>{stats?.logins.today_total || 0}</p>
          <span className="sub-text">
            성공 {stats?.logins.today_success || 0} / 실패 {stats?.logins.today_fail || 0}
          </span>
        </div>

        {/* 오류 발생 */}
        <div className={`monitor-card ${(stats?.errors.count || 0) > 0 ? 'warning' : 'ok'}`}>
          <h3>오류 발생</h3>
          <p>{stats?.errors.count || 0}건</p>
          <span className="sub-text">로그인 실패 + 잠금</span>
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
    </div>
  );
}
