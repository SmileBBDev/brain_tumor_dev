/**
 * 간호사 진료 접수 페이지 (P.66)
 * - 오늘 접수된 환자 목록
 * - 의사별 확인 탭
 * - 이달 예약 현황 목록
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getEncounters, getEncounterStatistics } from '@/services/encounter.api';
import { fetchUsers } from '@/services/users.api';
import type { Encounter, EncounterSearchParams, EncounterStatus, EncounterStatistics } from '@/types/encounter';
import type { User } from '@/types/user';
import Pagination from '@/layout/Pagination';
import './NurseReceptionPage.css';

// 날짜 포맷
const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

const formatTime = (dateStr: string | undefined): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 상태 표시
const STATUS_CONFIG: Record<EncounterStatus, { label: string; className: string }> = {
  scheduled: { label: '예정', className: 'status-scheduled' },
  'in_progress': { label: '진행중', className: 'status-in_progress' },
  completed: { label: '완료', className: 'status-completed' },
  cancelled: { label: '취소', className: 'status-cancelled' },
};

// 오늘 날짜 문자열
const getTodayString = (): string => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

// 월별 범위 계산 (offset: -1=전월, 0=당월, 1=차월)
const getMonthRange = (offset: number = 0): { start: string; end: string; month: number; year: number } => {
  const now = new Date();
  const targetMonth = now.getMonth() + offset;
  const start = new Date(now.getFullYear(), targetMonth, 1);
  const end = new Date(now.getFullYear(), targetMonth + 1, 0);
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
    month: start.getMonth() + 1,
    year: start.getFullYear(),
  };
};

export default function NurseReceptionPage() {
  const navigate = useNavigate();

  // 탭 상태
  const [activeTab, setActiveTab] = useState<'today' | 'monthly'>('today');
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | 'all'>('all');
  const [monthOffset, setMonthOffset] = useState<number>(0); // -1=전월, 0=당월, 1=차월

  // 의사 목록
  const [doctors, setDoctors] = useState<User[]>([]);

  // 오늘 접수 데이터
  const [todayEncounters, setTodayEncounters] = useState<Encounter[]>([]);
  const [todayLoading, setTodayLoading] = useState(false);

  // 월간 예약 데이터
  const [monthlyEncounters, setMonthlyEncounters] = useState<Encounter[]>([]);
  const [monthlyPage, setMonthlyPage] = useState(1);
  const [monthlyTotalCount, setMonthlyTotalCount] = useState(0);
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const pageSize = 15;

  // 통계
  const [_statistics, setStatistics] = useState<EncounterStatistics | null>(null);

  // 의사 목록 로드
  useEffect(() => {
    const loadDoctors = async () => {
      try {
        const response = await fetchUsers({ role__code: 'DOCTOR', is_active: true });
        setDoctors(response.results || []);
      } catch (error) {
        console.error('Failed to fetch doctors:', error);
      }
    };
    loadDoctors();
  }, []);

  // 통계 로드
  useEffect(() => {
    const loadStatistics = async () => {
      try {
        const stats = await getEncounterStatistics();
        setStatistics(stats);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
      }
    };
    loadStatistics();
  }, []);

  // 오늘 접수 로드 (모든 상태 - 예정/진행중/완료)
  const loadTodayEncounters = useCallback(async () => {
    setTodayLoading(true);
    try {
      const today = getTodayString();
      const params: EncounterSearchParams = {
        start_date: today,
        end_date: today,
        page_size: 100, // 오늘 전체
        // status 제거 - 모든 상태 조회 (scheduled, in_progress, completed)
      };

      if (selectedDoctorId !== 'all') {
        params.attending_doctor = selectedDoctorId;
      }

      const response = await getEncounters(params);
      let encounters: Encounter[] = [];
      if (Array.isArray(response)) {
        encounters = response;
      } else {
        encounters = response.results || [];
      }

      // 취소된 건 제외
      encounters = encounters.filter(enc => enc.status !== 'cancelled');
      setTodayEncounters(encounters);
    } catch (error) {
      console.error('Failed to fetch today encounters:', error);
    } finally {
      setTodayLoading(false);
    }
  }, [selectedDoctorId]);

  // 월간 예약 로드
  const loadMonthlyEncounters = useCallback(async () => {
    setMonthlyLoading(true);
    try {
      const { start, end } = getMonthRange(monthOffset);
      const params: EncounterSearchParams = {
        start_date: start,
        end_date: end,
        status: 'scheduled',
        page: monthlyPage,
        page_size: pageSize,
      };

      if (selectedDoctorId !== 'all') {
        params.attending_doctor = selectedDoctorId;
      }

      const response = await getEncounters(params);
      if (Array.isArray(response)) {
        setMonthlyEncounters(response);
        setMonthlyTotalCount(response.length);
      } else {
        setMonthlyEncounters(response.results || []);
        setMonthlyTotalCount(response.count || 0);
      }
    } catch (error) {
      console.error('Failed to fetch monthly encounters:', error);
    } finally {
      setMonthlyLoading(false);
    }
  }, [selectedDoctorId, monthlyPage, monthOffset]);

  // 현재 선택된 월 정보
  const currentMonthInfo = useMemo(() => getMonthRange(monthOffset), [monthOffset]);

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'today') {
      loadTodayEncounters();
    } else {
      loadMonthlyEncounters();
    }
  }, [activeTab, loadTodayEncounters, loadMonthlyEncounters]);

  // 오늘 상태별 집계
  const todaySummary = useMemo(() => {
    const summary = {
      total: todayEncounters.length,
      scheduled: 0,
      inProgress: 0,
      completed: 0,
    };

    todayEncounters.forEach((enc) => {
      if (enc.status === 'scheduled') summary.scheduled++;
      else if (enc.status === 'in_progress') summary.inProgress++;
      else if (enc.status === 'completed') summary.completed++;
    });

    return summary;
  }, [todayEncounters]);

  // 행 클릭 시 환자 상세로 이동
  const handleRowClick = (encounter: Encounter) => {
    navigate(`/patient/${encounter.patient}`);
  };

  // 월간 페이지 수
  const monthlyTotalPages = Math.ceil(monthlyTotalCount / pageSize);

  return (
    <div className="page nurse-reception-page">
      {/* 헤더 */}
      <header className="page-header">
        <h2>진료 접수 현황</h2>
        <span className="subtitle">오늘 접수 및 예약 현황을 관리합니다</span>
      </header>

      {/* 오늘 요약 카드 */}
      <section className="summary-cards">
        <div className="summary-card total">
          <span className="card-label">오늘 총 접수</span>
          <span className="card-value">{todaySummary.total}</span>
          <span className="card-unit">건</span>
        </div>
        <div className="summary-card scheduled">
          <span className="card-label">대기중</span>
          <span className="card-value">{todaySummary.scheduled}</span>
          <span className="card-unit">건</span>
        </div>
        <div className="summary-card in_progress">
          <span className="card-label">진행중</span>
          <span className="card-value">{todaySummary.inProgress}</span>
          <span className="card-unit">건</span>
        </div>
        <div className="summary-card completed">
          <span className="card-label">완료</span>
          <span className="card-value">{todaySummary.completed}</span>
          <span className="card-unit">건</span>
        </div>
      </section>

      {/* 의사별 필터 탭 */}
      <section className="doctor-filter">
        <button
          className={`doctor-tab ${selectedDoctorId === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedDoctorId('all')}
        >
          전체 의사
        </button>
        {doctors.map((doctor) => (
          <button
            key={doctor.id}
            className={`doctor-tab ${selectedDoctorId === doctor.id ? 'active' : ''}`}
            onClick={() => setSelectedDoctorId(doctor.id)}
          >
            {doctor.name}
          </button>
        ))}
      </section>

      {/* 탭 메뉴 */}
      <nav className="tab-nav">
        <button
          className={activeTab === 'today' ? 'active' : ''}
          onClick={() => setActiveTab('today')}
        >
          오늘 접수 ({todaySummary.total})
        </button>
        <div className="month-nav-group">
          <button
            className={`month-nav-btn ${activeTab === 'monthly' && monthOffset === -1 ? 'active' : ''}`}
            onClick={() => { setActiveTab('monthly'); setMonthOffset(-1); setMonthlyPage(1); }}
          >
            전월 ({getMonthRange(-1).month}월)
          </button>
          <button
            className={`month-nav-btn ${activeTab === 'monthly' && monthOffset === 0 ? 'active' : ''}`}
            onClick={() => { setActiveTab('monthly'); setMonthOffset(0); setMonthlyPage(1); }}
          >
            당월 ({getMonthRange(0).month}월)
          </button>
          <button
            className={`month-nav-btn ${activeTab === 'monthly' && monthOffset === 1 ? 'active' : ''}`}
            onClick={() => { setActiveTab('monthly'); setMonthOffset(1); setMonthlyPage(1); }}
          >
            차월 ({getMonthRange(1).month}월)
          </button>
        </div>
      </nav>

      {/* 콘텐츠 */}
      <section className="content">
        {/* 오늘 접수 탭 */}
        {activeTab === 'today' && (
          <div className="today-tab">
            {todayLoading ? (
              <div className="loading">로딩 중...</div>
            ) : todayEncounters.length === 0 ? (
              <div className="empty-message">오늘 접수된 환자가 없습니다.</div>
            ) : (
              <table className="reception-table">
                <thead>
                  <tr>
                    <th>접수 시간</th>
                    <th>환자명</th>
                    <th>환자번호</th>
                    <th>진료 유형</th>
                    <th>담당의</th>
                    <th>주호소</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {todayEncounters.map((encounter) => (
                    <tr
                      key={encounter.id}
                      onClick={() => handleRowClick(encounter)}
                      className="clickable-row"
                    >
                      <td>{formatTime(encounter.admission_date)}</td>
                      <td className="patient-name">{encounter.patient_name}</td>
                      <td>{encounter.patient_number}</td>
                      <td>{encounter.encounter_type_display}</td>
                      <td>{encounter.attending_doctor_name}</td>
                      <td className="chief-complaint">{encounter.chief_complaint}</td>
                      <td>
                        <span className={`status-badge ${STATUS_CONFIG[encounter.status]?.className}`}>
                          {STATUS_CONFIG[encounter.status]?.label || encounter.status_display}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* 월간 예약 탭 */}
        {activeTab === 'monthly' && (
          <div className="monthly-tab">
            <div className="monthly-header">
              <h4>{currentMonthInfo.year}년 {currentMonthInfo.month}월 예약 현황</h4>
              <span className="monthly-count">총 {monthlyTotalCount}건</span>
            </div>
            {monthlyLoading ? (
              <div className="loading">로딩 중...</div>
            ) : monthlyEncounters.length === 0 ? (
              <div className="empty-message">{currentMonthInfo.month}월 예약 환자가 없습니다.</div>
            ) : (
              <>
                <table className="reception-table">
                  <thead>
                    <tr>
                      <th>예약일</th>
                      <th>예약 시간</th>
                      <th>환자명</th>
                      <th>환자번호</th>
                      <th>진료 유형</th>
                      <th>담당의</th>
                      <th>진료과</th>
                      <th>주호소</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyEncounters.map((encounter) => (
                      <tr
                        key={encounter.id}
                        onClick={() => handleRowClick(encounter)}
                        className="clickable-row"
                      >
                        <td>{formatDate(encounter.admission_date)}</td>
                        <td>{formatTime(encounter.admission_date)}</td>
                        <td className="patient-name">{encounter.patient_name}</td>
                        <td>{encounter.patient_number}</td>
                        <td>{encounter.encounter_type_display}</td>
                        <td>{encounter.attending_doctor_name}</td>
                        <td>{encounter.department_display}</td>
                        <td className="chief-complaint">{encounter.chief_complaint}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <Pagination
                  currentPage={monthlyPage}
                  totalPages={monthlyTotalPages}
                  onChange={setMonthlyPage}
                  pageSize={pageSize}
                />
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
