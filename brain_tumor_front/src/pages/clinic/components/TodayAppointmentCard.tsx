/**
 * 금일 예약 환자 카드
 * - 오늘 예약된 환자 목록 표시
 * - GET /api/encounters/today/ 우선 사용 (fallback: 기존 필터)
 */
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getEncounters, getTodayEncounters } from '@/services/encounter.api';
import type { Encounter } from '@/types/encounter';

export default function TodayAppointmentCard() {
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);

  // 오늘 날짜
  const today = useMemo(() => {
    return new Date().toISOString().split('T')[0];
  }, []);

  // 데이터 로드
  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        // 1차: /encounters/today/ 엔드포인트 시도
        try {
          const response = await getTodayEncounters();
          // API가 {count, date, results} 형식으로 반환
          const data = Array.isArray(response) ? response : (response as any)?.results || [];
          setAppointments(data);
          return;
        } catch {
          // fallback: 기존 필터 방식 사용
        }

        // 2차: 기존 필터 방식 (scheduled + 오늘 날짜)
        const response = await getEncounters({
          status: 'scheduled',
          encounter_date: today,
        });
        const data = Array.isArray(response) ? response : response?.results || [];
        setAppointments(data);
      } catch (err) {
        console.error('Failed to fetch appointments:', err);
        setAppointments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, [today]);

  // 환자 진료 페이지로 이동
  const handleSelectPatient = (encounter: Encounter) => {
    navigate(`/patientsCare?patientId=${encounter.patient}`);
  };

  // 시간 순 정렬
  const sortedAppointments = useMemo(() => {
    return [...appointments].sort((a, b) => {
      const timeA = a.scheduled_time || '00:00';
      const timeB = b.scheduled_time || '00:00';
      return timeA.localeCompare(timeB);
    });
  }, [appointments]);

  return (
    <div className="clinic-card">
      <div className="clinic-card-header">
        <h3>
          <span className="card-icon">📋</span>
          금일 예약 환자
          <span className="appointment-count">({appointments.length})</span>
        </h3>
      </div>
      <div className="clinic-card-body appointment-body">
        {loading ? (
          <div className="loading-state">
            <span>로딩 중...</span>
          </div>
        ) : sortedAppointments.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📅</div>
            <div className="empty-state-text">오늘 예약된 환자가 없습니다.</div>
          </div>
        ) : (
          <div className="appointment-list">
            {sortedAppointments.map((appointment) => (
              <div
                key={appointment.id}
                className="appointment-item"
                onClick={() => handleSelectPatient(appointment)}
              >
                <div className="appointment-time">
                  {appointment.scheduled_time?.slice(0, 5) || '--:--'}
                </div>
                <div className="appointment-info">
                  <div className="patient-name">
                    {appointment.patient_name || `환자 #${appointment.patient}`}
                  </div>
                  <div className="appointment-type">
                    {appointment.encounter_type === 'outpatient' && '외래'}
                    {appointment.encounter_type === 'inpatient' && '입원'}
                    {appointment.encounter_type === 'emergency' && '응급'}
                  </div>
                </div>
                <div className="appointment-action">
                  <button className="btn btn-sm btn-primary">진료</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .appointment-count {
          font-size: 12px;
          font-weight: normal;
          color: var(--text-secondary, #666);
          margin-left: 4px;
        }
        .appointment-body {
          max-height: 300px;
          overflow-y: auto;
          padding: 0;
        }
        .loading-state {
          padding: 32px;
          text-align: center;
          color: var(--text-secondary, #666);
        }
        .appointment-list {
          padding: 0;
        }
        .appointment-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color, #e0e0e0);
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .appointment-item:last-child {
          border-bottom: none;
        }
        .appointment-item:hover {
          background: var(--bg-secondary, #f5f5f5);
        }
        .appointment-time {
          font-size: 16px;
          font-weight: 600;
          font-family: monospace;
          color: var(--primary, #1976d2);
          min-width: 50px;
        }
        .appointment-info {
          flex: 1;
        }
        .patient-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary, #1a1a1a);
        }
        .appointment-type {
          font-size: 12px;
          color: var(--text-secondary, #666);
        }
        .appointment-action {
          flex-shrink: 0;
        }
      `}</style>
    </div>
  );
}
