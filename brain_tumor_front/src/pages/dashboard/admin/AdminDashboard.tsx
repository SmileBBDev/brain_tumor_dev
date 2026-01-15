import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAdminStats } from '@/services/dashboard.api';
import type { AdminStats } from '@/services/dashboard.api';
import { UnifiedCalendar } from '@/components/calendar/UnifiedCalendar';
import DashboardDetailModal, { type ModalType } from './DashboardDetailModal';
import type { OcsStatus } from '@/types/ocs';
import './AdminDashboard.css';

interface ModalState {
  open: boolean;
  type: ModalType;
  title: string;
  roleFilter?: string;
  ocsStatusFilter?: OcsStatus;
}

const USERS_PER_PAGE = 5;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<ModalState>({
    open: false,
    type: 'users',
    title: '',
  });
  const [roleUserPage, setRoleUserPage] = useState(1);

  const openModal = (type: ModalType, title: string, roleFilter?: string, ocsStatusFilter?: OcsStatus) => {
    setModal({ open: true, type, title, roleFilter, ocsStatusFilter });
  };

  const closeModal = () => {
    setModal({ open: false, type: 'users', title: '' });
  };

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

      {/* 요약 카드 */}
      <div className="summary-cards">
        <div
          className="summary-card users clickable"
          onClick={() => openModal('users', '전체 사용자 목록')}
        >
          <div className="card-icon">👥</div>
          <div className="card-content">
            <span className="card-value">{stats.users.total}</span>
            <span className="card-label">전체 사용자</span>
            <span className="card-sub">최근 로그인: {stats.users.recent_logins}명</span>
          </div>
        </div>

        <div
          className="summary-card patients clickable"
          onClick={() => openModal('patients', '전체 환자 목록')}
        >
          <div className="card-icon">🏥</div>
          <div className="card-content">
            <span className="card-value">{stats.patients.total}</span>
            <span className="card-label">전체 환자</span>
            <span className="card-sub">이번 달 신규: {stats.patients.new_this_month}명</span>
          </div>
        </div>

        <div
          className="summary-card ocs clickable"
          onClick={() => openModal('ocs', '전체 OCS 목록')}
        >
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
            <div
              key={status}
              className={`status-item status-${status.toLowerCase()} clickable`}
              onClick={() => openModal('ocs_status', `${status} 상태 OCS 목록`, undefined, status as OcsStatus)}
            >
              <span className="status-label">{status}</span>
              <span className="status-count">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 역할별 사용자 현황 + 캘린더 */}
      <div className="dashboard-main-row">
        <div className="dashboard-section">
          <div className="section-header">
            <h3>역할별 사용자 현황</h3>
            <button
              className="manage-btn"
              onClick={() => navigate('/admin/users')}
            >
              사용자 관리
            </button>
          </div>
          <div className="role-list">
            {(() => {
              const roleEntries = Object.entries(stats.users.by_role);
              const totalPages = Math.ceil(roleEntries.length / USERS_PER_PAGE);
              const startIndex = (roleUserPage - 1) * USERS_PER_PAGE;
              const paginatedRoles = roleEntries.slice(startIndex, startIndex + USERS_PER_PAGE);

              return (
                <>
                  <table className="role-table">
                    <thead>
                      <tr>
                        <th>역할</th>
                        <th>인원</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedRoles.map(([role, count]) => (
                        <tr
                          key={role}
                          className="clickable"
                          onClick={() => openModal('role', `${role} 사용자 목록`, role)}
                        >
                          <td>{role}</td>
                          <td>{count}명</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {totalPages > 1 && (
                    <div className="pagination">
                      <button
                        className="page-btn"
                        disabled={roleUserPage === 1}
                        onClick={() => setRoleUserPage(roleUserPage - 1)}
                      >
                        이전
                      </button>
                      <span className="page-info">{roleUserPage} / {totalPages}</span>
                      <button
                        className="page-btn"
                        disabled={roleUserPage === totalPages}
                        onClick={() => setRoleUserPage(roleUserPage + 1)}
                      >
                        다음
                      </button>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        </div>
        <UnifiedCalendar
          title="관리자 통합 캘린더"
          showManageButton
          onManageClick={() => navigate('/admin/shared-calendar')}
        />
      </div>

      {/* 상세 팝업 모달 */}
      {modal.open && (
        <DashboardDetailModal
          type={modal.type}
          title={modal.title}
          roleFilter={modal.roleFilter}
          ocsStatusFilter={modal.ocsStatusFilter}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
