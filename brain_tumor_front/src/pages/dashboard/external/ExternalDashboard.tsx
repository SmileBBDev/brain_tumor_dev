import { useState, useEffect } from 'react';
import { getExternalStats } from '@/services/dashboard.api';
import type { ExternalStats } from '@/services/dashboard.api';
import { UnifiedCalendar } from '@/components/calendar/UnifiedCalendar';
import './ExternalDashboard.css';

export default function ExternalDashboard() {
  const [stats, setStats] = useState<ExternalStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getExternalStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch external stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="loading">통계 로딩 중...</div>;
  if (!stats) return <div className="error">통계를 불러올 수 없습니다.</div>;

  return (
    <div className="external-dashboard">
      <h2>외부기관 업로드 현황</h2>

      {/* 요약 카드 */}
      <div className="summary-cards">
        <div className="summary-card lis">
          <h3>🧬 LIS 업로드</h3>
          <div className="card-stats">
            <div className="stat pending">
              <span className="stat-value">{stats.lis_uploads.pending}</span>
              <span className="stat-label">대기 중</span>
            </div>
            <div className="stat completed">
              <span className="stat-value">{stats.lis_uploads.completed}</span>
              <span className="stat-label">완료</span>
            </div>
          </div>
          <span className="card-sub">이번 주: {stats.lis_uploads.total_this_week}건</span>
        </div>

        <div className="summary-card ris">
          <h3>🩻 RIS 업로드</h3>
          <div className="card-stats">
            <div className="stat pending">
              <span className="stat-value">{stats.ris_uploads.pending}</span>
              <span className="stat-label">대기 중</span>
            </div>
            <div className="stat completed">
              <span className="stat-value">{stats.ris_uploads.completed}</span>
              <span className="stat-label">완료</span>
            </div>
          </div>
          <span className="card-sub">이번 주: {stats.ris_uploads.total_this_week}건</span>
        </div>
      </div>

      {/* 최근 업로드 목록 + 캘린더 */}
      <div className="dashboard-main-row">
        <div className="dashboard-section">
          <h3>최근 업로드</h3>
          <table className="upload-table">
            <thead>
              <tr>
                <th>OCS ID</th>
                <th>환자</th>
                <th>유형</th>
                <th>상태</th>
                <th>업로드 시간</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_uploads.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty">업로드 내역이 없습니다.</td>
                </tr>
              ) : (
                stats.recent_uploads.map((upload) => (
                  <tr key={upload.id}>
                    <td>{upload.ocs_id}</td>
                    <td>{upload.patient_name}</td>
                    <td>{upload.job_role}</td>
                    <td>
                      <span className={`status-badge status-${upload.status.toLowerCase()}`}>
                        {upload.status}
                      </span>
                    </td>
                    <td>{new Date(upload.uploaded_at).toLocaleString('ko-KR')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <UnifiedCalendar title="외부기관 통합 캘린더" />
      </div>
    </div>
  );
}
