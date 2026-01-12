/**
 * 진찰 탭 (기존 AI 분석 탭 대체)
 * - 의사 소견 입력/조회
 * - AI 분석 결과 표시 (내부 항목으로)
 * - 모든 권한 읽기 가능, 의사만 수정 가능
 */
import { useState, useEffect } from 'react';
import { getPatientAIRequests, type AIInferenceRequest } from '@/services/ai.api';
import '@/assets/style/patientListView.css';

interface Props {
  role: string;
  patientId?: number;
}

export default function ExaminationTab({ role, patientId }: Props) {
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';
  const canEdit = isDoctor || isSystemManager;

  const [aiRequests, setAIRequests] = useState<AIInferenceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [doctorNote, setDoctorNote] = useState('');

  useEffect(() => {
    if (!patientId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await getPatientAIRequests(patientId);
        const aiData = Array.isArray(data) ? data : (data as any)?.results || [];
        setAIRequests(aiData.slice(0, 5));
      } catch (err) {
        console.error('Failed to fetch AI requests:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [patientId]);

  if (loading) {
    return (
      <div className="examination-tab">
        <div className="loading-state">데이터 로딩 중...</div>
      </div>
    );
  }

  if (!patientId) {
    return (
      <div className="examination-tab">
        <div className="empty-state">환자 정보를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="examination-tab">
      {/* 의사 소견 */}
      <section className="exam-section">
        <h3>의사 소견</h3>
        {canEdit ? (
          <textarea
            className="doctor-note-input"
            placeholder="진찰 소견을 입력하세요..."
            rows={6}
            value={doctorNote}
            onChange={(e) => setDoctorNote(e.target.value)}
          />
        ) : (
          <div className="doctor-note-view">
            {doctorNote || '등록된 소견이 없습니다.'}
          </div>
        )}
        {canEdit && (
          <div className="section-actions">
            <button className="btn btn-primary" onClick={() => alert('저장 기능은 API 연동 후 활성화됩니다.')}>
              소견 저장
            </button>
          </div>
        )}
      </section>

      {/* AI 분석 결과 */}
      <section className="exam-section">
        <h3>AI 분석 이력 ({aiRequests.length}건)</h3>
        {aiRequests.length === 0 ? (
          <div className="empty-message">AI 분석 이력이 없습니다.</div>
        ) : (
          <div className="ai-requests-list">
            {aiRequests.map((req) => (
              <div key={req.id} className="ai-request-card">
                <div className="ai-request-header">
                  <span className="model-name">{req.model_name || req.model_code}</span>
                  <span className={`status-badge status-${req.status.toLowerCase()}`}>
                    {req.status_display || req.status}
                  </span>
                </div>
                <div className="ai-request-meta">
                  <span>요청일: {req.requested_at?.split('T')[0]}</span>
                  {req.completed_at && (
                    <span>완료일: {req.completed_at?.split('T')[0]}</span>
                  )}
                </div>
                {req.has_result && req.result && (
                  <div className="ai-result-preview">
                    <strong>신뢰도: {(req.result.confidence_score ?? 0) * 100}%</strong>
                    {req.result.review_status && (
                      <span className={`review-badge review-${req.result.review_status}`}>
                        {req.result.review_status_display}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <style>{`
        .examination-tab {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .exam-section {
          background: var(--bg-primary, #fff);
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 8px;
          padding: 16px;
        }
        .exam-section h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary, #1a1a1a);
        }
        .doctor-note-input {
          width: 100%;
          padding: 12px;
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 6px;
          font-size: 14px;
          resize: vertical;
          font-family: inherit;
        }
        .doctor-note-input:focus {
          outline: none;
          border-color: var(--primary, #1976d2);
        }
        .doctor-note-view {
          padding: 12px;
          background: var(--bg-secondary, #f5f5f5);
          border-radius: 6px;
          color: var(--text-secondary, #666);
          min-height: 100px;
        }
        .section-actions {
          margin-top: 12px;
          display: flex;
          justify-content: flex-end;
        }
        .ai-requests-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .ai-request-card {
          padding: 12px;
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 6px;
          background: var(--bg-secondary, #fafafa);
        }
        .ai-request-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .model-name {
          font-weight: 600;
          color: var(--text-primary, #1a1a1a);
        }
        .status-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          color: #fff;
        }
        .status-pending { background: #9e9e9e; }
        .status-validating { background: #2196f3; }
        .status-processing { background: #ff9800; }
        .status-completed { background: #4caf50; }
        .status-failed { background: #f44336; }
        .ai-request-meta {
          font-size: 12px;
          color: var(--text-secondary, #666);
          display: flex;
          gap: 16px;
        }
        .ai-result-preview {
          margin-top: 8px;
          padding: 8px;
          background: #fff;
          border-radius: 4px;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .review-badge {
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 10px;
          font-weight: 500;
        }
        .review-pending { background: #e0e0e0; color: #666; }
        .review-approved { background: #c8e6c9; color: #2e7d32; }
        .review-rejected { background: #ffcdd2; color: #c62828; }
        .empty-message {
          padding: 24px;
          text-align: center;
          color: var(--text-secondary, #666);
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
