/**
 * 환자 일정 캘린더 카드
 * - 환자의 진료 일정을 달력 형태로 표시
 * - 의사 일정도 함께 표시 (다른 색상)
 */
import { useState, useMemo, useEffect, useCallback } from 'react';
import type { Encounter } from '@/types/encounter';
import { getScheduleCalendar } from '@/services/schedule.api';
import type { CalendarScheduleItem } from '@/types/schedule';

interface CalendarCardProps {
  patientId: number;
  encounters: Encounter[];
  onDateSelect?: (date: string | null) => void;
  selectedDate?: string | null;
}

export default function CalendarCard({
  patientId: _patientId,
  encounters,
  onDateSelect,
  selectedDate,
}: CalendarCardProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [doctorSchedules, setDoctorSchedules] = useState<CalendarScheduleItem[]>([]);

  // 의사 일정 로드
  const loadDoctorSchedules = useCallback(async () => {
    try {
      const data = await getScheduleCalendar({
        year: currentDate.getFullYear(),
        month: currentDate.getMonth() + 1,
      });
      setDoctorSchedules(data);
    } catch (err) {
      console.error('Failed to load doctor schedules:', err);
      // 실패해도 환자 일정은 표시
    }
  }, [currentDate]);

  useEffect(() => {
    loadDoctorSchedules();
  }, [loadDoctorSchedules]);

  // 현재 월의 첫째 날과 마지막 날
  const { firstDay, lastDay: _lastDay, daysInMonth } = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const first = new Date(year, month, 1);
    const last = new Date(year, month + 1, 0);
    return {
      firstDay: first.getDay(),
      lastDay: last.getDate(),
      daysInMonth: last.getDate(),
    };
  }, [currentDate]);

  // 진료 날짜 추출 헬퍼 (admission_date 사용, encounter_date는 폴백)
  const getEncounterDate = (e: Encounter): string | null => {
    // admission_date: "2026-01-13T09:00:00Z" 또는 "2026-01-13"
    const dateStr = e.admission_date || e.encounter_date;
    if (!dateStr) return null;
    // ISO 형식에서 날짜 부분만 추출 (YYYY-MM-DD)
    return dateStr.slice(0, 10);
  };

  // 해당 월의 진료 일정
  const monthEncounters = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;

    return encounters.filter((e) => {
      const dateStr = getEncounterDate(e);
      return dateStr?.startsWith(monthStr);
    });
  }, [currentDate, encounters]);

  // 날짜별 진료 맵
  const encountersByDate = useMemo(() => {
    const map: Record<string, Encounter[]> = {};
    monthEncounters.forEach((e) => {
      const dateStr = getEncounterDate(e);
      if (!dateStr) return;
      const day = parseInt(dateStr.split('-')[2] || '0', 10);
      if (!map[day]) map[day] = [];
      map[day].push(e);
    });
    return map;
  }, [monthEncounters]);

  // 날짜별 의사 일정 맵
  const doctorSchedulesByDate = useMemo(() => {
    const map: Record<number, CalendarScheduleItem[]> = {};
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    doctorSchedules.forEach((s) => {
      const start = new Date(s.start);
      const end = new Date(s.end);

      // 일정이 걸치는 모든 날짜에 추가
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        if (d.getFullYear() === year && d.getMonth() === month) {
          const day = d.getDate();
          if (!map[day]) map[day] = [];
          if (!map[day].some((item) => item.id === s.id)) {
            map[day].push(s);
          }
        }
      }
    });
    return map;
  }, [doctorSchedules, currentDate]);

  // 이전 달
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  // 다음 달
  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  // 오늘로 이동
  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // 요일 헤더
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  // 달력 그리드 생성
  const calendarDays = useMemo(() => {
    const days: (number | null)[] = [];

    // 첫째 주 빈 칸
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    // 날짜
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

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

  // 선택된 날짜인지 확인
  const isSelected = (day: number) => {
    if (!selectedDate) return false;
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return dateStr === selectedDate;
  };

  // 날짜 클릭 핸들러
  const handleDayClick = (day: number) => {
    if (!day || !encountersByDate[day]) return;

    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    if (selectedDate === dateStr) {
      // 이미 선택된 날짜 클릭 시 선택 해제
      onDateSelect?.(null);
    } else {
      onDateSelect?.(dateStr);
    }
  };

  // 해당 날짜에 일정이 있는지 (환자 또는 의사)
  const hasEvents = (day: number): boolean => {
    return !!(encountersByDate[day] || doctorSchedulesByDate[day]);
  };

  return (
    <div className="clinic-card">
      <div className="clinic-card-header">
        <h3>
          <span className="card-icon">📅</span>
          환자 일정 캘린더
        </h3>
        <button className="btn btn-sm btn-secondary" onClick={goToToday}>
          오늘
        </button>
      </div>
      <div className="clinic-card-body calendar-body">
        {/* 월 네비게이션 */}
        <div className="calendar-nav">
          <button className="nav-btn" onClick={prevMonth}>&lt;</button>
          <span className="nav-title">
            {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
          </span>
          <button className="nav-btn" onClick={nextMonth}>&gt;</button>
        </div>

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
          {calendarDays.map((day, idx) => (
            <div
              key={idx}
              className={`calendar-day ${day ? '' : 'empty'} ${day && isToday(day) ? 'today' : ''} ${
                day && hasEvents(day) ? 'has-event' : ''
              } ${day && encountersByDate[day as number] ? 'clickable' : ''} ${day && isSelected(day) ? 'selected' : ''}`}
              onClick={() => day && handleDayClick(day)}
            >
              {day && (
                <>
                  <span className="day-number">{day}</span>
                  <div className="day-events">
                    {/* 환자 진료 일정 */}
                    {encountersByDate[day]?.slice(0, 2).map((e, i) => (
                      <div
                        key={`enc-${i}`}
                        className={`event-dot ${e.status}`}
                        title={e.diagnosis || '진료'}
                      />
                    ))}
                    {/* 의사 개인 일정 */}
                    {doctorSchedulesByDate[day]?.slice(0, 1).map((s) => (
                      <div
                        key={`sch-${s.id}`}
                        className="event-dot doctor-schedule"
                        style={{ backgroundColor: s.color }}
                        title={s.title}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        {/* 범례 */}
        <div className="calendar-legend">
          <div className="legend-item">
            <span className="event-dot scheduled"></span>
            <span>예약</span>
          </div>
          <div className="legend-item">
            <span className="event-dot in_progress"></span>
            <span>진행</span>
          </div>
          <div className="legend-item">
            <span className="event-dot completed"></span>
            <span>완료</span>
          </div>
          <div className="legend-item">
            <span className="event-dot doctor-schedule" style={{ backgroundColor: '#9ca3af' }}></span>
            <span>의사일정</span>
          </div>
        </div>
      </div>

      <style>{`
        .calendar-body {
          padding: 12px;
        }
        .calendar-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .nav-btn {
          width: 28px;
          height: 28px;
          border: 1px solid var(--border, #e5e7eb);
          background: var(--card-bg, white);
          color: var(--text-main, #1f2937);
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        .nav-btn:hover {
          background: var(--bg-main, #f4f6f9);
        }
        .nav-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-main, #1f2937);
        }
        .calendar-weekdays {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          text-align: center;
          margin-bottom: 4px;
        }
        .weekday {
          font-size: 11px;
          font-weight: 500;
          color: var(--text-sub, #6b7280);
          padding: 4px;
        }
        .weekday.sun { color: var(--danger, #e56b6f); }
        .weekday.sat { color: var(--info, #5b8def); }
        .calendar-grid {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 2px;
        }
        .calendar-day {
          aspect-ratio: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          border-radius: 4px;
          cursor: default;
          position: relative;
          color: var(--text-main, #1f2937);
        }
        .calendar-day.empty {
          background: transparent;
        }
        .calendar-day.today {
          background: var(--primary, #5b6fd6);
          color: white;
        }
        .calendar-day.has-event .day-number {
          font-weight: 600;
        }
        .calendar-day.clickable {
          cursor: pointer;
        }
        .calendar-day.clickable:hover {
          background: var(--bg-main, #f4f6f9);
        }
        .calendar-day.selected {
          background: var(--info, #5b8def);
          color: white;
        }
        .calendar-day.selected:hover {
          background: var(--info, #5b8def);
        }
        .day-number {
          margin-bottom: 2px;
        }
        .day-events {
          display: flex;
          gap: 2px;
        }
        .event-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }
        .event-dot.scheduled {
          background: var(--warning, #f2a65a);
        }
        .event-dot.in_progress {
          background: var(--info, #5b8def);
        }
        .event-dot.completed {
          background: var(--success, #5fb3a2);
        }
        .event-dot.doctor-schedule {
          border: 1px solid rgba(255, 255, 255, 0.5);
        }
        .calendar-legend {
          display: flex;
          justify-content: center;
          gap: 16px;
          margin-top: 12px;
          padding-top: 8px;
          border-top: 1px solid var(--border, #e5e7eb);
          flex-wrap: wrap;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          color: var(--text-sub, #6b7280);
        }
      `}</style>
    </div>
  );
}
