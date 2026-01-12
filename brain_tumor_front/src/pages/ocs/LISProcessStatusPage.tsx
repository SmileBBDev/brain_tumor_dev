/**
 * LIS 전체 검사 현황 대시보드
 * - 현황 요약: 전체 검사 건수, Pending/진행중/완료 건수
 * - 진행 상황 분포 그래프
 * - 지연 검사 알림: 일정 시간 초과한 검사 목록
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOCSList } from '@/services/ocs.api';
import type { OCSListItem } from '@/types/ocs';
import { useOCSEventCallback } from '@/context/OCSNotificationContext';
import './LISProcessStatusPage.css';

// 상태별 설정
const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  ORDERED: { label: 'Pending', color: '#f39c12' },
  ACCEPTED: { label: 'Pending', color: '#f39c12' },
  IN_PROGRESS: { label: '진행중', color: '#3498db' },
  RESULT_READY: { label: '진행중', color: '#3498db' },
  CONFIRMED: { label: '완료', color: '#27ae60' },
  CANCELLED: { label: '취소', color: '#95a5a6' },
};

// 지연 기준 (분)
const DELAY_THRESHOLD_MINUTES = 60;

// 날짜 포맷
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 경과 시간 계산
const getElapsedMinutes = (dateStr: string): number => {
  const date = new Date(dateStr);
  const now = new Date();
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
};

// 경과 시간 표시
const formatElapsedTime = (minutes: number): string => {
  if (minutes < 60) return `${minutes}분`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}시간 ${mins}분` : `${hours}시간`;
};

export default function LISProcessStatusPage() {
  const navigate = useNavigate();

  // 상태
  const [ocsItems, setOcsItems] = useState<OCSListItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 데이터 로드 (useOCSEventCallback보다 먼저 정의해야 함)
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getOCSList({
        job_role: 'LIS',
        page_size: 200, // 전체 조회
      });
      setOcsItems(response.results || []);
    } catch (error) {
      console.error('Failed to load LIS data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // WebSocket 이벤트 콜백 (전역 Context 사용)
  useOCSEventCallback({
    autoRefresh: loadData,
  });

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 통계 계산
  const stats = useMemo(() => {
    const result = {
      total: ocsItems.length,
      pending: 0,
      inProgress: 0,
      completed: 0,
      cancelled: 0,
    };

    ocsItems.forEach((item) => {
      switch (item.ocs_status) {
        case 'ORDERED':
        case 'ACCEPTED':
          result.pending++;
          break;
        case 'IN_PROGRESS':
        case 'RESULT_READY':
          result.inProgress++;
          break;
        case 'CONFIRMED':
          result.completed++;
          break;
        case 'CANCELLED':
          result.cancelled++;
          break;
      }
    });

    return result;
  }, [ocsItems]);

  // 지연된 항목
  const delayedItems = useMemo(() => {
    return ocsItems
      .filter((item) => {
        if (item.ocs_status === 'CONFIRMED' || item.ocs_status === 'CANCELLED') {
          return false;
        }
        const elapsed = getElapsedMinutes(item.created_at);
        return elapsed > DELAY_THRESHOLD_MINUTES;
      })
      .sort((a, b) => {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      })
      .slice(0, 10);
  }, [ocsItems]);

  // 진행률 퍼센트
  const getPercentage = (value: number): number => {
    if (stats.total === 0) return 0;
    return Math.round((value / stats.total) * 100);
  };

  // 행 클릭
  const handleRowClick = (item: OCSListItem) => {
    navigate(`/ocs/lis/${item.id}`);
  };

  return (
    <div className="page lis-process-status-page">
      {/* Toast 알림은 AppLayout에서 전역 렌더링 */}

      {/* 헤더 */}
      <header className="page-header">
        <h2>전체 검사 현황</h2>
        <span className="subtitle">검사실 검사 진행 상황을 모니터링합니다</span>
        <button className="refresh-btn" onClick={loadData} disabled={loading}>
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </header>

      {/* 요약 카드 */}
      <section className="summary-cards">
        <div className="summary-card total">
          <span className="card-icon">📊</span>
          <div className="card-content">
            <span className="card-label">전체 검사</span>
            <span className="card-value">{stats.total}</span>
          </div>
        </div>
        <div className="summary-card pending">
          <span className="card-icon">⏳</span>
          <div className="card-content">
            <span className="card-label">Pending</span>
            <span className="card-value">{stats.pending}</span>
          </div>
        </div>
        <div className="summary-card in-progress">
          <span className="card-icon">🔬</span>
          <div className="card-content">
            <span className="card-label">진행중</span>
            <span className="card-value">{stats.inProgress}</span>
          </div>
        </div>
        <div className="summary-card completed">
          <span className="card-icon">✅</span>
          <div className="card-content">
            <span className="card-label">완료</span>
            <span className="card-value">{stats.completed}</span>
          </div>
        </div>
      </section>

      {/* 진행 상황 분포 */}
      <section className="progress-section">
        <h3>검사 상태 분포</h3>
        <div className="progress-chart">
          <div className="progress-bar">
            {stats.pending > 0 && (
              <div
                className="progress-segment pending"
                style={{ width: `${getPercentage(stats.pending)}%` }}
                title={`Pending: ${stats.pending}건 (${getPercentage(stats.pending)}%)`}
              />
            )}
            {stats.inProgress > 0 && (
              <div
                className="progress-segment in-progress"
                style={{ width: `${getPercentage(stats.inProgress)}%` }}
                title={`진행중: ${stats.inProgress}건 (${getPercentage(stats.inProgress)}%)`}
              />
            )}
            {stats.completed > 0 && (
              <div
                className="progress-segment completed"
                style={{ width: `${getPercentage(stats.completed)}%` }}
                title={`완료: ${stats.completed}건 (${getPercentage(stats.completed)}%)`}
              />
            )}
            {stats.cancelled > 0 && (
              <div
                className="progress-segment cancelled"
                style={{ width: `${getPercentage(stats.cancelled)}%` }}
                title={`취소: ${stats.cancelled}건 (${getPercentage(stats.cancelled)}%)`}
              />
            )}
          </div>
          <div className="progress-legend">
            <div className="legend-item">
              <span className="legend-color pending" />
              <span>Pending ({stats.pending}건, {getPercentage(stats.pending)}%)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color in-progress" />
              <span>진행중 ({stats.inProgress}건, {getPercentage(stats.inProgress)}%)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color completed" />
              <span>완료 ({stats.completed}건, {getPercentage(stats.completed)}%)</span>
            </div>
            {stats.cancelled > 0 && (
              <div className="legend-item">
                <span className="legend-color cancelled" />
                <span>취소 ({stats.cancelled}건, {getPercentage(stats.cancelled)}%)</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 지연 검사 알림 */}
      <section className="delayed-section">
        <h3>
          지연 검사 알림
          <span className="threshold-info">({DELAY_THRESHOLD_MINUTES}분 초과)</span>
        </h3>
        {delayedItems.length === 0 ? (
          <div className="empty-message">지연된 검사가 없습니다.</div>
        ) : (
          <table className="delayed-table">
            <thead>
              <tr>
                <th>OCS ID</th>
                <th>환자명</th>
                <th>환자번호</th>
                <th>검사 유형</th>
                <th>상태</th>
                <th>접수 시간</th>
                <th>경과 시간</th>
                <th>작업자</th>
                <th>요청의사</th>
              </tr>
            </thead>
            <tbody>
              {delayedItems.map((item) => {
                const elapsed = getElapsedMinutes(item.created_at);
                const isUrgent = elapsed > DELAY_THRESHOLD_MINUTES * 2;

                return (
                  <tr
                    key={item.id}
                    className={`clickable-row ${isUrgent ? 'urgent-row' : ''}`}
                    onClick={() => handleRowClick(item)}
                  >
                    <td className="ocs-id">{item.ocs_id}</td>
                    <td className="patient-name">{item.patient.name}</td>
                    <td>{item.patient.patient_number}</td>
                    <td>{item.job_type}</td>
                    <td>
                      <span className={`status-badge ${item.ocs_status.toLowerCase()}`}>
                        {STATUS_CONFIG[item.ocs_status]?.label || item.ocs_status_display}
                      </span>
                    </td>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td className={`elapsed-time ${isUrgent ? 'urgent' : 'delayed'}`}>
                      {formatElapsedTime(elapsed)}
                    </td>
                    <td>{item.worker?.name || '-'}</td>
                    <td>{item.doctor?.name || '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
