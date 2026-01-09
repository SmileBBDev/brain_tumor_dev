/**
 * RIS 작업자용 영상 워크리스트 페이지
 * - 영상 오더 접수, 작업, 결과 제출
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import Pagination from '@/layout/Pagination';
import { getOCSList, acceptOCS, startOCS } from '@/services/ocs.api';
import type {
  OCSListItem,
  OCSSearchParams,
  OcsStatus,
  Priority,
} from '@/types/ocs';
import { OCS_STATUS_LABELS, PRIORITY_LABELS } from '@/types/ocs';
import OCSDetailModal from './OCSDetailModal';

// 날짜 포맷
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 상태별 스타일 클래스
const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    ORDERED: 'status-ordered',
    ACCEPTED: 'status-accepted',
    IN_PROGRESS: 'status-in-progress',
    RESULT_READY: 'status-result-ready',
    CONFIRMED: 'status-confirmed',
    CANCELLED: 'status-cancelled',
  };
  return classes[status] || '';
};

// 우선순위별 스타일 클래스
const getPriorityClass = (priority: string): string => {
  const classes: Record<string, string> = {
    urgent: 'priority-urgent',
    normal: 'priority-normal',
    scheduled: 'priority-scheduled',
  };
  return classes[priority] || '';
};

export default function RISWorklistPage() {
  const { user } = useAuth();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<OcsStatus | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');
  const [unassignedOnly, setUnassignedOnly] = useState(false);
  const [myWorkOnly, setMyWorkOnly] = useState(false);

  // Modal states
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedOcsId, setSelectedOcsId] = useState<number | null>(null);

  // OCS 목록 조회
  useEffect(() => {
    console.log('[RISWorklistPage] useEffect triggered, fetching OCS list...');
    const fetchOCSList = async () => {
      setLoading(true);
      try {
        const params: OCSSearchParams = {
          page,
          page_size: pageSize,
          job_role: 'RIS', // RIS 오더만
        };

        if (statusFilter) params.ocs_status = statusFilter;
        if (priorityFilter) params.priority = priorityFilter;
        if (unassignedOnly) params.unassigned = true;
        if (myWorkOnly && user) params.worker_id = user.id;

        console.log('[RISWorklistPage] Fetching with params:', params);
        const response = await getOCSList(params);
        console.log('[RISWorklistPage] Response:', response);
        // 페이지네이션 응답과 배열 응답 모두 처리
        if (Array.isArray(response)) {
          // 배열 응답 (페이지네이션 없음)
          setOcsList(response as unknown as OCSListItem[]);
          setTotalCount(response.length);
        } else {
          // 페이지네이션 응답
          setOcsList(response.results);
          setTotalCount(response.count);
        }
      } catch (error) {
        console.error('[RISWorklistPage] Failed to fetch OCS list:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOCSList();
  }, [page, pageSize, statusFilter, priorityFilter, unassignedOnly, myWorkOnly, user, refreshKey]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value as OcsStatus | '');
    setPage(1);
  };

  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPriorityFilter(e.target.value as Priority | '');
    setPage(1);
  };

  // 오더 접수
  const handleAccept = async (ocsId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await acceptOCS(ocsId);
      alert('오더를 접수했습니다.');
      setRefreshKey((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to accept OCS:', error);
      alert('접수에 실패했습니다.');
    }
  };

  // 작업 시작
  const handleStart = async (ocsId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await startOCS(ocsId);
      alert('작업을 시작합니다.');
      setRefreshKey((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to start OCS:', error);
      alert('작업 시작에 실패했습니다.');
    }
  };

  const handleRowClick = (ocs: OCSListItem) => {
    setSelectedOcsId(ocs.id);
    setIsDetailModalOpen(true);
  };

  const handleModalClose = () => {
    setIsDetailModalOpen(false);
    setSelectedOcsId(null);
  };

  const handleModalSuccess = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="page ris-worklist">
      {/* 필터 영역 */}
      <section className="filter-bar">
        <div className="filter-left">
          <strong className="ocs-count">
            영상 오더 <span>{totalCount}</span>건
          </strong>
        </div>
        <div className="filter-right">
          <select value={statusFilter} onChange={handleStatusChange}>
            <option value="">전체 상태</option>
            {Object.entries(OCS_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select value={priorityFilter} onChange={handlePriorityChange}>
            <option value="">전체 우선순위</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={unassignedOnly}
              onChange={(e) => {
                setUnassignedOnly(e.target.checked);
                if (e.target.checked) setMyWorkOnly(false);
                setPage(1);
              }}
            />
            미배정만
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={myWorkOnly}
              onChange={(e) => {
                setMyWorkOnly(e.target.checked);
                if (e.target.checked) setUnassignedOnly(false);
                setPage(1);
              }}
            />
            내 작업만
          </label>
        </div>
      </section>

      {/* 워크리스트 테이블 */}
      <section className="content">
        {loading ? (
          <div>로딩 중...</div>
        ) : (
          <table className="ocs-table worklist-table">
            <thead>
              <tr>
                <th>OCS ID</th>
                <th>상태</th>
                <th>우선순위</th>
                <th>환자</th>
                <th>작업 유형</th>
                <th>처방 의사</th>
                <th>생성일시</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {!ocsList || ocsList.length === 0 ? (
                <tr>
                  <td colSpan={8} align="center">
                    데이터 없음
                  </td>
                </tr>
              ) : (
                ocsList.map((ocs) => (
                  <tr
                    key={ocs.id}
                    onClick={() => handleRowClick(ocs)}
                    className="clickable-row"
                  >
                    <td>{ocs.ocs_id}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(ocs.ocs_status)}`}>
                        {ocs.ocs_status_display}
                      </span>
                    </td>
                    <td>
                      <span className={`priority-badge ${getPriorityClass(ocs.priority)}`}>
                        {ocs.priority_display}
                      </span>
                    </td>
                    <td>{ocs.patient.name}</td>
                    <td>{ocs.job_type}</td>
                    <td>{ocs.doctor.name}</td>
                    <td>{formatDate(ocs.created_at)}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {ocs.ocs_status === 'ORDERED' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={(e) => handleAccept(ocs.id, e)}
                        >
                          접수
                        </button>
                      )}
                      {ocs.ocs_status === 'ACCEPTED' && ocs.worker?.id === user?.id && (
                        <button
                          className="btn btn-sm btn-success"
                          onClick={(e) => handleStart(ocs.id, e)}
                        >
                          시작
                        </button>
                      )}
                      {ocs.ocs_status === 'IN_PROGRESS' && ocs.worker?.id === user?.id && (
                        <button
                          className="btn btn-sm btn-info"
                          onClick={() => handleRowClick(ocs)}
                        >
                          결과 입력
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      {/* 페이징 */}
      <section className="pagination-bar">
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onChange={setPage}
          pageSize={pageSize}
        />
      </section>

      {/* OCS 상세 모달 */}
      {selectedOcsId && (
        <OCSDetailModal
          isOpen={isDetailModalOpen}
          ocsId={selectedOcsId}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}
