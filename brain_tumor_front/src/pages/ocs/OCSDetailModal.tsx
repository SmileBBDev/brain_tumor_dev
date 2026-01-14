import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import {
  getOCS,
  acceptOCS,
  startOCS,
  submitOCSResult,
  confirmOCS,
  cancelOCS,
} from '@/services/ocs.api';
import type { OCSDetail, OCSHistory } from '@/types/ocs';
import '@/pages/patient/PatientCreateModal.css';

type Props = {
  isOpen: boolean;
  ocsId: number;
  onClose: () => void;
  onSuccess: () => void;
};

// 날짜 포맷
const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export default function OCSDetailModal({ isOpen, ocsId, onClose, onSuccess }: Props) {
  const { role, user } = useAuth();
  const [ocs, setOcs] = useState<OCSDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'info' | 'result' | 'history'>('info');
  const [cancelReason, setCancelReason] = useState('');

  useEffect(() => {
    if (isOpen && ocsId) {
      fetchOCSDetail();
    }
  }, [isOpen, ocsId]);

  const fetchOCSDetail = async () => {
    setLoading(true);
    try {
      const data = await getOCS(ocsId);
      setOcs(data);
    } catch (error) {
      console.error('Failed to fetch OCS detail:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // 권한 체크
  const isDoctor = ocs?.doctor.id === user?.id;
  const isWorker = ocs?.worker?.id === user?.id;
  const isAdmin = ['SYSTEMMANAGER', 'ADMIN'].includes(role || '');
  const canAccept =
    ocs?.ocs_status === 'ORDERED' &&
    !ocs?.worker &&
    (role === ocs?.job_role || isAdmin);
  const canStart = ocs?.ocs_status === 'ACCEPTED' && isWorker;
  const canSubmit = ocs?.ocs_status === 'IN_PROGRESS' && isWorker;
  const canConfirm = ocs?.ocs_status === 'RESULT_READY' && isDoctor;
  const canCancel =
    ocs?.is_editable &&
    (isDoctor || isWorker) &&
    ocs?.ocs_status !== 'CONFIRMED' &&
    ocs?.ocs_status !== 'CANCELLED';

  // 액션 핸들러들
  const handleAccept = async () => {
    if (!ocs) return;
    setActionLoading(true);
    try {
      await acceptOCS(ocs.id);
      await fetchOCSDetail();
      onSuccess();
    } catch (error) {
      console.error('Failed to accept OCS:', error);
      alert('접수에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStart = async () => {
    if (!ocs) return;
    setActionLoading(true);
    try {
      await startOCS(ocs.id);
      await fetchOCSDetail();
      onSuccess();
    } catch (error) {
      console.error('Failed to start OCS:', error);
      alert('작업 시작에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!ocs) return;
    setActionLoading(true);
    try {
      await submitOCSResult(ocs.id, {
        worker_result: ocs.worker_result,
        attachments: ocs.attachments,
      });
      await fetchOCSDetail();
      onSuccess();
    } catch (error) {
      console.error('Failed to submit OCS result:', error);
      alert('결과 제출에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirm = async (result: boolean) => {
    if (!ocs) return;
    setActionLoading(true);
    try {
      await confirmOCS(ocs.id, { ocs_result: result });
      await fetchOCSDetail();
      onSuccess();
    } catch (error) {
      console.error('Failed to confirm OCS:', error);
      alert('확정에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!ocs) return;
    if (!confirm('정말 취소하시겠습니까?')) return;
    setActionLoading(true);
    try {
      await cancelOCS(ocs.id, { cancel_reason: cancelReason });
      await fetchOCSDetail();
      onSuccess();
      setCancelReason('');
    } catch (error) {
      console.error('Failed to cancel OCS:', error);
      alert('취소에 실패했습니다.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-xl" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>OCS 상세 정보</h2>
          <button className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        {loading ? (
          <div className="modal-body">로딩 중...</div>
        ) : ocs ? (
          <>
            {/* 탭 메뉴 */}
            <div className="tab-menu">
              <button
                className={activeTab === 'info' ? 'active' : ''}
                onClick={() => setActiveTab('info')}
              >
                기본 정보
              </button>
              <button
                className={activeTab === 'result' ? 'active' : ''}
                onClick={() => setActiveTab('result')}
              >
                요청/결과
              </button>
              <button
                className={activeTab === 'history' ? 'active' : ''}
                onClick={() => setActiveTab('history')}
              >
                이력
              </button>
            </div>

            <div className="modal-body">
              {/* 기본 정보 탭 */}
              {activeTab === 'info' && (
                <div className="info-grid">
                  <div className="info-row">
                    <label>OCS ID:</label>
                    <span>{ocs.ocs_id}</span>
                  </div>
                  <div className="info-row">
                    <label>상태:</label>
                    <span className={`status-badge status-${ocs.ocs_status.toLowerCase()}`}>
                      {ocs.ocs_status_display}
                    </span>
                  </div>
                  <div className="info-row">
                    <label>우선순위:</label>
                    <span className={`priority-badge priority-${ocs.priority}`}>
                      {ocs.priority_display}
                    </span>
                  </div>
                  <div className="info-row">
                    <label>환자:</label>
                    <span>{ocs.patient.name} ({ocs.patient.patient_number})</span>
                  </div>
                  <div className="info-row">
                    <label>처방 의사:</label>
                    <span>{ocs.doctor.name}</span>
                  </div>
                  <div className="info-row">
                    <label>작업자:</label>
                    <span>{ocs.worker ? ocs.worker.name : '미배정'}</span>
                  </div>
                  <div className="info-row">
                    <label>작업 역할:</label>
                    <span>{ocs.job_role}</span>
                  </div>
                  <div className="info-row">
                    <label>작업 유형:</label>
                    <span>{ocs.job_type}</span>
                  </div>
                  <div className="info-row">
                    <label>생성일시:</label>
                    <span>{formatDate(ocs.created_at)}</span>
                  </div>
                  <div className="info-row">
                    <label>접수일시:</label>
                    <span>{formatDate(ocs.accepted_at)}</span>
                  </div>
                  <div className="info-row">
                    <label>진행시작:</label>
                    <span>{formatDate(ocs.in_progress_at)}</span>
                  </div>
                  <div className="info-row">
                    <label>결과대기:</label>
                    <span>{formatDate(ocs.result_ready_at)}</span>
                  </div>
                  <div className="info-row">
                    <label>확정일시:</label>
                    <span>{formatDate(ocs.confirmed_at)}</span>
                  </div>
                  {ocs.ocs_status === 'CONFIRMED' && (
                    <div className="info-row">
                      <label>결과:</label>
                      <span>{ocs.ocs_result ? '정상' : '비정상'}</span>
                    </div>
                  )}
                  {ocs.cancel_reason && (
                    <div className="info-row">
                      <label>취소 사유:</label>
                      <span>{ocs.cancel_reason}</span>
                    </div>
                  )}
                </div>
              )}

              {/* 요청/결과 탭 */}
              {activeTab === 'result' && (
                <div className="result-section">
                  <h4>의사 요청</h4>
                  {ocs.doctor_request && Object.keys(ocs.doctor_request).length > 0 ? (
                    <pre className="json-viewer">
                      {JSON.stringify(ocs.doctor_request, null, 2)}
                    </pre>
                  ) : (
                    <p className="no-data">아직 요청 내용이 없습니다.</p>
                  )}

                  <h4>작업 결과</h4>
                  {ocs.worker_result && Object.keys(ocs.worker_result).length > 0 ? (
                    <pre className="json-viewer">
                      {JSON.stringify(ocs.worker_result, null, 2)}
                    </pre>
                  ) : (
                    <p className="no-data">아직 결과가 없습니다.</p>
                  )}

                  {ocs.attachments?.files && ocs.attachments.files.length > 0 && (
                    <>
                      <h4>첨부파일</h4>
                      <ul className="attachment-list">
                        {ocs.attachments.files.map((file, idx) => (
                          <li key={idx}>
                            {file.name} ({(file.size / 1024).toFixed(1)} KB)
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}

              {/* 이력 탭 */}
              {activeTab === 'history' && (
                <div className="history-section">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>일시</th>
                        <th>액션</th>
                        <th>수행자</th>
                        <th>상태 변경</th>
                        <th>사유</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ocs.history.map((h: OCSHistory) => (
                        <tr key={h.id}>
                          <td>{formatDate(h.created_at)}</td>
                          <td>{h.action_display}</td>
                          <td>
                            {h.actor
                              ? h.actor.name
                              : '-'}
                          </td>
                          <td>
                            {h.from_status && h.to_status
                              ? `${h.from_status} → ${h.to_status}`
                              : h.to_status || '-'}
                          </td>
                          <td>{h.reason || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* 액션 버튼 */}
            <div className="modal-footer">
              {canCancel && (
                <div className="cancel-section">
                  <input
                    type="text"
                    placeholder="취소 사유 (선택)"
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                  />
                  <button
                    className="btn danger"
                    onClick={handleCancel}
                    disabled={actionLoading}
                  >
                    취소
                  </button>
                </div>
              )}

              <div className="action-buttons">
                {canAccept && (
                  <button
                    className="btn primary"
                    onClick={handleAccept}
                    disabled={actionLoading}
                  >
                    접수하기
                  </button>
                )}
                {canStart && (
                  <button
                    className="btn primary"
                    onClick={handleStart}
                    disabled={actionLoading}
                  >
                    작업 시작
                  </button>
                )}
                {canSubmit && (
                  <button
                    className="btn primary"
                    onClick={handleSubmit}
                    disabled={actionLoading}
                  >
                    결과 제출
                  </button>
                )}
                {canConfirm && (
                  <>
                    <button
                      className="btn success"
                      onClick={() => handleConfirm(true)}
                      disabled={actionLoading}
                    >
                      정상 확정
                    </button>
                    <button
                      className="btn warning"
                      onClick={() => handleConfirm(false)}
                      disabled={actionLoading}
                    >
                      비정상 확정
                    </button>
                  </>
                )}
                <button className="btn secondary" onClick={onClose}>
                  닫기
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="modal-body">OCS 정보를 불러올 수 없습니다.</div>
        )}
      </div>
    </div>
  );
}
