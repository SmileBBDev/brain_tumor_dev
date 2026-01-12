/**
 * 환자 상세 - 요약 탭
 * - 환자 기본 정보
 * - 최근 진료 이력 (5건)
 * - OCS 이력 (최근 5건)
 * - AI 추론 이력 (최근 3건) - 의사/시스템관리자만
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPatientEncounters } from '@/services/encounter.api';
import { getOCSByPatient } from '@/services/ocs.api';
import { getPatientAIRequests } from '@/services/ai.api';
import type { Encounter } from '@/types/encounter';
import type { OCSListItem } from '@/types/ocs';
import type { AIInferenceRequest } from '@/services/ai.api';
import '@/assets/style/patientListView.css';

type Props = {
  role: string;
  patientId?: number;
};

// 상태 뱃지 스타일
const STATUS_COLORS: Record<string, string> = {
  // Encounter status
  scheduled: '#2196f3',
  in_progress: '#ff9800',
  completed: '#4caf50',
  cancelled: '#9e9e9e',
  // OCS status
  ORDERED: '#2196f3',
  ACCEPTED: '#03a9f4',
  IN_PROGRESS: '#ff9800',
  RESULT_READY: '#8bc34a',
  CONFIRMED: '#4caf50',
  CANCELLED: '#9e9e9e',
  // AI status
  PENDING: '#9e9e9e',
  VALIDATING: '#2196f3',
  PROCESSING: '#ff9800',
  COMPLETED: '#4caf50',
  FAILED: '#f44336',
};

// 날짜 포맷
const formatDate = (dateStr?: string | null): string => {
  if (!dateStr) return '-';
  return dateStr.split('T')[0];
};

export default function SummaryTab({ role, patientId }: Props) {
  const navigate = useNavigate();
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';
  const canViewAI = isDoctor || isSystemManager;

  // 상태
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [aiRequests, setAIRequests] = useState<AIInferenceRequest[]>([]);
  const [loading, setLoading] = useState(true);

  // 데이터 로드
  useEffect(() => {
    if (!patientId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        // 병렬로 데이터 로드
        const [encounterRes, ocsRes, aiRes] = await Promise.all([
          getPatientEncounters(patientId).catch(() => []),
          getOCSByPatient(patientId).catch(() => []),
          canViewAI ? getPatientAIRequests(patientId).catch(() => []) : Promise.resolve([]),
        ]);

        // API 응답이 배열 또는 {results: []} 형식일 수 있음
        const encounterData = Array.isArray(encounterRes) ? encounterRes : (encounterRes as any)?.results || [];
        const ocsData = Array.isArray(ocsRes) ? ocsRes : (ocsRes as any)?.results || [];
        const aiData = Array.isArray(aiRes) ? aiRes : (aiRes as any)?.results || [];

        setEncounters(encounterData.slice(0, 5));
        setOcsList(ocsData.slice(0, 5));
        setAIRequests(aiData.slice(0, 3));
      } catch (err) {
        console.error('Failed to fetch summary data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [patientId, canViewAI]);

  // 로딩 상태
  if (loading) {
    return (
      <div className="summary-layout">
        <div className="loading-state">데이터 로딩 중...</div>
      </div>
    );
  }

  // 환자 ID 없음
  if (!patientId) {
    return (
      <div className="summary-layout">
        <div className="empty-state">환자 정보를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="summary-layout">
      {/* 좌측 영역: 최근 진료 이력 */}
      <div className="summary-left">
        <div className="card">
          <h3>최근 진료 이력 ({encounters.length}건)</h3>
          {encounters.length === 0 ? (
            <div className="empty-message">진료 이력이 없습니다.</div>
          ) : (
            <table className="summary-table">
              <thead>
                <tr>
                  <th>날짜</th>
                  <th>유형</th>
                  <th>담당의</th>
                  <th>상태</th>
                  <th>주호소</th>
                </tr>
              </thead>
              <tbody>
                {encounters.map((enc) => (
                  <tr
                    key={enc.id}
                    className="clickable-row"
                    onClick={() => navigate(`/patientsCare?patientId=${patientId}&encounterId=${enc.id}`)}
                  >
                    <td>{formatDate(enc.encounter_date || enc.admission_date)}</td>
                    <td>{enc.encounter_type_display || enc.encounter_type}</td>
                    <td>{enc.attending_doctor_name || '-'}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ backgroundColor: STATUS_COLORS[enc.status] || '#9e9e9e' }}
                      >
                        {enc.status_display || enc.status}
                      </span>
                    </td>
                    <td className="truncate">{enc.chief_complaint || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 우측 영역: OCS 이력 + AI 추론 */}
      <div className="summary-right">
        {/* OCS 이력 */}
        <div className="card">
          <h4>OCS 이력 ({ocsList.length}건)</h4>
          {ocsList.length === 0 ? (
            <div className="empty-message">OCS 이력이 없습니다.</div>
          ) : (
            <table className="summary-table compact">
              <thead>
                <tr>
                  <th>날짜</th>
                  <th>유형</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {ocsList.map((ocs) => (
                  <tr
                    key={ocs.id}
                    className="clickable-row"
                    onClick={() => {
                      const path = ocs.job_role === 'RIS'
                        ? `/ocs/ris/${ocs.id}`
                        : `/ocs/lis/${ocs.id}`;
                      navigate(path);
                    }}
                  >
                    <td>{formatDate(ocs.created_at)}</td>
                    <td>{ocs.job_type || ocs.job_role}</td>
                    <td>
                      <span
                        className="status-badge small"
                        style={{ backgroundColor: STATUS_COLORS[ocs.ocs_status] || '#9e9e9e' }}
                      >
                        {ocs.ocs_status_display || ocs.ocs_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* AI 추론 이력 (의사/시스템관리자만) */}
        {canViewAI && (
          <div className="card ai">
            <h4>AI 추론 이력 ({aiRequests.length}건)</h4>
            {aiRequests.length === 0 ? (
              <div className="empty-message">AI 추론 이력이 없습니다.</div>
            ) : (
              <table className="summary-table compact">
                <thead>
                  <tr>
                    <th>날짜</th>
                    <th>모델</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {aiRequests.map((req) => (
                    <tr
                      key={req.id}
                      className="clickable-row"
                      onClick={() => navigate(`/ai/requests/${req.id}`)}
                    >
                      <td>{formatDate(req.requested_at)}</td>
                      <td>{req.model_name || req.model_code}</td>
                      <td>
                        <span
                          className="status-badge small"
                          style={{ backgroundColor: STATUS_COLORS[req.status] || '#9e9e9e' }}
                        >
                          {req.status_display || req.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      <style>{`
        .summary-layout {
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 20px;
          padding: 16px;
        }
        .summary-left,
        .summary-right {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .card {
          background: var(--bg-primary, #fff);
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 8px;
          padding: 16px;
        }
        .card h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #1a1a1a);
        }
        .card h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary, #1a1a1a);
        }
        .card.ai {
          border-left: 3px solid #9c27b0;
        }
        .summary-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }
        .summary-table.compact {
          font-size: 12px;
        }
        .summary-table th {
          text-align: left;
          padding: 8px 6px;
          border-bottom: 1px solid var(--border-color, #e0e0e0);
          font-weight: 500;
          color: var(--text-secondary, #666);
          white-space: nowrap;
        }
        .summary-table td {
          padding: 8px 6px;
          border-bottom: 1px solid var(--border-color, #f0f0f0);
          color: var(--text-primary, #1a1a1a);
        }
        .clickable-row {
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .clickable-row:hover {
          background: var(--bg-secondary, #f5f5f5);
        }
        .status-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          color: #fff;
        }
        .status-badge.small {
          padding: 1px 6px;
          font-size: 10px;
        }
        .truncate {
          max-width: 150px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .empty-message {
          padding: 16px;
          text-align: center;
          color: var(--text-secondary, #666);
          font-size: 13px;
        }
        .loading-state,
        .empty-state {
          padding: 40px;
          text-align: center;
          color: var(--text-secondary, #666);
        }
      `}</style>
    </div>
  );
}
