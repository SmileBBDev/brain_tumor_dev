/**
 * 간호사 대시보드 (진료 접수 현황 통합)
 * - 오늘 접수 요약 카드
 * - 의사별 필터
 * - 오늘 접수 / 월간 진료 현황 탭
 * - 환자 목록 위젯
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getEncounters, getTodayEncounters } from '@/services/encounter.api';
import { fetchUsers } from '@/services/users.api';
import type { Encounter, EncounterSearchParams, EncounterStatus } from '@/types/encounter';
import type { User } from '@/types/user';
import Pagination from '@/layout/Pagination';
import PatientListWidget from '../common/PatientListWidget';
import { UnifiedCalendar } from '@/components/calendar/UnifiedCalendar';
import '@/assets/style/patientListView.css';
import './NurseDashboard.css';

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

export default function NurseDashboard() {
  const navigate = useNavigate();

  // 탭 상태
  const [activeTab, setActiveTab] = useState<'today' | 'monthly'>('today');
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | 'all'>('all');
  const [monthOffset, setMonthOffset] = useState<number | null>(0);

  // 의사 목록
  const [doctors, setDoctors] = useState<User[]>([]);

  // 오늘 접수 데이터
  const [todayEncounters, setTodayEncounters] = useState<Encounter[]>([]);
  const [todayLoading, setTodayLoading] = useState(false);

  // 월간 데이터
  const [monthlyEncounters, setMonthlyEncounters] = useState<Encounter[]>([]);
  const [monthlyPage, setMonthlyPage] = useState(1);
  const [monthlyTotalCount, setMonthlyTotalCount] = useState(0);
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const pageSize = 10;

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

  // 오늘 접수 로드
  const loadTodayEncounters = useCallback(async () => {
    setTodayLoading(true);
    try {
      let encounters = await getTodayEncounters();
      encounters = encounters.filter(enc => enc.status !== 'cancelled');

      if (selectedDoctorId !== 'all') {
        encounters = encounters.filter(enc => enc.attending_doctor === selectedDoctorId);
      }

      setTodayEncounters(encounters);
    } catch (error) {
      console.error('Failed to fetch today encounters:', error);
    } finally {
      setTodayLoading(false);
    }
  }, [selectedDoctorId]);

  // 월간 로드
  const loadMonthlyEncounters = useCallback(async () => {
    setMonthlyLoading(true);
    try {
      const params: EncounterSearchParams = {
        page: monthlyPage,
        page_size: pageSize,
      };

      if (monthOffset !== null) {
        const { start, end } = getMonthRange(monthOffset);
        params.start_date = start;
        params.end_date = end;
      }

      if (selectedDoctorId !== 'all') {
        params.attending_doctor = selectedDoctorId;
      }

      const response = await getEncounters(params);
      let encounters: Encounter[] = [];
      if (Array.isArray(response)) {
        encounters = response;
        setMonthlyTotalCount(response.length);
      } else {
        encounters = response.results || [];
        setMonthlyTotalCount(response.count || 0);
      }

      encounters = encounters.filter(enc => enc.status !== 'cancelled');
      setMonthlyEncounters(encounters);
    } catch (error) {
      console.error('Failed to fetch monthly encounters:', error);
    } finally {
      setMonthlyLoading(false);
    }
  }, [selectedDoctorId, monthlyPage, monthOffset]);

  // 현재 선택된 월 정보
  const currentMonthInfo = useMemo(() => monthOffset !== null ? getMonthRange(monthOffset) : null, [monthOffset]);

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
    const summary = { total: todayEncounters.length, scheduled: 0, inProgress: 0, completed: 0 };
    todayEncounters.forEach((enc) => {
      if (enc.status === 'scheduled') summary.scheduled++;
      else if (enc.status === 'in_progress') summary.inProgress++;
      else if (enc.status === 'completed') summary.completed++;
    });
    return summary;
  }, [todayEncounters]);

  // 행 클릭
  const handleRowClick = (encounter: Encounter) => {
    navigate(`/patients/${encounter.patient}`);
  };

  const monthlyTotalPages = Math.ceil(monthlyTotalCount / pageSize);

  return (
    <div className="dashboard nurse nurse-dashboard">
      {/* 오늘 요약 카드 */}
      <section className="summary-cards nurse-summary">
        <div className="card summary total">
          <span className="title">오늘 총 접수</span>
          <strong className="value">{todaySummary.total}</strong>
        </div>
        <div className="card summary scheduled">
          <span className="title">대기중</span>
          <strong className="value">{todaySummary.scheduled}</strong>
        </div>
        <div className="card summary in-progress">
          <span className="title">진행중</span>
          <strong className="value">{todaySummary.inProgress}</strong>
        </div>
        <div className="card summary completed">
          <span className="title">완료</span>
          <strong className="value">{todaySummary.completed}</strong>
        </div>
      </section>

      {/* 의사별 필터 */}
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
            className={`month-nav-btn ${activeTab === 'monthly' && monthOffset === null ? 'active' : ''}`}
            onClick={() => { setActiveTab('monthly'); setMonthOffset(null); setMonthlyPage(1); }}
          >
            전체
          </button>
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

      {/* 메인 콘텐츠 */}
      <div className="dashboard-main">
        {/* 접수 테이블 */}
        <section className="card reception-content">
          {activeTab === 'today' && (
            <div className="today-tab">
              {todayLoading ? (
                <div className="loading">로딩 중...</div>
              ) : todayEncounters.length === 0 ? (
                <div className="empty-message">오늘 접수된 환자가 없습니다.</div>
              ) : (
                <table className="table reception-table">
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

          {activeTab === 'monthly' && (
            <div className="monthly-tab">
              <div className="monthly-header">
                <h4>
                  {currentMonthInfo
                    ? `${currentMonthInfo.year}년 ${currentMonthInfo.month}월 진료 현황`
                    : '전체 진료 현황'}
                </h4>
                <span className="monthly-count">총 {monthlyTotalCount}건</span>
              </div>
              {monthlyLoading ? (
                <div className="loading">로딩 중...</div>
              ) : monthlyEncounters.length === 0 ? (
                <div className="empty-message">
                  {currentMonthInfo
                    ? `${currentMonthInfo.month}월 진료 환자가 없습니다.`
                    : '등록된 진료가 없습니다.'}
                </div>
              ) : (
                <>
                  <table className="table reception-table">
                    <thead>
                      <tr>
                        <th>예약일</th>
                        <th>시간</th>
                        <th>환자명</th>
                        <th>환자번호</th>
                        <th>진료 유형</th>
                        <th>담당의</th>
                        <th>상태</th>
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
                          <td>
                            <span className={`status-badge ${STATUS_CONFIG[encounter.status]?.className}`}>
                              {STATUS_CONFIG[encounter.status]?.label || encounter.status_display}
                            </span>
                          </td>
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

        {/* 사이드 패널: 환자 목록 + 캘린더 */}
        <div className="dashboard-sidebar">
          <PatientListWidget
            title="환자 목록"
            limit={5}
            showViewAll={true}
            compact={true}
          />
          <UnifiedCalendar title="간호사 통합 캘린더" />
        </div>
      </div>
    </div>
  );
}
