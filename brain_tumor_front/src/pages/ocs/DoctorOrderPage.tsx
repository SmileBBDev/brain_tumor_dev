/**
 * 의사용 검사 오더 관리 페이지
 * - 오더 조회, 확정, 취소
 * - 오더 생성은 /orders/create 페이지로 이동
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import OCSListTable from './OCSListTable';
import OCSDetailModal from './OCSDetailModal';

export default function DoctorOrderPage() {
  const navigate = useNavigate();
  const { role, user } = useAuth();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

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

        // 의사인 경우 자신의 오더만
        if (role === 'DOCTOR' && user?.id) {
          params.doctor_id = user.id;
        }

        const response = await getOCSList(params);
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
  }, [page, pageSize, statusFilter, jobRoleFilter, priorityFilter, searchQuery, role, user?.id, refreshKey]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value as OcsStatus | '');
    setPage(1);
  };

  const handleJobRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setJobRoleFilter(e.target.value as JobRole | '');
    setPage(1);
  };

  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPriorityFilter(e.target.value as Priority | '');
    setPage(1);
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

  // 오더 생성 페이지로 이동
  const handleCreateOrder = () => {
    navigate('/orders/create');
  };

  return (
    <div className="page doctor-order">
      {/* 필터 영역 */}
      <section className="filter-bar">
        <div className="filter-left">
          <strong className="ocs-count">
            총 <span>{totalCount}</span>건의 오더
          </strong>
          <button
            className="btn btn-primary"
            onClick={handleCreateOrder}
          >
            + 오더 생성
          </button>
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
                if (e.key === 'Enter') {
                  setSearchQuery(searchInput);
                  setPage(1);
                }
              }}
            />
            <button
              className="btn btn-search"
              onClick={() => {
                setSearchQuery(searchInput);
                setPage(1);
              }}
            >
              검색
            </button>
            {searchQuery && (
              <button
                className="btn btn-clear"
                onClick={() => {
                  setSearchInput('');
                  setSearchQuery('');
                  setPage(1);
                }}
              >
                초기화
              </button>
            )}
          </div>

          <select value={statusFilter} onChange={handleStatusChange}>
            <option value="">전체 상태</option>
            {Object.entries(OCS_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select value={jobRoleFilter} onChange={handleJobRoleChange}>
            <option value="">전체 역할</option>
            {Object.entries(JOB_ROLE_LABELS).map(([value, label]) => (
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
        </div>
      </section>

      {/* OCS 리스트 */}
      <section className="content">
        {loading ? (
          <div>로딩 중...</div>
        ) : (
          <OCSListTable
            role={role}
            ocsList={ocsList}
            onRowClick={handleRowClick}
          />
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

      <style>{`
        .search-box {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .search-box input {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          width: 220px;
        }

        .search-box input:focus {
          outline: none;
          border-color: #1976d2;
        }

        .btn-search {
          padding: 8px 16px;
          background-color: #1976d2;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-search:hover {
          background-color: #1565c0;
        }

        .btn-clear {
          padding: 8px 12px;
          background-color: #f5f5f5;
          color: #666;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-clear:hover {
          background-color: #e0e0e0;
        }
      `}</style>
    </div>
  );
}
