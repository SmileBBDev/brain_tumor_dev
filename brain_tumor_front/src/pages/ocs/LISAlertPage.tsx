/**
 * LIS 검사 결과 Alert 화면 (P.90)
 * - 이상(Abnormal) 또는 치명적(Critical) 검사 결과 실시간 알림
 * - Alert 리스트: 발생 시간, 환자명, 검사 항목, 중요도, 상태
 * - 확인 처리 및 상세 보기 액션
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOCSList, getOCS } from '@/services/ocs.api';
import type { OCSListItem, OCSDetail, LISWorkerResult } from '@/types/ocs';
import Pagination from '@/layout/Pagination';
import { useOCSNotification } from '@/hooks/useOCSNotification';
import OCSNotificationToast from '@/components/OCSNotificationToast';
import './LISAlertPage.css';

// Alert 중요도 타입
type AlertSeverity = 'critical' | 'high' | 'normal';

// Alert 상태 타입
type AlertStatus = 'unconfirmed' | 'confirmed';

// Alert 아이템 인터페이스
interface AlertItem {
  id: number;
  ocsId: string;
  ocsPk: number;
  patientName: string;
  patientNumber: string;
  testName: string;
  testCode: string;
  resultValue: string;
  referenceRange: string;
  severity: AlertSeverity;
  status: AlertStatus;
  timestamp: string;
}

// 중요도 설정
const SEVERITY_CONFIG: Record<AlertSeverity, { label: string; className: string }> = {
  critical: { label: 'Critical', className: 'severity-critical' },
  high: { label: 'High', className: 'severity-high' },
  normal: { label: 'Normal', className: 'severity-normal' },
};

// 상태 설정
const STATUS_CONFIG: Record<AlertStatus, { label: string; className: string }> = {
  unconfirmed: { label: '미확인', className: 'status-unconfirmed' },
  confirmed: { label: '확인됨', className: 'status-confirmed' },
};

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

export default function LISAlertPage() {
  const navigate = useNavigate();

  // 상태
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // 필터
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | 'all'>('all');

  // 확인된 Alert ID 목록 (로컬 상태)
  const [confirmedAlerts, setConfirmedAlerts] = useState<Set<number>>(() => {
    const saved = localStorage.getItem('lis_confirmed_alerts');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  // WebSocket 알림
  const { notifications, removeNotification } = useOCSNotification({
    autoRefresh: () => loadAlerts(),
  });

  // Alert 데이터 로드
  const loadAlerts = useCallback(async () => {
    setLoading(true);
    try {
      // LIS OCS 중 결과가 있는 것들 조회
      const response = await getOCSList({
        job_role: 'LIS',
        page: 1,
        page_size: 100, // 전체 조회 후 필터링
      });

      const alertItems: AlertItem[] = [];

      // 각 OCS에서 이상 결과 추출
      for (const ocs of response.results) {
        if (ocs.ocs_status === 'RESULT_READY' || ocs.ocs_status === 'CONFIRMED') {
          try {
            const detail = await getOCS(ocs.id);
            const workerResult = detail.worker_result as LISWorkerResult;

            if (workerResult?.test_results) {
              // 이상 결과만 필터링
              const abnormalResults = workerResult.test_results.filter(
                (test) => test.is_abnormal
              );

              abnormalResults.forEach((test) => {
                // 중요도 판단 (간단한 로직 - 실제로는 더 정교한 로직 필요)
                const severity = determineSeverity(test.value, test.reference);

                alertItems.push({
                  id: alertItems.length + 1,
                  ocsId: ocs.ocs_id,
                  ocsPk: ocs.id,
                  patientName: ocs.patient.name,
                  patientNumber: ocs.patient.patient_number,
                  testName: test.name,
                  testCode: test.code,
                  resultValue: `${test.value} ${test.unit}`,
                  referenceRange: test.reference,
                  severity,
                  status: confirmedAlerts.has(ocs.id) ? 'confirmed' : 'unconfirmed',
                  timestamp: detail.result_ready_at || detail.updated_at,
                });
              });
            }
          } catch (error) {
            console.error(`Failed to fetch OCS detail ${ocs.id}:`, error);
          }
        }
      }

      // 정렬: Critical > High > Normal, 시간 내림차순
      alertItems.sort((a, b) => {
        const severityOrder = { critical: 0, high: 1, normal: 2 };
        if (severityOrder[a.severity] !== severityOrder[b.severity]) {
          return severityOrder[a.severity] - severityOrder[b.severity];
        }
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });

      setAlerts(alertItems);
      setTotalCount(alertItems.length);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  }, [confirmedAlerts]);

  // 중요도 판단 함수
  const determineSeverity = (value: string, reference: string): AlertSeverity => {
    // 간단한 판단 로직 (실제로는 각 검사 항목별 기준 필요)
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return 'high';

    // 참조 범위 파싱 시도
    const rangeMatch = reference.match(/([\d.]+)\s*[-~]\s*([\d.]+)/);
    if (rangeMatch) {
      const low = parseFloat(rangeMatch[1]);
      const high = parseFloat(rangeMatch[2]);
      const range = high - low;

      // 참조 범위의 2배 이상 벗어나면 Critical
      if (numValue < low - range || numValue > high + range) {
        return 'critical';
      }
      // 참조 범위를 벗어나면 High
      if (numValue < low || numValue > high) {
        return 'high';
      }
    }

    return 'normal';
  };

  // 초기 로드
  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // 확인 처리
  const handleConfirm = (alert: AlertItem) => {
    const newConfirmed = new Set(confirmedAlerts);
    newConfirmed.add(alert.ocsPk);
    setConfirmedAlerts(newConfirmed);
    localStorage.setItem('lis_confirmed_alerts', JSON.stringify([...newConfirmed]));

    // UI 업데이트
    setAlerts((prev) =>
      prev.map((a) =>
        a.ocsPk === alert.ocsPk ? { ...a, status: 'confirmed' } : a
      )
    );
  };

  // 상세 보기
  const handleViewDetail = (alert: AlertItem) => {
    navigate(`/ocs/lis/${alert.ocsPk}`);
  };

  // 필터링된 Alert
  const filteredAlerts = alerts.filter((alert) => {
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false;
    if (statusFilter !== 'all' && alert.status !== statusFilter) return false;
    return true;
  });

  // 페이지네이션
  const paginatedAlerts = filteredAlerts.slice(
    (page - 1) * pageSize,
    page * pageSize
  );
  const totalPages = Math.ceil(filteredAlerts.length / pageSize);

  // 통계
  const stats = {
    total: alerts.length,
    critical: alerts.filter((a) => a.severity === 'critical').length,
    high: alerts.filter((a) => a.severity === 'high').length,
    unconfirmed: alerts.filter((a) => a.status === 'unconfirmed').length,
  };

  return (
    <div className="page lis-alert-page">
      {/* Toast 알림 */}
      <OCSNotificationToast
        notifications={notifications}
        onDismiss={removeNotification}
      />

      {/* 헤더 */}
      <header className="page-header">
        <h2>검사 결과 Alert</h2>
        <span className="subtitle">이상 및 치명적 검사 결과 알림을 관리합니다</span>
      </header>

      {/* 요약 카드 */}
      <section className="summary-cards">
        <div className="summary-card total">
          <span className="card-label">전체 Alert</span>
          <span className="card-value">{stats.total}</span>
        </div>
        <div className="summary-card critical">
          <span className="card-label">Critical</span>
          <span className="card-value">{stats.critical}</span>
        </div>
        <div className="summary-card high">
          <span className="card-label">High</span>
          <span className="card-value">{stats.high}</span>
        </div>
        <div className="summary-card unconfirmed">
          <span className="card-label">미확인</span>
          <span className="card-value">{stats.unconfirmed}</span>
        </div>
      </section>

      {/* 필터 */}
      <section className="filter-section">
        <div className="filter-group">
          <label>중요도:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | 'all')}
          >
            <option value="all">전체</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="normal">Normal</option>
          </select>
        </div>
        <div className="filter-group">
          <label>상태:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as AlertStatus | 'all')}
          >
            <option value="all">전체</option>
            <option value="unconfirmed">미확인</option>
            <option value="confirmed">확인됨</option>
          </select>
        </div>
        <button className="refresh-btn" onClick={loadAlerts} disabled={loading}>
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </section>

      {/* Alert 테이블 */}
      <section className="alert-table-section">
        {loading ? (
          <div className="loading">로딩 중...</div>
        ) : paginatedAlerts.length === 0 ? (
          <div className="empty-message">이상 검사 결과가 없습니다.</div>
        ) : (
          <table className="alert-table">
            <thead>
              <tr>
                <th>발생 시간</th>
                <th>환자명</th>
                <th>환자번호</th>
                <th>검사 항목</th>
                <th>결과값</th>
                <th>참조 범위</th>
                <th>중요도</th>
                <th>상태</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {paginatedAlerts.map((alert) => (
                <tr
                  key={`${alert.ocsPk}-${alert.testCode}`}
                  className={alert.status === 'unconfirmed' ? 'unconfirmed-row' : ''}
                >
                  <td>{formatDateTime(alert.timestamp)}</td>
                  <td className="patient-name">{alert.patientName}</td>
                  <td>{alert.patientNumber}</td>
                  <td>
                    <span className="test-name">{alert.testName}</span>
                    <span className="test-code">({alert.testCode})</span>
                  </td>
                  <td className="result-value abnormal">{alert.resultValue}</td>
                  <td className="reference">{alert.referenceRange}</td>
                  <td>
                    <span className={`severity-badge ${SEVERITY_CONFIG[alert.severity].className}`}>
                      {SEVERITY_CONFIG[alert.severity].label}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${STATUS_CONFIG[alert.status].className}`}>
                      {STATUS_CONFIG[alert.status].label}
                    </span>
                  </td>
                  <td className="action-cell">
                    {alert.status === 'unconfirmed' && (
                      <button
                        className="confirm-btn"
                        onClick={() => handleConfirm(alert)}
                      >
                        확인
                      </button>
                    )}
                    <button
                      className="detail-btn"
                      onClick={() => handleViewDetail(alert)}
                    >
                      상세
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onChange={setPage}
            pageSize={pageSize}
          />
        )}
      </section>
    </div>
  );
}
