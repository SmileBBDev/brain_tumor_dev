/**
 * 통합 캘린더 컴포넌트
 * - 공유 일정 (읽기 전용) + 개인 일정 (CRUD) 표시
 * - Dashboard용 통합 캘린더
 */
import { useState, useMemo, useEffect, useCallback } from 'react';
import {
  getUnifiedCalendar,
  createPersonalSchedule,
  updatePersonalSchedule,
  deletePersonalSchedule,
} from '@/services/schedule.api';
import type {
  UnifiedScheduleItem,
  PersonalScheduleCreateRequest,
  PersonalScheduleUpdateRequest,
  ScheduleType,
  ScheduleScope,
} from '@/types/schedule';
import {
  SCHEDULE_TYPE_LABELS,
  SCHEDULE_TYPE_COLORS,
  SCOPE_LABELS,
  SCOPE_COLORS,
} from '@/types/schedule';
import './UnifiedCalendar.css';

interface UnifiedCalendarProps {
  title?: string;
  patientId?: number; // 진료탭용 환자 ID
  showManageButton?: boolean; // 관리 버튼 표시 여부 (Admin용)
  onManageClick?: () => void; // 관리 버튼 클릭 핸들러
}

interface ScheduleModalData {
  mode: 'create' | 'edit' | 'view';
  schedule?: UnifiedScheduleItem;
  date?: string;
}

export function UnifiedCalendar({ title = '통합 캘린더', patientId, showManageButton, onManageClick }: UnifiedCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [sharedSchedules, setSharedSchedules] = useState<UnifiedScheduleItem[]>([]);
  const [personalSchedules, setPersonalSchedules] = useState<UnifiedScheduleItem[]>([]);
  const [patientSchedules, setPatientSchedules] = useState<UnifiedScheduleItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalData, setModalData] = useState<ScheduleModalData | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  // 필터 상태
  const [showShared, setShowShared] = useState(true);
  const [showPersonal, setShowPersonal] = useState(true);
  const [showPatient, setShowPatient] = useState(true);

  // 데이터 로드
  const loadSchedules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUnifiedCalendar({
        year: currentDate.getFullYear(),
        month: currentDate.getMonth() + 1,
        patient_id: patientId,
      });
      setSharedSchedules(data.shared);
      setPersonalSchedules(data.personal);
      setPatientSchedules(data.patient);
    } catch (err) {
      console.error('Failed to load unified calendar:', err);
      setError('캘린더를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [currentDate, patientId]);

  useEffect(() => {
    loadSchedules();
    setSelectedDay(null);
  }, [loadSchedules]);

  // 모든 일정 합치기 (필터 적용)
  const allSchedules = useMemo(() => {
    const result: UnifiedScheduleItem[] = [];
    if (showShared) result.push(...sharedSchedules);
    if (showPersonal) result.push(...personalSchedules);
    if (showPatient) result.push(...patientSchedules);
    return result;
  }, [sharedSchedules, personalSchedules, patientSchedules, showShared, showPersonal, showPatient]);

  // 현재 월의 첫째 날과 마지막 날
  const { firstDay, daysInMonth } = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const first = new Date(year, month, 1);
    const last = new Date(year, month + 1, 0);
    return {
      firstDay: first.getDay(),
      daysInMonth: last.getDate(),
    };
  }, [currentDate]);

  // 날짜별 일정 맵
  const schedulesByDate = useMemo(() => {
    const map: Record<number, UnifiedScheduleItem[]> = {};
    allSchedules.forEach((s) => {
      const start = new Date(s.start);
      const end = new Date(s.end);
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();

      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        if (d.getFullYear() === year && d.getMonth() === month) {
          const day = d.getDate();
          if (!map[day]) map[day] = [];
          if (!map[day].some((item) => item.id === s.id && item.scope === s.scope)) {
            map[day].push(s);
          }
        }
      }
    });
    return map;
  }, [allSchedules, currentDate]);

  // 네비게이션
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // 캘린더 그리드 생성
  const calendarDays = useMemo(() => {
    const days: (number | null)[] = [];
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let i = 1; i <= daysInMonth; i++) days.push(i);
    return days;
  }, [firstDay, daysInMonth]);

  const today = new Date();
  const isToday = (day: number) => {
    return (
      day === today.getDate() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getFullYear() === today.getFullYear()
    );
  };

  // 날짜의 우선 scope 색상 (배경색 결정)
  const getPrimaryScopeColor = (day: number): string | null => {
    const daySchedules = schedulesByDate[day];
    if (!daySchedules || daySchedules.length === 0) return null;

    // scope 우선순위: shared > personal > patient
    const priority: ScheduleScope[] = ['shared', 'personal', 'patient'];
    for (const scope of priority) {
      const found = daySchedules.find(s => s.scope === scope);
      if (found) return SCOPE_COLORS[scope];
    }
    return SCOPE_COLORS[daySchedules[0].scope];
  };

  // 날짜 클릭
  const handleDayClick = (day: number | null) => {
    if (!day) return;

    if (selectedDay === day) {
      // 같은 날짜 다시 클릭시 새 개인 일정 생성
      const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      setModalData({ mode: 'create', date: dateStr });
    } else {
      setSelectedDay(day);
    }
  };

  // 일정 클릭
  const handleScheduleClick = (schedule: UnifiedScheduleItem) => {
    if (schedule.scope === 'personal') {
      setModalData({ mode: 'edit', schedule });
    } else {
      // 공유/환자 일정은 보기만 가능
      setModalData({ mode: 'view', schedule });
    }
  };

  // 새 일정 추가 버튼
  const handleAddSchedule = () => {
    if (!selectedDay) return;
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDay).padStart(2, '0')}`;
    setModalData({ mode: 'create', date: dateStr });
  };

  // 모달 닫기
  const closeModal = () => {
    setModalData(null);
  };

  // 요일 헤더
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  // 선택된 날짜의 일정 목록
  const selectedDaySchedules = selectedDay ? schedulesByDate[selectedDay] || [] : [];

  return (
    <section className="card unified-calendar">
      <header className="card-header">
        <h3>{title}</h3>
        <div className="header-buttons">
          {showManageButton && onManageClick && (
            <button className="btn btn-sm btn-primary" onClick={onManageClick}>
              캘린더 관리
            </button>
          )}
          <button className="btn btn-sm btn-secondary" onClick={goToToday}>
            오늘
          </button>
        </div>
      </header>

      <div className="calendar-body">
        {/* 월 네비게이션 */}
        <div className="calendar-nav">
          <button className="nav-btn" onClick={prevMonth}>
            &lt;
          </button>
          <span className="nav-title">
            {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
          </span>
          <button className="nav-btn" onClick={nextMonth}>
            &gt;
          </button>
        </div>

        {/* Scope 필터 */}
        <div className="scope-filters">
          <label className={`filter-item ${showShared ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={showShared}
              onChange={(e) => setShowShared(e.target.checked)}
            />
            <span className="filter-color" style={{ backgroundColor: SCOPE_COLORS.shared }} />
            {SCOPE_LABELS.shared}
          </label>
          <label className={`filter-item ${showPersonal ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={showPersonal}
              onChange={(e) => setShowPersonal(e.target.checked)}
            />
            <span className="filter-color" style={{ backgroundColor: SCOPE_COLORS.personal }} />
            {SCOPE_LABELS.personal}
          </label>
          {patientId && (
            <label className={`filter-item ${showPatient ? 'active' : ''}`}>
              <input
                type="checkbox"
                checked={showPatient}
                onChange={(e) => setShowPatient(e.target.checked)}
              />
              <span className="filter-color" style={{ backgroundColor: SCOPE_COLORS.patient }} />
              {SCOPE_LABELS.patient}
            </label>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-state">로딩 중...</div>
        ) : (
          <>
            {/* 요일 헤더 */}
            <div className="calendar-weekdays">
              {weekDays.map((day, idx) => (
                <div
                  key={day}
                  className={`weekday ${idx === 0 ? 'sun' : ''} ${idx === 6 ? 'sat' : ''}`}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* 날짜 그리드 */}
            <div className="calendar-grid">
              {calendarDays.map((day, idx) => {
                const daySchedules = day ? schedulesByDate[day] : null;
                const scheduleCount = daySchedules?.length || 0;
                const primaryColor = day ? getPrimaryScopeColor(day) : null;
                const isTodayCell = day ? isToday(day) : false;
                const isSelected = day === selectedDay;

                const cellStyle = primaryColor
                  ? { '--schedule-color': primaryColor } as React.CSSProperties
                  : undefined;

                return (
                  <div
                    key={idx}
                    className={`calendar-day ${day ? 'clickable' : 'empty'} ${isTodayCell ? 'today' : ''} ${isSelected ? 'selected' : ''} ${scheduleCount > 0 ? 'has-schedule' : ''}`}
                    style={cellStyle}
                    onClick={() => handleDayClick(day)}
                  >
                    {day && (
                      <>
                        <span className={`day-number ${scheduleCount > 0 ? 'bold' : ''}`}>
                          {day}
                        </span>
                        {scheduleCount > 1 && (
                          <span className="schedule-badge" style={{ backgroundColor: primaryColor || '#5b8def' }}>
                            {scheduleCount}
                          </span>
                        )}
                        {scheduleCount === 1 && primaryColor && (
                          <span
                            className="schedule-type-dot"
                            style={{ backgroundColor: primaryColor }}
                          />
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 범례 */}
            <div className="calendar-legend">
              {(Object.keys(SCOPE_LABELS) as ScheduleScope[]).map((scope) => (
                <div key={scope} className="legend-item">
                  <span
                    className="legend-color"
                    style={{ backgroundColor: SCOPE_COLORS[scope] }}
                  />
                  <span>{SCOPE_LABELS[scope]}</span>
                </div>
              ))}
            </div>

            {/* 선택된 날짜 상세 패널 */}
            {selectedDay && (
              <div className="selected-day-panel">
                <div className="panel-header">
                  <span className="panel-title">
                    {currentDate.getMonth() + 1}월 {selectedDay}일 일정
                  </span>
                  <button className="btn-add" onClick={handleAddSchedule}>
                    + 개인 일정 추가
                  </button>
                </div>

                {selectedDaySchedules.length === 0 ? (
                  <div className="panel-empty">
                    선택한 날짜에 일정이 없습니다.
                  </div>
                ) : (
                  <ul className="schedule-list">
                    {selectedDaySchedules.map((s) => (
                      <li
                        key={`${s.scope}-${s.id}`}
                        className="schedule-item"
                        onClick={() => handleScheduleClick(s)}
                      >
                        <span
                          className="schedule-color"
                          style={{ backgroundColor: s.color || SCOPE_COLORS[s.scope] }}
                        />
                        <div className="schedule-info">
                          <span className="schedule-title">
                            {s.title}
                            {s.scope !== 'personal' && (
                              <span className={`scope-tag scope-${s.scope}`}>
                                {SCOPE_LABELS[s.scope]}
                              </span>
                            )}
                          </span>
                          <span className="schedule-type">
                            {s.schedule_type_display}
                            {s.all_day ? ' (종일)' : ` ${s.start.slice(11, 16)}`}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* 일정 모달 */}
      {modalData && (
        <PersonalScheduleModal
          mode={modalData.mode}
          schedule={modalData.schedule}
          defaultDate={modalData.date}
          onClose={closeModal}
          onSave={loadSchedules}
        />
      )}
    </section>
  );
}

// =============================================================================
// 개인 일정 생성/수정/보기 모달
// =============================================================================
interface PersonalScheduleModalProps {
  mode: 'create' | 'edit' | 'view';
  schedule?: UnifiedScheduleItem;
  defaultDate?: string;
  onClose: () => void;
  onSave: () => void;
}

function PersonalScheduleModal({ mode, schedule, defaultDate, onClose, onSave }: PersonalScheduleModalProps) {
  const isViewOnly = mode === 'view';
  const isEdit = mode === 'edit';

  const [title, setTitle] = useState(schedule?.title || '');
  const [scheduleType, setScheduleType] = useState<ScheduleType>(schedule?.schedule_type || 'personal');
  const [startDate, setStartDate] = useState(
    schedule ? schedule.start.slice(0, 10) : defaultDate || ''
  );
  const [startTime, setStartTime] = useState(
    schedule && !schedule.all_day ? schedule.start.slice(11, 16) : '09:00'
  );
  const [endDate, setEndDate] = useState(
    schedule ? schedule.end.slice(0, 10) : defaultDate || ''
  );
  const [endTime, setEndTime] = useState(
    schedule && !schedule.all_day ? schedule.end.slice(11, 16) : '10:00'
  );
  const [allDay, setAllDay] = useState(schedule?.all_day || false);
  const [color, setColor] = useState(schedule?.color || SCHEDULE_TYPE_COLORS[scheduleType]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!schedule) {
      setColor(SCHEDULE_TYPE_COLORS[scheduleType]);
    }
  }, [scheduleType, schedule]);

  const handleSave = async () => {
    if (!title.trim()) {
      setError('제목을 입력해주세요.');
      return;
    }
    if (!startDate || !endDate) {
      setError('날짜를 선택해주세요.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const startDatetime = allDay
        ? `${startDate}T00:00:00`
        : `${startDate}T${startTime}:00`;
      const endDatetime = allDay
        ? `${endDate}T23:59:59`
        : `${endDate}T${endTime}:00`;

      if (mode === 'create') {
        const data: PersonalScheduleCreateRequest = {
          title: title.trim(),
          schedule_type: scheduleType,
          start_datetime: startDatetime,
          end_datetime: endDatetime,
          all_day: allDay,
          color,
        };
        await createPersonalSchedule(data);
      } else if (isEdit && schedule) {
        const data: PersonalScheduleUpdateRequest = {
          title: title.trim(),
          schedule_type: scheduleType,
          start_datetime: startDatetime,
          end_datetime: endDatetime,
          all_day: allDay,
          color,
        };
        await updatePersonalSchedule(schedule.id, data);
      }

      onSave();
      onClose();
    } catch (err) {
      console.error('Failed to save schedule:', err);
      setError('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!schedule) return;
    if (!confirm('이 일정을 삭제하시겠습니까?')) return;

    setDeleting(true);
    setError(null);

    try {
      await deletePersonalSchedule(schedule.id);
      onSave();
      onClose();
    } catch (err) {
      console.error('Failed to delete schedule:', err);
      setError('삭제에 실패했습니다.');
    } finally {
      setDeleting(false);
    }
  };

  const getModalTitle = () => {
    if (isViewOnly) {
      const scopeLabel = schedule?.scope ? SCOPE_LABELS[schedule.scope] : '';
      return `${scopeLabel} 상세`;
    }
    return mode === 'create' ? '개인 일정 추가' : '개인 일정 수정';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h3>{getModalTitle()}</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </header>

        <div className="modal-body">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label>제목 {!isViewOnly && '*'}</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="일정 제목을 입력하세요"
              autoFocus={!isViewOnly}
              disabled={isViewOnly}
            />
          </div>

          <div className="form-group">
            <label>유형</label>
            <select
              value={scheduleType}
              onChange={(e) => setScheduleType(e.target.value as ScheduleType)}
              disabled={isViewOnly}
            >
              {(Object.keys(SCHEDULE_TYPE_LABELS) as ScheduleType[]).map((type) => (
                <option key={type} value={type}>
                  {SCHEDULE_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>시작일 {!isViewOnly && '*'}</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isViewOnly}
              />
            </div>
            {!allDay && (
              <div className="form-group">
                <label>시작 시간</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  disabled={isViewOnly}
                />
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>종료일 {!isViewOnly && '*'}</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isViewOnly}
              />
            </div>
            {!allDay && (
              <div className="form-group">
                <label>종료 시간</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  disabled={isViewOnly}
                />
              </div>
            )}
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={allDay}
                onChange={(e) => setAllDay(e.target.checked)}
                disabled={isViewOnly}
              />
              종일
            </label>
          </div>

          {!isViewOnly && (
            <div className="form-group">
              <label>색상</label>
              <div className="color-picker">
                {Object.values(SCHEDULE_TYPE_COLORS).map((c) => (
                  <button
                    key={c}
                    className={`color-option ${color === c ? 'selected' : ''}`}
                    style={{ backgroundColor: c }}
                    onClick={() => setColor(c)}
                    type="button"
                  />
                ))}
                <input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="color-input"
                />
              </div>
            </div>
          )}
        </div>

        <footer className="modal-footer">
          {isEdit && (
            <button
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={deleting || saving}
            >
              {deleting ? '삭제 중...' : '삭제'}
            </button>
          )}
          <div className="footer-right">
            <button className="btn btn-secondary" onClick={onClose} disabled={saving || deleting}>
              {isViewOnly ? '닫기' : '취소'}
            </button>
            {!isViewOnly && (
              <button className="btn btn-primary" onClick={handleSave} disabled={saving || deleting}>
                {saving ? '저장 중...' : '저장'}
              </button>
            )}
          </div>
        </footer>
      </div>
    </div>
  );
}

export default UnifiedCalendar;
