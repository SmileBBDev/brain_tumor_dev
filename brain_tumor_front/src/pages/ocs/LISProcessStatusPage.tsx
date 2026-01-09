/**
 * LIS 검사 결과 처리 상태 화면 (P.86)
 * - 업로드된 Raw 데이터의 파싱/정규화/저장 상태 모니터링
 * - 오류 발생 시 재처리 기능
 */
import { useState, useEffect, useCallback } from 'react';
import Pagination from '@/layout/Pagination';
import './LISProcessStatusPage.css';

// 처리 상태 타입
type ProcessStatus = 'pending' | 'parsing' | 'normalizing' | 'saving' | 'completed' | 'error';

// 처리 아이템 인터페이스
interface ProcessItem {
  id: string;
  rawId: string;
  fileName: string;
  receivedAt: string;
  parseStatus: ProcessStatus;
  normalizeStatus: ProcessStatus;
  saveStatus: ProcessStatus;
  errorMessage: string | null;
  recordCount: number | null;
  processedAt: string | null;
}

// 상태 설정
const STATUS_CONFIG: Record<ProcessStatus, { label: string; className: string }> = {
  pending: { label: '대기', className: 'status-pending' },
  parsing: { label: '파싱 중', className: 'status-processing' },
  normalizing: { label: '정규화 중', className: 'status-processing' },
  saving: { label: '저장 중', className: 'status-processing' },
  completed: { label: '완료', className: 'status-completed' },
  error: { label: '오류', className: 'status-error' },
};

// 날짜 포맷
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// 더미 데이터 생성
const generateMockData = (): ProcessItem[] => {
  const statuses: ProcessStatus[] = ['pending', 'parsing', 'normalizing', 'saving', 'completed', 'error'];
  const items: ProcessItem[] = [];

  for (let i = 1; i <= 25; i++) {
    const isError = i % 7 === 0;
    const isCompleted = i % 3 === 0 && !isError;
    const isPending = i % 5 === 0 && !isError && !isCompleted;

    let parseStatus: ProcessStatus = 'completed';
    let normalizeStatus: ProcessStatus = 'completed';
    let saveStatus: ProcessStatus = 'completed';
    let errorMessage: string | null = null;

    if (isPending) {
      parseStatus = 'pending';
      normalizeStatus = 'pending';
      saveStatus = 'pending';
    } else if (isError) {
      const errorStep = Math.floor(Math.random() * 3);
      if (errorStep === 0) {
        parseStatus = 'error';
        normalizeStatus = 'pending';
        saveStatus = 'pending';
        errorMessage = '파일 형식이 올바르지 않습니다. (line 15)';
      } else if (errorStep === 1) {
        parseStatus = 'completed';
        normalizeStatus = 'error';
        saveStatus = 'pending';
        errorMessage = '필수 필드 누락: patient_id';
      } else {
        parseStatus = 'completed';
        normalizeStatus = 'completed';
        saveStatus = 'error';
        errorMessage = '데이터베이스 연결 오류';
      }
    }

    items.push({
      id: `proc-${i}`,
      rawId: `RAW-${String(i).padStart(6, '0')}`,
      fileName: `lab_result_${String(i).padStart(3, '0')}.csv`,
      receivedAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      parseStatus,
      normalizeStatus,
      saveStatus,
      errorMessage,
      recordCount: isCompleted ? Math.floor(Math.random() * 50) + 10 : null,
      processedAt: isCompleted ? new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString() : null,
    });
  }

  return items.sort((a, b) => new Date(b.receivedAt).getTime() - new Date(a.receivedAt).getTime());
};

export default function LISProcessStatusPage() {
  // 상태
  const [items, setItems] = useState<ProcessItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // 필터
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'processing' | 'completed' | 'error'>('all');

  // 재처리 중인 항목
  const [reprocessingIds, setReprocessingIds] = useState<Set<string>>(new Set());

  // 데이터 로드 (실제 구현 시 API 호출)
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 300));
      const data = generateMockData();
      setItems(data);
    } catch (error) {
      console.error('Failed to load process status:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 재처리 핸들러
  const handleReprocess = async (item: ProcessItem) => {
    setReprocessingIds((prev) => new Set(prev).add(item.id));

    try {
      // 시뮬레이션: 2초 후 성공
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // 상태 업데이트
      setItems((prev) =>
        prev.map((i) =>
          i.id === item.id
            ? {
                ...i,
                parseStatus: 'completed',
                normalizeStatus: 'completed',
                saveStatus: 'completed',
                errorMessage: null,
                recordCount: Math.floor(Math.random() * 50) + 10,
                processedAt: new Date().toISOString(),
              }
            : i
        )
      );
    } catch (error) {
      console.error('Reprocess failed:', error);
    } finally {
      setReprocessingIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(item.id);
        return newSet;
      });
    }
  };

  // 전체 상태 계산
  const getOverallStatus = (item: ProcessItem): ProcessStatus => {
    if (item.parseStatus === 'error' || item.normalizeStatus === 'error' || item.saveStatus === 'error') {
      return 'error';
    }
    if (item.parseStatus === 'pending' && item.normalizeStatus === 'pending' && item.saveStatus === 'pending') {
      return 'pending';
    }
    if (item.parseStatus === 'completed' && item.normalizeStatus === 'completed' && item.saveStatus === 'completed') {
      return 'completed';
    }
    return 'parsing'; // processing
  };

  // 필터링
  const filteredItems = items.filter((item) => {
    if (statusFilter === 'all') return true;
    const overall = getOverallStatus(item);
    if (statusFilter === 'pending') return overall === 'pending';
    if (statusFilter === 'processing') return ['parsing', 'normalizing', 'saving'].includes(overall);
    if (statusFilter === 'completed') return overall === 'completed';
    if (statusFilter === 'error') return overall === 'error';
    return true;
  });

  // 페이지네이션
  const paginatedItems = filteredItems.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.ceil(filteredItems.length / pageSize);

  // 통계
  const stats = {
    total: items.length,
    pending: items.filter((i) => getOverallStatus(i) === 'pending').length,
    processing: items.filter((i) => ['parsing', 'normalizing', 'saving'].includes(getOverallStatus(i))).length,
    completed: items.filter((i) => getOverallStatus(i) === 'completed').length,
    error: items.filter((i) => getOverallStatus(i) === 'error').length,
  };

  return (
    <div className="page lis-process-status-page">
      {/* 헤더 */}
      <header className="page-header">
        <h2>검사 결과 처리 상태</h2>
        <span className="subtitle">업로드된 Raw 데이터의 처리 현황을 모니터링합니다</span>
        <button className="refresh-btn" onClick={loadData} disabled={loading}>
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </header>

      {/* 요약 카드 */}
      <section className="summary-cards">
        <div className="summary-card total">
          <span className="card-label">전체</span>
          <span className="card-value">{stats.total}</span>
        </div>
        <div className="summary-card pending">
          <span className="card-label">대기</span>
          <span className="card-value">{stats.pending}</span>
        </div>
        <div className="summary-card processing">
          <span className="card-label">처리 중</span>
          <span className="card-value">{stats.processing}</span>
        </div>
        <div className="summary-card completed">
          <span className="card-label">완료</span>
          <span className="card-value">{stats.completed}</span>
        </div>
        <div className="summary-card error">
          <span className="card-label">오류</span>
          <span className="card-value">{stats.error}</span>
        </div>
      </section>

      {/* 필터 */}
      <section className="filter-section">
        <div className="filter-group">
          <label>상태 필터:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
          >
            <option value="all">전체</option>
            <option value="pending">대기</option>
            <option value="processing">처리 중</option>
            <option value="completed">완료</option>
            <option value="error">오류</option>
          </select>
        </div>
      </section>

      {/* 테이블 */}
      <section className="table-section">
        {loading ? (
          <div className="loading">로딩 중...</div>
        ) : paginatedItems.length === 0 ? (
          <div className="empty-message">처리 기록이 없습니다.</div>
        ) : (
          <table className="process-table">
            <thead>
              <tr>
                <th>Raw ID</th>
                <th>파일명</th>
                <th>수신 시간</th>
                <th>파싱</th>
                <th>정규화</th>
                <th>저장</th>
                <th>레코드 수</th>
                <th>오류 메시지</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {paginatedItems.map((item) => {
                const hasError = getOverallStatus(item) === 'error';
                const isReprocessing = reprocessingIds.has(item.id);

                return (
                  <tr key={item.id} className={hasError ? 'error-row' : ''}>
                    <td className="raw-id">{item.rawId}</td>
                    <td className="filename">{item.fileName}</td>
                    <td className="datetime">{formatDateTime(item.receivedAt)}</td>
                    <td>
                      <span className={`status-badge ${STATUS_CONFIG[item.parseStatus].className}`}>
                        {STATUS_CONFIG[item.parseStatus].label}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${STATUS_CONFIG[item.normalizeStatus].className}`}>
                        {STATUS_CONFIG[item.normalizeStatus].label}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${STATUS_CONFIG[item.saveStatus].className}`}>
                        {STATUS_CONFIG[item.saveStatus].label}
                      </span>
                    </td>
                    <td className="record-count">{item.recordCount ?? '-'}</td>
                    <td className="error-message">
                      {item.errorMessage && (
                        <span className="error-text" title={item.errorMessage}>
                          {item.errorMessage}
                        </span>
                      )}
                    </td>
                    <td className="action-cell">
                      {hasError && (
                        <button
                          className="reprocess-btn"
                          onClick={() => handleReprocess(item)}
                          disabled={isReprocessing}
                        >
                          {isReprocessing ? '처리 중...' : '재처리'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
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
