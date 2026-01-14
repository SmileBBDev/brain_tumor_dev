import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAdminStats } from '@/services/dashboard.api';
import type { AdminStats } from '@/services/dashboard.api';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getAdminStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch admin stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="loading">통계 로딩 중...</div>;
  if (!stats) return <div className="error">통계를 불러올 수 없습니다.</div>;

  return (
    <div className="admin-dashboard">
      <h2>관리자 대시보드</h2>

      {/* 관리 버튼 영역 */}
      <div className="admin-actions">
        <button
          className="action-btn calendar-btn"
          onClick={() => navigate('/admin/shared-calendar')}
        >
          <span className="btn-icon">📅</span>
          <span className="btn-text">권한별 캘린더 관리</span>
        </button>
      </div>

      {/* 요약 카드 */}
      <div className="summary-cards">
        <div className="summary-card users">
          <div className="card-icon">👥</div>
          <div className="card-content">
            <span className="card-value">{stats.users.total}</span>
            <span className="card-label">전체 사용자</span>
            <span className="card-sub">최근 로그인: {stats.users.recent_logins}명</span>
          </div>
        </div>

        <div className="summary-card patients">
          <div className="card-icon">🏥</div>
          <div className="card-content">
            <span className="card-value">{stats.patients.total}</span>
            <span className="card-label">전체 환자</span>
            <span className="card-sub">이번 달 신규: {stats.patients.new_this_month}명</span>
          </div>
        </div>

        <div className="summary-card ocs">
          <div className="card-icon">📋</div>
          <div className="card-content">
            <span className="card-value">{stats.ocs.total}</span>
            <span className="card-label">OCS 현황</span>
            <span className="card-sub">대기 중: {stats.ocs.pending_count}건</span>
          </div>
        </div>
      </div>

      {/* OCS 상태별 현황 */}
      <div className="dashboard-section">
        <h3>OCS 상태별 현황</h3>
        <div className="status-grid">
          {Object.entries(stats.ocs.by_status).map(([status, count]) => (
            <div key={status} className={`status-item status-${status.toLowerCase()}`}>
              <span className="status-label">{status}</span>
              <span className="status-count">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 역할별 사용자 현황 */}
      <div className="dashboard-section">
        <h3>역할별 사용자</h3>
        <div className="role-grid">
          {Object.entries(stats.users.by_role).map(([role, count]) => (
            <div key={role} className="role-item">
              <span className="role-name">{role}</span>
              <span className="role-count">{count}명</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
