import { useState, useEffect } from 'react';
import { useAuth } from '@/pages/auth/AuthProvider';
import { getEncounters } from '@/services/encounter.api';
import type { Encounter, EncounterSearchParams, EncounterType, EncounterStatus, Department } from '@/types/encounter';
import EncounterListTable from './EncounterListTable';
import EncounterCreateModal from './EncounterCreateModal';
import EncounterEditModal from './EncounterEditModal';
import EncounterDeleteModal from './EncounterDeleteModal';
import Pagination from '@/layout/Pagination';
import '@/assets/style/encounterListView.css';

export default function EncounterListPage() {
  const { role } = useAuth();
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';
  const canCreate = isDoctor || isSystemManager;

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);

  // Data
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(false);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [encounterTypeFilter, setEncounterTypeFilter] = useState<EncounterType | ''>('');
  const [statusFilter, setStatusFilter] = useState<EncounterStatus | ''>('');
  const [departmentFilter, setDepartmentFilter] = useState<Department | ''>('');

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedEncounter, setSelectedEncounter] = useState<Encounter | null>(null);

  // Fetch encounters
  const fetchEncounters = async () => {
    setLoading(true);
    try {
      const params: EncounterSearchParams = {
        page,
        page_size: pageSize,
        ...(searchQuery && { q: searchQuery }),
        ...(encounterTypeFilter && { encounter_type: encounterTypeFilter }),
        ...(statusFilter && { status: statusFilter }),
        ...(departmentFilter && { department: departmentFilter }),
      };

      console.log('Fetching encounters with params:', params);
      const response = await getEncounters(params);
      console.log('Encounters response:', response);

      // Handle both paginated and non-paginated responses
      if (Array.isArray(response)) {
        // Direct array response (no pagination)
        setEncounters(response);
        setTotalCount(response.length);
      } else {
        // Paginated response with results and count
        setEncounters(response.results || []);
        setTotalCount(response.count || 0);
      }
    } catch (error: any) {
      console.error('Failed to fetch encounters:', error);
      console.error('Error details:', error.response?.data);
      alert(`진료 목록을 불러오는데 실패했습니다.\n${error.response?.data?.detail || error.message || '알 수 없는 오류'}`);
      // Set empty array on error to prevent undefined
      setEncounters([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEncounters();
  }, [page, searchQuery, encounterTypeFilter, statusFilter, departmentFilter]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEncounters();
  };

  // Handle create
  const handleCreateClick = () => {
    setIsCreateModalOpen(true);
  };

  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    fetchEncounters();
  };

  // Handle edit
  const handleEditClick = (encounter: Encounter) => {
    setSelectedEncounter(encounter);
    setIsEditModalOpen(true);
  };

  const handleEditSuccess = () => {
    setIsEditModalOpen(false);
    setSelectedEncounter(null);
    fetchEncounters();
  };

  // Handle delete
  const handleDeleteClick = (encounter: Encounter) => {
    setSelectedEncounter(encounter);
    setIsDeleteModalOpen(true);
  };

  const handleDeleteSuccess = () => {
    setIsDeleteModalOpen(false);
    setSelectedEncounter(null);
    fetchEncounters();
  };

  // Reset filters
  const handleResetFilters = () => {
    setSearchQuery('');
    setEncounterTypeFilter('');
    setStatusFilter('');
    setDepartmentFilter('');
    setPage(1);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>진료 목록</h1>
      </div>

      <div className="content">
        {/* Filter Bar */}
        <div className="filter-bar">
          <div className="filter-left">
            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="환자명, 환자번호, 주호소 검색"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ minWidth: '250px' }}
              />
              <button type="submit" className="btn primary">검색</button>
            </form>

            <select
              value={encounterTypeFilter}
              onChange={(e) => {
                setEncounterTypeFilter(e.target.value as EncounterType | '');
                setPage(1);
              }}
            >
              <option value="">전체 진료유형</option>
              <option value="outpatient">외래</option>
              <option value="inpatient">입원</option>
              <option value="emergency">응급</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as EncounterStatus | '');
                setPage(1);
              }}
            >
              <option value="">전체 상태</option>
              <option value="scheduled">예정</option>
              <option value="in-progress">진행중</option>
              <option value="completed">완료</option>
              <option value="cancelled">취소</option>
            </select>

            <select
              value={departmentFilter}
              onChange={(e) => {
                setDepartmentFilter(e.target.value as Department | '');
                setPage(1);
              }}
            >
              <option value="">전체 진료과</option>
              <option value="neurology">신경과</option>
              <option value="neurosurgery">신경외과</option>
            </select>

            <button className="btn" onClick={handleResetFilters}>
              필터 초기화
            </button>
          </div>

          <div className="filter-right">
            {canCreate && (
              <button className="btn primary" onClick={handleCreateClick}>
                진료 등록
              </button>
            )}
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>로딩 중...</div>
        ) : (
          <>
            <EncounterListTable
              role={role}
              encounters={encounters}
              onEdit={handleEditClick}
              onDelete={handleDeleteClick}
            />

            <Pagination
              currentPage={page}
              totalCount={totalCount}
              pageSize={pageSize}
              onPageChange={setPage}
            />
          </>
        )}
      </div>

      {/* Modals */}
      {isCreateModalOpen && (
        <EncounterCreateModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      {isEditModalOpen && selectedEncounter && (
        <EncounterEditModal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedEncounter(null);
          }}
          onSuccess={handleEditSuccess}
          encounter={selectedEncounter}
        />
      )}

      {isDeleteModalOpen && selectedEncounter && (
        <EncounterDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setSelectedEncounter(null);
          }}
          onSuccess={handleDeleteSuccess}
          encounter={selectedEncounter}
        />
      )}
    </div>
  );
}
