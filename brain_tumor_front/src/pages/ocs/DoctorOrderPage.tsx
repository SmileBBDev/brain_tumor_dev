/**
 * 의사용 검사 오더 관리 페이지
 * - 오더 생성, 조회, 확정, 취소
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../auth/AuthProvider';
import Pagination from '@/layout/Pagination';
import { getOCSList, createOCS } from '@/services/ocs.api';
import { getPatients } from '@/services/patient.api';
import type {
  OCSListItem,
  OCSSearchParams,
  OcsStatus,
  JobRole,
  Priority,
  OCSCreateData,
} from '@/types/ocs';
import type { Patient } from '@/types/patient';
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
  const [refreshKey, setRefreshKey] = useState(0); // 리스트 새로고침 트리거

  // Filter states
  const [statusFilter, setStatusFilter] = useState<OcsStatus | ''>('');
  const [jobRoleFilter, setJobRoleFilter] = useState<JobRole | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // Modal states
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedOcsId, setSelectedOcsId] = useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Create form states
  const [createForm, setCreateForm] = useState<Partial<OCSCreateData>>({
    job_role: 'RIS',
    job_type: '',
    priority: 'normal',
    patient_id: 0,
  });

  // Patient search states
  const [patientSearchQuery, setPatientSearchQuery] = useState('');
  const [patientSearchResults, setPatientSearchResults] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);

  // Job type search states
  const [jobTypeSearch, setJobTypeSearch] = useState('');

  // Job type options by role
  const JOB_TYPE_OPTIONS: Record<JobRole, string[]> = {
    RIS: ['CT', 'MRI', 'PET', 'X-RAY', 'Ultrasound', 'Mammography', 'Fluoroscopy'],
    LIS: ['CBC', 'BMP', 'CMP', 'Lipid Panel', 'LFT', 'RFT', 'Thyroid Panel', 'Coagulation', 'Urinalysis', 'Tumor Markers'],
    TREATMENT: ['Chemotherapy', 'Radiation', 'Surgery', 'Biopsy', 'Injection'],
    CONSULT: ['Neurology', 'Oncology', 'Radiology', 'Pathology'],
  };

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
  }, [page, pageSize, statusFilter, jobRoleFilter, priorityFilter, searchQuery, role, user?.id, refreshKey]);

  // 환자 검색
  const searchPatients = useCallback(async (query: string) => {
    if (!query || query.length < 1) {
      setPatientSearchResults([]);
      setShowPatientDropdown(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await getPatients({ q: query, page_size: 10 });
      setPatientSearchResults(response.results);
      setShowPatientDropdown(true);
    } catch (error) {
      console.error('Failed to search patients:', error);
      setPatientSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // 검색어 변경 시 디바운스 적용
  useEffect(() => {
    const timer = setTimeout(() => {
      searchPatients(patientSearchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [patientSearchQuery, searchPatients]);

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
    setRefreshKey((prev) => prev + 1); // 리스트 새로고침 트리거
  };

  // 환자 선택
  const handlePatientSelect = (patient: Patient) => {
    setSelectedPatient(patient);
    setCreateForm({ ...createForm, patient_id: patient.id });
    setPatientSearchQuery(`${patient.name} (${patient.patient_number})`);
    setShowPatientDropdown(false);
  };

  // 환자 선택 해제
  const handlePatientClear = () => {
    setSelectedPatient(null);
    setCreateForm({ ...createForm, patient_id: 0 });
    setPatientSearchQuery('');
    setPatientSearchResults([]);
  };

  // 오더 생성 모달 열기
  const handleOpenCreateModal = () => {
    setCreateForm({
      job_role: 'RIS',
      job_type: '',
      priority: 'normal',
      patient_id: 0,
    });
    setSelectedPatient(null);
    setPatientSearchQuery('');
    setPatientSearchResults([]);
    setIsCreateModalOpen(true);
  };

  // 오더 생성
  const handleCreateOrder = async () => {
    if (!createForm.patient_id || !createForm.job_type) {
      alert('환자와 작업 유형을 선택해주세요.');
      return;
    }

    try {
      await createOCS(createForm as OCSCreateData);
      alert('오더가 생성되었습니다.');
      setIsCreateModalOpen(false);
      setCreateForm({
        job_role: 'RIS',
        job_type: '',
        priority: 'normal',
        patient_id: 0,
      });
      setSelectedPatient(null);
      setPatientSearchQuery('');
      setRefreshKey((prev) => prev + 1); // 리스트 새로고침 트리거
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
            onClick={handleOpenCreateModal}
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

      {/* 오더 생성 모달 */}
      {isCreateModalOpen && (
        <div className="modal-overlay" onClick={() => setIsCreateModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>오더 생성</h3>
              <button className="close-btn" onClick={() => setIsCreateModalOpen(false)}>&times;</button>
            </div>
            <div className="modal-body">
              {/* 환자 검색 */}
              <div className="form-group">
                <label>환자 선택 *</label>
                <div className="patient-search-container">
                  <div className="search-input-wrapper">
                    <input
                      type="text"
                      value={patientSearchQuery}
                      onChange={(e) => {
                        setPatientSearchQuery(e.target.value);
                        if (selectedPatient) {
                          setSelectedPatient(null);
                          setCreateForm({ ...createForm, patient_id: 0 });
                        }
                      }}
                      onFocus={() => {
                        if (patientSearchResults.length > 0) {
                          setShowPatientDropdown(true);
                        }
                      }}
                      placeholder="환자명 또는 환자번호로 검색"
                      className={selectedPatient ? 'selected' : ''}
                    />
                    {selectedPatient && (
                      <button
                        type="button"
                        className="clear-btn"
                        onClick={handlePatientClear}
                      >
                        &times;
                      </button>
                    )}
                    {isSearching && <span className="searching-indicator">검색 중...</span>}
                  </div>

                  {/* 검색 결과 드롭다운 */}
                  {showPatientDropdown && patientSearchResults.length > 0 && (
                    <ul className="patient-dropdown">
                      {patientSearchResults.map((patient) => (
                        <li
                          key={patient.id}
                          onClick={() => handlePatientSelect(patient)}
                          className="patient-item"
                        >
                          <span className="patient-name">{patient.name}</span>
                          <span className="patient-info">
                            {patient.patient_number} | {patient.gender === 'M' ? '남' : patient.gender === 'F' ? '여' : '기타'} | {patient.age}세
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}

                  {showPatientDropdown && patientSearchQuery && patientSearchResults.length === 0 && !isSearching && (
                    <div className="no-results">검색 결과가 없습니다.</div>
                  )}
                </div>

                {selectedPatient && (
                  <div className="selected-patient-info">
                    <strong>{selectedPatient.name}</strong>
                    <span>{selectedPatient.patient_number}</span>
                    <span>{selectedPatient.gender === 'M' ? '남' : selectedPatient.gender === 'F' ? '여' : '기타'}</span>
                    <span>{selectedPatient.age}세</span>
                    <span>{selectedPatient.phone}</span>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>작업 역할 *</label>
                <select
                  value={createForm.job_role}
                  onChange={(e) => {
                    setCreateForm({ ...createForm, job_role: e.target.value as JobRole, job_type: '' });
                    setJobTypeSearch('');
                  }}
                >
                  {Object.entries(JOB_ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>작업 유형 *</label>
                <input
                  type="text"
                  placeholder="검색 (예: CT, MRI, CBC...)"
                  value={jobTypeSearch}
                  onChange={(e) => setJobTypeSearch(e.target.value)}
                  className="search-input"
                />
                <select
                  value={createForm.job_type || ''}
                  onChange={(e) => setCreateForm({ ...createForm, job_type: e.target.value })}
                  size={5}
                  className="searchable-select"
                >
                  <option value="">작업 유형을 선택하세요</option>
                  {(JOB_TYPE_OPTIONS[createForm.job_role as JobRole] || [])
                    .filter(type => type.toLowerCase().includes(jobTypeSearch.toLowerCase()))
                    .map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                </select>
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
              <button className="btn secondary" onClick={() => setIsCreateModalOpen(false)}>
                취소
              </button>
              <button
                className="btn primary"
                onClick={handleCreateOrder}
                disabled={!createForm.patient_id || !createForm.job_type}
              >
                생성
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .patient-search-container {
          position: relative;
        }

        .search-input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .search-input-wrapper input {
          width: 100%;
          padding: 8px 12px;
          padding-right: 60px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .search-input-wrapper input.selected {
          background-color: #e8f5e9;
          border-color: #4caf50;
        }

        .search-input-wrapper .clear-btn {
          position: absolute;
          right: 8px;
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #999;
          padding: 0 8px;
        }

        .search-input-wrapper .clear-btn:hover {
          color: #333;
        }

        .searching-indicator {
          position: absolute;
          right: 40px;
          font-size: 12px;
          color: #666;
        }

        .patient-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: white;
          border: 1px solid #ddd;
          border-top: none;
          border-radius: 0 0 4px 4px;
          max-height: 200px;
          overflow-y: auto;
          z-index: 1000;
          list-style: none;
          padding: 0;
          margin: 0;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .patient-item {
          padding: 10px 12px;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #eee;
        }

        .patient-item:last-child {
          border-bottom: none;
        }

        .patient-item:hover {
          background-color: #f5f5f5;
        }

        .patient-name {
          font-weight: 500;
        }

        .patient-info {
          font-size: 12px;
          color: #666;
        }

        .no-results {
          padding: 12px;
          text-align: center;
          color: #666;
          font-size: 14px;
        }

        .selected-patient-info {
          margin-top: 8px;
          padding: 10px;
          background-color: #f8f9fa;
          border-radius: 4px;
          display: flex;
          gap: 12px;
          align-items: center;
          font-size: 13px;
        }

        .selected-patient-info strong {
          color: #333;
        }

        .selected-patient-info span {
          color: #666;
        }

        .search-input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          margin-bottom: 8px;
        }

        .searchable-select {
          width: 100%;
          padding: 4px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .searchable-select option {
          padding: 8px;
        }

        .searchable-select option:hover {
          background-color: #f5f5f5;
        }

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
