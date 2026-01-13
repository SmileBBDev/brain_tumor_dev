/**
 * OCS 통합 처리 현황 대시보드
 * - RIS + LIS 통합 현황 요약
 * - 각 부서별 진행 상황 분포
 * - 전체 Pending/Completed 현황
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOCSProcessStatus } from '@/services/ocs.api';
import type { OCSProcessStatus } from '@/services/ocs.api';
import { useOCSEventCallback } from '@/context/OCSNotificationContext';
import './OCSProcessStatusPage.css';

export default function OCSProcessStatusPage() {
  const navigate = useNavigate();

  const [status, setStatus] = useState<OCSProcessStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 데이터 로드
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getOCSProcessStatus();
      setStatus(response);
    } catch (err) {
      console.error('Failed to load OCS process status:', err);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  // WebSocket 이벤트 콜백 (전역 Context 사용)
  // DB 트랜잭션 완료를 위해 300ms 딜레이 추가
  useOCSEventCallback({
    autoRefresh: () => setTimeout(() => loadData(), 300),
  });

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 퍼센트 계산
  const getPercentage = (value: number, total: number): number => {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
  };

  // 부서별 상세 페이지로 이동
  const handleNavigateToDetail = (type: 'ris' | 'lis') => {
    navigate(`/ocs/${type}/process-status`);
  };

  return (
    <div className="page ocs-process-status-page">
      {/* 헤더 */}
      <header className="page-header">
        <div className="header-left">
          <h2>OCS 처리 현황</h2>
          <span className="subtitle">RIS/LIS 통합 처리 현황을 모니터링합니다</span>
        </div>
        <div className="header-right">
          <button className="refresh-btn" onClick={loadData} disabled={loading}>
            {loading ? '로딩 중...' : '새로고침'}
          </button>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      {status && (
        <>
          {/* 통합 요약 카드 */}
          <section className="combined-summary">
            <div className="summary-card pending">
              <span className="card-icon">⏳</span>
              <div className="card-content">
                <span className="card-label">전체 대기중</span>
                <span className="card-value">{status.combined.total_pending}</span>
              </div>
            </div>
            <div className="summary-card completed">
              <span className="card-icon">✅</span>
              <div className="card-content">
                <span className="card-label">전체 완료</span>
                <span className="card-value">{status.combined.total_completed}</span>
              </div>
            </div>
          </section>

          {/* 부서별 현황 */}
          <section className="department-section">
            {/* RIS 현황 */}
            <div className="department-card" onClick={() => handleNavigateToDetail('ris')}>
              <div className="department-header">
                <h3>
                  <span className="dept-icon">🔬</span>
                  RIS (영상의학)
                </h3>
                <span className="today-count">오늘 {status.ris.total_today}건</span>
              </div>

              <div className="stats-grid">
                <div className="stat-item pending">
                  <span className="stat-label">대기</span>
                  <span className="stat-value">{status.ris.pending}</span>
                </div>
                <div className="stat-item in-progress">
                  <span className="stat-label">진행중</span>
                  <span className="stat-value">{status.ris.in_progress}</span>
                </div>
                <div className="stat-item completed">
                  <span className="stat-label">완료</span>
                  <span className="stat-value">{status.ris.completed}</span>
                </div>
              </div>

              <div className="progress-bar">
                {status.ris.pending > 0 && (
                  <div
                    className="progress-segment pending"
                    style={{
                      width: `${getPercentage(
                        status.ris.pending,
                        status.ris.pending + status.ris.in_progress + status.ris.completed
                      )}%`,
                    }}
                  />
                )}
                {status.ris.in_progress > 0 && (
                  <div
                    className="progress-segment in-progress"
                    style={{
                      width: `${getPercentage(
                        status.ris.in_progress,
                        status.ris.pending + status.ris.in_progress + status.ris.completed
                      )}%`,
                    }}
                  />
                )}
                {status.ris.completed > 0 && (
                  <div
                    className="progress-segment completed"
                    style={{
                      width: `${getPercentage(
                        status.ris.completed,
                        status.ris.pending + status.ris.in_progress + status.ris.completed
                      )}%`,
                    }}
                  />
                )}
              </div>

              <div className="view-detail">상세보기 →</div>
            </div>

            {/* LIS 현황 */}
            <div className="department-card" onClick={() => handleNavigateToDetail('lis')}>
              <div className="department-header">
                <h3>
                  <span className="dept-icon">🧬</span>
                  LIS (진단검사)
                </h3>
                <span className="today-count">오늘 {status.lis.total_today}건</span>
              </div>

              <div className="stats-grid">
                <div className="stat-item pending">
                  <span className="stat-label">대기</span>
                  <span className="stat-value">{status.lis.pending}</span>
                </div>
                <div className="stat-item in-progress">
                  <span className="stat-label">진행중</span>
                  <span className="stat-value">{status.lis.in_progress}</span>
                </div>
                <div className="stat-item completed">
                  <span className="stat-label">완료</span>
                  <span className="stat-value">{status.lis.completed}</span>
                </div>
              </div>

              <div className="progress-bar">
                {status.lis.pending > 0 && (
                  <div
                    className="progress-segment pending"
                    style={{
                      width: `${getPercentage(
                        status.lis.pending,
                        status.lis.pending + status.lis.in_progress + status.lis.completed
                      )}%`,
                    }}
                  />
                )}
                {status.lis.in_progress > 0 && (
                  <div
                    className="progress-segment in-progress"
                    style={{
                      width: `${getPercentage(
                        status.lis.in_progress,
                        status.lis.pending + status.lis.in_progress + status.lis.completed
                      )}%`,
                    }}
                  />
                )}
                {status.lis.completed > 0 && (
                  <div
                    className="progress-segment completed"
                    style={{
                      width: `${getPercentage(
                        status.lis.completed,
                        status.lis.pending + status.lis.in_progress + status.lis.completed
                      )}%`,
                    }}
                  />
                )}
              </div>

              <div className="view-detail">상세보기 →</div>
            </div>
          </section>

          {/* 범례 */}
          <section className="legend-section">
            <div className="legend-item">
              <span className="legend-color pending" />
              <span>대기중</span>
            </div>
            <div className="legend-item">
              <span className="legend-color in-progress" />
              <span>진행중</span>
            </div>
            <div className="legend-item">
              <span className="legend-color completed" />
              <span>완료</span>
            </div>
          </section>
        </>
      )}

      {loading && !status && <div className="loading-message">로딩 중...</div>}
    </div>
  );
}
