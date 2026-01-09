/**
 * 간호사용 검사 현황 페이지 (읽기 전용)
 * - 모든 OCS 현황 조회
 * - 상태/역할/우선순위 필터링
 * - 환자명/환자번호/OCS ID 검색
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import Pagination from '@/layout/Pagination';
import { getOCSList } from '@/services/ocs.api';
import type {
  OCSListItem,
  OCSSearchParams,
  OcsStatus,
  JobRole,
  Priority,
} from '@/types/ocs';
import {
  OCS_STATUS_LABELS,
  PRIORITY_LABELS,
  JOB_ROLE_LABELS,
} from '@/types/ocs';
import OCSDetailModal from '../ocs/OCSDetailModal';
import './OrderListPage.css';

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

export default function OrderListPage() {
  const { user } = useAuth();
  const role = user?.role?.code;

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<OcsStatus | ''>('');
  const [jobRoleFilter, setJobRoleFilter] = useState<JobRole | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // Modal states
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedOcsId, setSelectedOcsId] = useState<number | null>(null);

  // OCS 목록 조회
  useEffect(() => {
    const fetchOCSList = async () => {
      setLoading(true);
      try {
        const params: OCSSearchParams = {
          page,
          page_size: pageSize,
        };

        if (statusFilter) params.ocs_status = statusFilter;
        if (jobRoleFilter) params.job_role = jobRoleFilter;
        if (priorityFilter) params.priority = priorityFilter;
        if (searchQuery) params.q = searchQuery;

        const response = await getOCSList(params);
        // 페이지네이션 응답과 배열 응답 모두 처리
        if (Array.isArray(response)) {
          setOcsList(response as unknown as OCSListItem[]);
          setTotalCount(response.length);
        } else {
          setOcsList(response.results);
          setTotalCount(response.count);
        }
      } catch (error) {
        console.error('Failed to fetch OCS list:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOCSList();
  }, [page, pageSize, statusFilter, jobRoleFilter, priorityFilter, searchQuery]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleRowClick = (ocs: OCSListItem) => {
    setSelectedOcsId(ocs.id);
    setIsDetailModalOpen(true);
  };

  const handleModalClose = () => {
    setIsDetailModalOpen(false);
    setSelectedOcsId(null);
  };

  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPage(1);
  };

  if (!role) return <div>접근 권한 정보 없음</div>;

  return (
    <div className="page order-list-page">
      {/* 헤더 */}
      <header className="page-header">
        <h2>검사 현황</h2>
        <span className="subtitle">전체 OCS 오더 현황을 확인합니다</span>
      </header>

      {/* 필터 영역 */}
      <section className="filter-bar">
        <div className="filter-left">
          <strong className="ocs-count">
            총 <span>{totalCount}</span>건
          </strong>
        </div>
        <div className="filter-right">
          {/* 검색 */}
          <div className="search-box">
            <input
              type="text"
              placeholder="환자명 / 환자번호 / OCS ID 검색"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch();
              }}
            />
            <button className="btn btn-search" onClick={handleSearch}>
              검색
            </button>
            {searchQuery && (
              <button className="btn btn-clear" onClick={handleClearSearch}>
                초기화
              </button>
            )}
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as OcsStatus | '');
              setPage(1);
            }}
          >
            <option value="">전체 상태</option>
            {Object.entries(OCS_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={jobRoleFilter}
            onChange={(e) => {
              setJobRoleFilter(e.target.value as JobRole | '');
              setPage(1);
            }}
          >
            <option value="">전체 역할</option>
            {Object.entries(JOB_ROLE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => {
              setPriorityFilter(e.target.value as Priority | '');
              setPage(1);
            }}
          >
            <option value="">전체 우선순위</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* 테이블 */}
      <section className="content">
        {loading ? (
          <div className="loading">로딩 중...</div>
        ) : (
          <table className="ocs-table">
            <thead>
              <tr>
                <th>OCS ID</th>
                <th>상태</th>
                <th>우선순위</th>
                <th>환자</th>
                <th>환자번호</th>
                <th>역할</th>
                <th>작업유형</th>
                <th>처방의</th>
                <th>작업자</th>
                <th>생성일시</th>
              </tr>
            </thead>
            <tbody>
              {!ocsList || ocsList.length === 0 ? (
                <tr>
                  <td colSpan={10} align="center">
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
                    <td>{ocs.patient.patient_number}</td>
                    <td>{JOB_ROLE_LABELS[ocs.job_role] || ocs.job_role}</td>
                    <td>{ocs.job_type}</td>
                    <td>{ocs.doctor.name}</td>
                    <td>{ocs.worker?.name || '-'}</td>
                    <td>{formatDate(ocs.created_at)}</td>
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

      {/* OCS 상세 모달 (읽기 전용) */}
      {selectedOcsId && (
        <OCSDetailModal
          isOpen={isDetailModalOpen}
          ocsId={selectedOcsId}
          onClose={handleModalClose}
          onSuccess={() => {}} // 읽기 전용이므로 빈 함수
        />
      )}
    </div>
  );
}
