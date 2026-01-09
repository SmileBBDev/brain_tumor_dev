/**
 * AI 추론 요청 목록 페이지
 * - 전체 AI 추론 요청 조회
 * - 상태별 필터링
 * - 요청 생성 링크
 */
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { useAIRequestList, useAIModels } from '@/hooks';
import { LoadingSpinner, EmptyState, useToast } from '@/components/common';
import Pagination from '@/layout/Pagination';
import type { AIInferenceRequest } from '@/services/ai.api';
import './AIRequestListPage.css';

// 상태 라벨
const STATUS_LABELS: Record<string, string> = {
  PENDING: '대기 중',
  VALIDATING: '검증 중',
  PROCESSING: '처리 중',
  COMPLETED: '완료',
  FAILED: '실패',
  CANCELLED: '취소됨',
};

// 상태 색상
const STATUS_COLORS: Record<string, string> = {
  PENDING: 'status-pending',
  VALIDATING: 'status-validating',
  PROCESSING: 'status-processing',
  COMPLETED: 'status-completed',
  FAILED: 'status-failed',
  CANCELLED: 'status-cancelled',
};

// 우선순위 라벨
const PRIORITY_LABELS: Record<string, string> = {
  low: '낮음',
  normal: '보통',
  high: '높음',
  urgent: '긴급',
};

export default function AIRequestListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  // 필터 상태
  const [statusFilter, setStatusFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [myOnly, setMyOnly] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 데이터 조회
  const { requests, loading, error, refresh } = useAIRequestList({
    status: statusFilter || undefined,
    modelCode: modelFilter || undefined,
    myOnly,
    pollingInterval: 5000, // 5초마다 상태 업데이트
  });

  const { models } = useAIModels();

  // 페이지네이션 적용
  const totalPages = Math.ceil(requests.length / pageSize);
  const paginatedRequests = requests.slice((page - 1) * pageSize, page * pageSize);

  // 요청 상세 페이지로 이동
  const handleRowClick = useCallback(
    (request: AIInferenceRequest) => {
      navigate(`/ai/requests/${request.id}`);
    },
    [navigate]
  );

  // 새 요청 생성 페이지로 이동
  const handleCreateRequest = useCallback(() => {
    navigate('/ai/requests/create');
  }, [navigate]);

  // 시간 포맷
  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 처리 시간 포맷
  const formatProcessingTime = (seconds: number | null) => {
    if (seconds === null) return '-';
    if (seconds < 60) return `${seconds}초`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}분 ${secs}초`;
  };

  return (
    <div className="page ai-request-list">
      {/* 헤더 */}
      <header className="page-header">
        <h2>AI 분석 요청 관리</h2>
        <span className="subtitle">AI 추론 요청을 조회하고 관리합니다</span>
      </header>

      {/* 필터 영역 */}
      <section className="filter-bar">
        <div className="filter-left">
          <strong className="request-count">
            총 <span>{requests.length}</span>건의 요청
          </strong>
          <button className="btn btn-primary" onClick={handleCreateRequest}>
            + 새 분석 요청
          </button>
        </div>
        <div className="filter-right">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={myOnly}
              onChange={(e) => setMyOnly(e.target.checked)}
            />
            내 요청만
          </label>

          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">전체 상태</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select value={modelFilter} onChange={(e) => setModelFilter(e.target.value)}>
            <option value="">전체 모델</option>
            {models.map((model) => (
              <option key={model.code} value={model.code}>
                {model.name}
              </option>
            ))}
          </select>

          <button className="btn btn-secondary" onClick={refresh}>
            새로고침
          </button>
        </div>
      </section>

      {/* 요청 목록 */}
      <section className="content">
        {loading ? (
          <LoadingSpinner text="AI 분석 요청 목록을 불러오는 중..." />
        ) : error ? (
          <div className="error-state">
            <p>{error}</p>
            <button className="btn btn-primary" onClick={refresh}>
              다시 시도
            </button>
          </div>
        ) : paginatedRequests.length === 0 ? (
          <EmptyState
            icon="AI"
            title="AI 분석 요청이 없습니다"
            description="새 AI 분석 요청을 생성하거나 필터 조건을 변경해주세요."
            action={{ label: '새 분석 요청', onClick: handleCreateRequest }}
          />
        ) : (
          <table className="ai-request-table">
            <thead>
              <tr>
                <th>요청 ID</th>
                <th>환자</th>
                <th>모델</th>
                <th>상태</th>
                <th>우선순위</th>
                <th>요청자</th>
                <th>요청일시</th>
                <th>처리시간</th>
                <th>결과</th>
              </tr>
            </thead>
            <tbody>
              {paginatedRequests.map((request) => (
                <tr
                  key={request.id}
                  onClick={() => handleRowClick(request)}
                  className="clickable"
                >
                  <td className="request-id">{request.request_id}</td>
                  <td>
                    <div className="patient-info">
                      <span className="patient-name">{request.patient_name}</span>
                      <span className="patient-number">{request.patient_number}</span>
                    </div>
                  </td>
                  <td>{request.model_name}</td>
                  <td>
                    <span className={`status-badge ${STATUS_COLORS[request.status]}`}>
                      {STATUS_LABELS[request.status] || request.status}
                    </span>
                  </td>
                  <td>
                    <span className={`priority-badge priority-${request.priority}`}>
                      {PRIORITY_LABELS[request.priority] || request.priority}
                    </span>
                  </td>
                  <td>{request.requested_by_name}</td>
                  <td>{formatDateTime(request.requested_at)}</td>
                  <td>{formatProcessingTime(request.processing_time)}</td>
                  <td>
                    {request.has_result ? (
                      <span className="result-available">결과 있음</span>
                    ) : request.status === 'FAILED' ? (
                      <span className="result-failed">실패</span>
                    ) : (
                      <span className="result-pending">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <section className="pagination-bar">
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onChange={setPage}
            pageSize={pageSize}
          />
        </section>
      )}

      {/* Toast 컨테이너 */}
      <toast.ToastContainer position="top-right" />
    </div>
  );
}
