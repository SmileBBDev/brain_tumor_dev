/**
 * RIS 작업자용 영상 워크리스트 페이지 (P.74)
 * - 영상 오더 접수, 작업, 결과 제출
 * - Modality 필터, 검색 기능 추가
 * - 상세 페이지로 이동
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import './RISWorklistPage.css';

// Modality 옵션
const MODALITY_OPTIONS = ['CT', 'MRI', 'PET', 'X-RAY', 'Ultrasound', 'Mammography', 'Fluoroscopy'];

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
  const navigate = useNavigate();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<OcsStatus | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');
  const [modalityFilter, setModalityFilter] = useState('');
  const [unassignedOnly, setUnassignedOnly] = useState(false);
  const [myWorkOnly, setMyWorkOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // OCS 목록 조회
  useEffect(() => {
    const fetchOCSList = async () => {
      setLoading(true);
      try {
        const params: OCSSearchParams = {
          page,
          page_size: pageSize,
          job_role: 'RIS',
        };

        if (statusFilter) params.ocs_status = statusFilter;
        if (priorityFilter) params.priority = priorityFilter;
        if (unassignedOnly) params.unassigned = true;
        if (myWorkOnly && user) params.worker_id = user.id;
        if (searchQuery) params.q = searchQuery;

        const response = await getOCSList(params);

        let results: OCSListItem[];
        if (Array.isArray(response)) {
          results = response as unknown as OCSListItem[];
        } else {
          results = response.results;
          setTotalCount(response.count);
        }

        // Modality 필터링 (클라이언트 사이드)
        if (modalityFilter) {
          results = results.filter(ocs =>
            ocs.job_type.toUpperCase() === modalityFilter.toUpperCase()
          );
        }

        setOcsList(results);
        if (Array.isArray(response)) {
          setTotalCount(results.length);
        }
      } catch (error) {
        console.error('[RISWorklistPage] Failed to fetch OCS list:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOCSList();
  }, [page, pageSize, statusFilter, priorityFilter, modalityFilter, unassignedOnly, myWorkOnly, user, refreshKey, searchQuery]);

  const totalPages = Math.ceil(totalCount / pageSize);

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

  // 행 클릭 → 상세 페이지로 이동
  const handleRowClick = (ocs: OCSListItem) => {
    navigate(`/ocs/ris/${ocs.id}`);
  };

  // 검색
  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPage(1);
  };

  // 상태별 카운트 계산
  const statusCounts = {
    pending: ocsList.filter(o => o.ocs_status === 'ORDERED').length,
    reading: ocsList.filter(o => ['ACCEPTED', 'IN_PROGRESS'].includes(o.ocs_status)).length,
    completed: ocsList.filter(o => ['RESULT_READY', 'CONFIRMED'].includes(o.ocs_status)).length,
  };

  return (
    <div className="page ris-worklist">
      {/* 헤더 */}
      <header className="page-header">
        <h2>영상 판독 Worklist</h2>
        <span className="subtitle">담당 영상 검사 목록을 확인하고 판독을 진행합니다</span>
      </header>

      {/* 요약 카드 */}
      <section className="summary-cards">
        <div className="summary-card pending">
          <span className="count">{statusCounts.pending}</span>
          <span className="label">대기 중</span>
        </div>
        <div className="summary-card reading">
          <span className="count">{statusCounts.reading}</span>
          <span className="label">판독 중</span>
        </div>
        <div className="summary-card completed">
          <span className="count">{statusCounts.completed}</span>
          <span className="label">완료</span>
        </div>
      </section>

      {/* 필터 영역 */}
      <section className="filter-bar">
        <div className="filter-left">
          <strong className="ocs-count">
            전체 <span>{totalCount}</span>건
          </strong>
        </div>
        <div className="filter-right">
          {/* 검색 */}
          <div className="search-box">
            <input
              type="text"
              placeholder="환자명 / 환자번호 검색"
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

          {/* Modality 필터 */}
          <select
            value={modalityFilter}
            onChange={(e) => {
              setModalityFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">전체 Modality</option>
            {MODALITY_OPTIONS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          {/* 상태 필터 */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as OcsStatus | '');
              setPage(1);
            }}
          >
            <option value="">전체 상태</option>
            {Object.entries(OCS_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          {/* 우선순위 필터 */}
          <select
            value={priorityFilter}
            onChange={(e) => {
              setPriorityFilter(e.target.value as Priority | '');
              setPage(1);
            }}
          >
            <option value="">전체 우선순위</option>
            {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
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
          <div className="loading">로딩 중...</div>
        ) : (
          <table className="ocs-table worklist-table">
            <thead>
              <tr>
                <th>OCS ID</th>
                <th>상태</th>
                <th>우선순위</th>
                <th>Modality</th>
                <th>환자명</th>
                <th>환자번호</th>
                <th>처방 의사</th>
                <th>담당자</th>
                <th>생성일시</th>
                <th>액션</th>
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
                    className={`clickable-row ${ocs.priority === 'urgent' ? 'urgent-row' : ''}`}
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
                    <td><span className="modality-badge">{ocs.job_type}</span></td>
                    <td>{ocs.patient.name}</td>
                    <td>{ocs.patient.patient_number}</td>
                    <td>{ocs.doctor.name}</td>
                    <td>{ocs.worker?.name || <span className="unassigned">미배정</span>}</td>
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
                          판독 시작
                        </button>
                      )}
                      {ocs.ocs_status === 'IN_PROGRESS' && ocs.worker?.id === user?.id && (
                        <button
                          className="btn btn-sm btn-info"
                          onClick={() => handleRowClick(ocs)}
                        >
                          판독 계속
                        </button>
                      )}
                      {['RESULT_READY', 'CONFIRMED'].includes(ocs.ocs_status) && (
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleRowClick(ocs)}
                        >
                          조회
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
    </div>
  );
}
