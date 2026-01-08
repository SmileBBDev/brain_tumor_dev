/**
 * 의사용 검사 오더 관리 페이지
 * - 오더 생성, 조회, 확정, 취소
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import Pagination from '@/layout/Pagination';
import { getOCSList, createOCS } from '@/services/ocs.api';
import type {
  OCSListItem,
  OCSSearchParams,
  OcsStatus,
  JobRole,
  Priority,
  OCSCreateRequest,
} from '@/types/ocs';
import {
  OCS_STATUS_LABELS,
  PRIORITY_LABELS,
  JOB_ROLE_LABELS,
} from '@/types/ocs';
import OCSListTable from './OCSListTable';
import OCSDetailModal from './OCSDetailModal';

export default function DoctorOrderPage() {
  const { role, user } = useAuth();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Filter states
  const [statusFilter, setStatusFilter] = useState<OcsStatus | ''>('');
  const [jobRoleFilter, setJobRoleFilter] = useState<JobRole | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');

  // Modal states
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedOcsId, setSelectedOcsId] = useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Create form states
  const [createForm, setCreateForm] = useState<Partial<OCSCreateRequest>>({
    job_role: 'RIS',
    job_type: '',
    priority: 'normal',
    patient_id: 0,
  });

  if (!role || !['DOCTOR', 'SYSTEMMANAGER', 'ADMIN'].includes(role)) {
    return <div className="page">접근 권한이 없습니다.</div>;
  }

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

      // 의사인 경우 자신의 오더만
      if (role === 'DOCTOR') {
        params.doctor_id = user?.id;
      }

      const response = await getOCSList(params);
      setOcsList(response.results);
      setTotalCount(response.count);
    } catch (error) {
      console.error('Failed to fetch OCS list:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOCSList();
  }, [page, statusFilter, jobRoleFilter, priorityFilter]);

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
    fetchOCSList();
  };

  // 오더 생성
  const handleCreateOrder = async () => {
    if (!createForm.patient_id || !createForm.job_type) {
      alert('환자와 작업 유형을 선택해주세요.');
      return;
    }

    try {
      await createOCS(createForm as OCSCreateRequest);
      alert('오더가 생성되었습니다.');
      setIsCreateModalOpen(false);
      setCreateForm({
        job_role: 'RIS',
        job_type: '',
        priority: 'normal',
        patient_id: 0,
      });
      fetchOCSList();
    } catch (error) {
      console.error('Failed to create OCS:', error);
      alert('오더 생성에 실패했습니다.');
    }
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
            onClick={() => setIsCreateModalOpen(true)}
          >
            + 새 오더 생성
          </button>
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

      {/* 오더 생성 모달 (간단 버전) */}
      {isCreateModalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>새 오더 생성</h3>
              <button onClick={() => setIsCreateModalOpen(false)}>&times;</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>환자 ID</label>
                <input
                  type="number"
                  value={createForm.patient_id || ''}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, patient_id: Number(e.target.value) })
                  }
                  placeholder="환자 ID 입력"
                />
              </div>
              <div className="form-group">
                <label>작업 역할</label>
                <select
                  value={createForm.job_role}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, job_role: e.target.value as JobRole })
                  }
                >
                  {Object.entries(JOB_ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>작업 유형</label>
                <input
                  type="text"
                  value={createForm.job_type || ''}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, job_type: e.target.value })
                  }
                  placeholder="예: MRI, CT, BLOOD"
                />
              </div>
              <div className="form-group">
                <label>우선순위</label>
                <select
                  value={createForm.priority}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, priority: e.target.value as Priority })
                  }
                >
                  {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setIsCreateModalOpen(false)}>
                취소
              </button>
              <button className="btn btn-primary" onClick={handleCreateOrder}>
                생성
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
