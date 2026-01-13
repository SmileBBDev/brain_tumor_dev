/**
 * ExaminationTab - 진찰 탭 (ClinicPage용)
 * - 환자 주의사항 표시
 * - SOAP 노트 입력/표시
 * - 처방 및 오더 관리
 * - 검사 결과 확인
 * - 최근 진료/검사 이력
 * - AI 분석 요약
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getExaminationSummary,
  getPatientAlerts,
  createPatientAlert,
  updatePatientAlert,
  deletePatientAlert,
} from '@/services/patient.api';
import { updateEncounter } from '@/services/encounter.api';
import type {
  PatientAlert,
  PatientAlertCreateData,
  ExaminationSummary,
  AlertType,
  AlertSeverity,
} from '@/types/patient';
import type { OCSListItem } from '@/types/ocs';
import type { Encounter } from '@/types/encounter';
import PrescriptionCard from './DiagnosisPrescriptionCard';
import './ExaminationTab.css';

interface ExaminationTabProps {
  patientId: number;
  encounterId: number | null;
  encounter: Encounter | null;
  ocsList: OCSListItem[];
  onUpdate: () => void;
}

// 심각도 색상
const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  HIGH: '#d32f2f',
  MEDIUM: '#f57c00',
  LOW: '#1976d2',
};

// 타입 아이콘
const ALERT_TYPE_ICONS: Record<AlertType, string> = {
  ALLERGY: '⚠️',
  CONTRAINDICATION: '🚫',
  PRECAUTION: '⚡',
  OTHER: 'ℹ️',
};

interface SOAPData {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

// 상태 표시 텍스트
const OCS_STATUS_LABELS: Record<string, string> = {
  ORDERED: '오더됨',
  ACCEPTED: '접수됨',
  IN_PROGRESS: '진행 중',
  RESULT_READY: '결과 대기',
  CONFIRMED: '확정됨',
  CANCELLED: '취소됨',
};

// 작업 역할 표시
const JOB_ROLE_LABELS: Record<string, string> = {
  RIS: '영상',
  LIS: '검사',
};

// 검사 유형 라벨
const JOB_TYPE_LABELS: Record<string, string> = {
  BLOOD: '혈액검사',
  URINE: '소변검사',
  GENETIC: '유전자검사',
  PROTEIN: '단백질검사',
  PATHOLOGY: '병리검사',
};

export default function ExaminationTab({
  patientId,
  encounterId,
  encounter,
  ocsList,
  onUpdate,
}: ExaminationTabProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<ExaminationSummary | null>(null);
  const [alerts, setAlerts] = useState<PatientAlert[]>([]);
  const [soapData, setSOAPData] = useState<SOAPData>({
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
  });
  const [savingSOAP, setSavingSOAP] = useState(false);
  const [soapSaved, setSOAPSaved] = useState(false);

  // 주호소 (읽기 전용 - SOAP Subjective에서 입력)
  const [chiefComplaint, setChiefComplaint] = useState('');

  // Alert 모달 상태
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PatientAlert | null>(null);

  // 토스트 메시지
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 토스트 표시 헬퍼
  const showToast = (type: 'success' | 'error', text: string) => {
    setToastMessage({ type, text });
    setTimeout(() => setToastMessage(null), 3000);
  };

  // 데이터 로드
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, alertsData] = await Promise.all([
        getExaminationSummary(patientId).catch(() => null),
        getPatientAlerts(patientId).catch(() => []),
      ]);

      if (summaryData) {
        setSummary(summaryData);
        // 현재 진료의 SOAP 데이터 로드
        if (summaryData.current_encounter) {
          setSOAPData({
            subjective: summaryData.current_encounter.subjective || '',
            objective: summaryData.current_encounter.objective || '',
            assessment: summaryData.current_encounter.assessment || '',
            plan: summaryData.current_encounter.plan || '',
          });
        }
        // 주호소 초기화 (현재 진료 > 환자 기본)
        setChiefComplaint(
          summaryData.current_encounter?.chief_complaint ||
          summaryData.patient?.chief_complaint ||
          ''
        );
      }
      setAlerts(alertsData);
    } catch (err) {
      console.error('Failed to load examination data:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // SOAP 저장
  const handleSaveSOAP = async () => {
    if (!encounterId) return;

    setSavingSOAP(true);
    setSOAPSaved(false);
    try {
      await updateEncounter(encounterId, soapData);
      onUpdate();
      setSOAPSaved(true);
      setTimeout(() => setSOAPSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save SOAP:', err);
      showToast('error', 'SOAP 저장에 실패했습니다.');
    } finally {
      setSavingSOAP(false);
    }
  };

  // Alert 추가
  const handleAddAlert = () => {
    setEditingAlert(null);
    setShowAlertModal(true);
  };

  // Alert 편집
  const handleEditAlert = (alert: PatientAlert) => {
    setEditingAlert(alert);
    setShowAlertModal(true);
  };

  // Alert 삭제
  const handleDeleteAlert = async (alertId: number) => {
    if (!confirm('이 주의사항을 삭제하시겠습니까?')) return;

    try {
      await deletePatientAlert(patientId, alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      showToast('success', '주의사항이 삭제되었습니다.');
    } catch (err) {
      console.error('Failed to delete alert:', err);
      showToast('error', '삭제에 실패했습니다.');
    }
  };

  // Alert 저장
  const handleSaveAlert = async (data: PatientAlertCreateData) => {
    try {
      if (editingAlert) {
        const updated = await updatePatientAlert(patientId, editingAlert.id, data);
        setAlerts((prev) => prev.map((a) => (a.id === editingAlert.id ? updated : a)));
        showToast('success', '주의사항이 수정되었습니다.');
      } else {
        const created = await createPatientAlert(patientId, data);
        setAlerts((prev) => [created, ...prev]);
        showToast('success', '주의사항이 추가되었습니다.');
      }
      setShowAlertModal(false);
    } catch (err) {
      console.error('Failed to save alert:', err);
      showToast('error', '저장에 실패했습니다.');
    }
  };

  if (loading) {
    return <div className="examination-tab loading">로딩 중...</div>;
  }

  const activeAlerts = alerts.filter((a) => a.is_active);

  return (
    <div className="examination-tab enhanced">
      {/* 토스트 메시지 */}
      {toastMessage && (
        <div className={`toast-message toast-${toastMessage.type}`}>
          {toastMessage.text}
        </div>
      )}

      {/* 상단 요약 영역: 주의사항 + 기본정보 */}
      <div className="top-summary-row">
        {/* 환자 주의사항 */}
        <section className="exam-section alert-section compact">
          <div className="section-header">
            <h4>
              <span className="section-icon warning">!</span>
              주의사항
              {activeAlerts.length > 0 && (
                <span className="alert-count">{activeAlerts.length}</span>
              )}
            </h4>
            <button className="btn btn-sm btn-outline" onClick={handleAddAlert}>
              + 추가
            </button>
          </div>
          {activeAlerts.length === 0 ? (
            <div className="empty-message small">등록된 주의사항이 없습니다.</div>
          ) : (
            <div className="alert-list horizontal">
              {activeAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className="alert-chip"
                  style={{ borderColor: SEVERITY_COLORS[alert.severity] }}
                  onClick={() => handleEditAlert(alert)}
                  title={alert.description || alert.title}
                >
                  <span className="alert-icon">{ALERT_TYPE_ICONS[alert.alert_type]}</span>
                  <span className="alert-title">{alert.title}</span>
                  <button
                    className="btn-remove"
                    onClick={(e) => { e.stopPropagation(); handleDeleteAlert(alert.id); }}
                  >
                    ×
                  </button>
                </div>
              ))}
              {activeAlerts.length > 3 && (
                <span className="more-alerts">+{activeAlerts.length - 3}개</span>
              )}
            </div>
          )}
        </section>

        {/* 환자 기본정보 - 간소화 */}
        {summary?.patient && (
          <section className="exam-section info-section compact">
            <h4>
              <span className="section-icon info">i</span>
              기본정보
            </h4>
            <div className="info-chips">
              <span className="info-chip">
                <span className="chip-label">혈액형</span>
                <span className="chip-value">{summary.patient.blood_type || '-'}</span>
              </span>
              <span className="info-chip">
                <span className="chip-label">알레르기</span>
                <span className="chip-value">
                  {summary.patient.allergies?.length > 0
                    ? summary.patient.allergies.slice(0, 2).join(', ')
                    : '-'}
                </span>
              </span>
              <span className="info-chip">
                <span className="chip-label">기저질환</span>
                <span className="chip-value">
                  {summary.patient.chronic_diseases?.length > 0
                    ? summary.patient.chronic_diseases.slice(0, 2).join(', ')
                    : '-'}
                </span>
              </span>
              {chiefComplaint && (
                <span className="info-chip highlight">
                  <span className="chip-label">주호소</span>
                  <span className="chip-value">{chiefComplaint}</span>
                </span>
              )}
            </div>
          </section>
        )}
      </div>

      {/* 메인 컨텐츠: 3컬럼 그리드 */}
      <div className="main-content-grid three-column">
        {/* 컬럼 1: SOAP 노트 */}
        <div className="content-column soap-column">
          <section className="exam-section soap-section">
            <div className="section-header">
              <h4>
                <span className="section-icon edit">S</span>
                SOAP 노트
              </h4>
              <button
                className={`btn btn-sm ${soapSaved ? 'btn-success' : 'btn-primary'}`}
                onClick={handleSaveSOAP}
                disabled={savingSOAP || !encounterId}
              >
                {savingSOAP ? '저장 중...' : soapSaved ? '저장됨 ✓' : '저장'}
              </button>
            </div>
            {!encounterId ? (
              <div className="empty-message">진료 시작 후 작성 가능</div>
            ) : (
              <div className="soap-form compact">
                <div className="soap-field">
                  <label>S - 주관적 소견</label>
                  <textarea
                    value={soapData.subjective}
                    onChange={(e) => setSOAPData({ ...soapData, subjective: e.target.value })}
                    placeholder="환자가 호소하는 증상..."
                    rows={2}
                  />
                </div>
                <div className="soap-field">
                  <label>O - 객관적 소견</label>
                  <textarea
                    value={soapData.objective}
                    onChange={(e) => setSOAPData({ ...soapData, objective: e.target.value })}
                    placeholder="검사 결과, 관찰 소견..."
                    rows={2}
                  />
                </div>
                <div className="soap-field">
                  <label>A - 평가</label>
                  <textarea
                    value={soapData.assessment}
                    onChange={(e) => setSOAPData({ ...soapData, assessment: e.target.value })}
                    placeholder="진단, 감별진단..."
                    rows={2}
                  />
                </div>
                <div className="soap-field">
                  <label>P - 계획</label>
                  <textarea
                    value={soapData.plan}
                    onChange={(e) => setSOAPData({ ...soapData, plan: e.target.value })}
                    placeholder="치료 계획, 처방..."
                    rows={2}
                  />
                </div>
              </div>
            )}
          </section>

          {/* AI 분석 요약 - SOAP 아래로 이동 */}
          {summary?.ai_summary && (
            <section className="exam-section ai-section">
              <h4>
                <span className="section-icon ai">AI</span>
                AI 분석 요약
              </h4>
              <div className="ai-summary compact">
                <div className="ai-meta">
                  분석일: {summary.ai_summary.created_at?.split('T')[0]}
                </div>
                <pre className="ai-result">
                  {JSON.stringify(summary.ai_summary.result, null, 2)}
                </pre>
              </div>
            </section>
          )}
        </div>

        {/* 컬럼 2: 처방 + 최근 이력 */}
        <div className="content-column middle-column">
          <PrescriptionCard
            patientId={patientId}
            encounter={encounter}
          />

          {/* 최근 이력 */}
          {summary && (
            <section className="exam-section history-section compact">
              <h4>
                <span className="section-icon history">H</span>
                최근 이력
              </h4>
              <div className="history-tabs">
                <div className="history-tab-content">
                  {/* 최근 진료 */}
                  <div className="history-mini-list">
                    <h5>진료 ({summary.recent_encounters?.length || 0})</h5>
                    {summary.recent_encounters?.length === 0 ? (
                      <div className="empty-message small">기록 없음</div>
                    ) : (
                      <ul className="history-list mini">
                        {summary.recent_encounters?.slice(0, 3).map((enc) => (
                          <li key={enc.id}>
                            <span className="date">{enc.encounter_date?.split('T')[0]}</span>
                            <span className="type">{enc.encounter_type_display}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* 최근 검사 */}
                  <div className="history-mini-list">
                    <h5>검사</h5>
                    <div className="ocs-inline">
                      <span className="ocs-badge ris">RIS {summary.recent_ocs?.ris?.length || 0}</span>
                      <span className="ocs-badge lis">LIS {summary.recent_ocs?.lis?.length || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>

        {/* 컬럼 3: 검사 오더 + 결과 + AI 요청 */}
        <div className="content-column order-column">
          {/* 검사 오더 */}
          <section className="exam-section order-card">
            <div className="section-header">
              <h4>
                <span className="card-icon">📋</span>
                검사 오더
                <span className="order-counts">
                  <span className="pending-count">
                    {ocsList.filter(o => ['ORDERED', 'ACCEPTED', 'IN_PROGRESS'].includes(o.ocs_status)).length}
                  </span>
                  /
                  <span className="completed-count">
                    {ocsList.filter(o => ['RESULT_READY', 'CONFIRMED'].includes(o.ocs_status)).length}
                  </span>
                </span>
              </h4>
              <button
                className="btn btn-sm btn-primary"
                onClick={() => navigate(`/ocs/create?patientId=${patientId}`)}
              >
                + 새 오더
              </button>
            </div>
            {ocsList.length === 0 ? (
              <div className="empty-message">등록된 오더가 없습니다.</div>
            ) : (
              <div className="order-list">
                {ocsList.slice(0, 6).map((ocs) => (
                  <div
                    key={ocs.id}
                    className="order-item"
                    onClick={() => {
                      if (ocs.job_role === 'RIS') {
                        navigate(`/ocs/ris/${ocs.id}`);
                      } else if (ocs.job_role === 'LIS') {
                        navigate(`/ocs/lis/${ocs.id}`);
                      }
                    }}
                  >
                    <div className="order-item-content">
                      <div className="order-item-title">
                        <span className={`job-role-badge ${ocs.job_role.toLowerCase()}`}>
                          {JOB_ROLE_LABELS[ocs.job_role] || ocs.job_role}
                        </span>
                        {JOB_TYPE_LABELS[ocs.job_type] || ocs.job_type}
                      </div>
                      <div className="order-item-subtitle">
                        {ocs.ocs_id} | {ocs.created_at?.slice(0, 10)}
                      </div>
                    </div>
                    <span className={`status-badge ${ocs.ocs_status.toLowerCase()}`}>
                      {OCS_STATUS_LABELS[ocs.ocs_status] || ocs.ocs_status}
                    </span>
                  </div>
                ))}
                {ocsList.length > 6 && (
                  <div className="more-link" onClick={() => navigate(`/ocs/manage?patientId=${patientId}`)}>
                    +{ocsList.length - 6}개 더 보기
                  </div>
                )}
              </div>
            )}
          </section>

          {/* AI 추론 요청 섹션 */}
          <section className="exam-section ai-request-card">
            <div className="section-header">
              <h4>
                <span className="card-icon">🤖</span>
                AI 추론 요청
              </h4>
              <button
                className="btn btn-sm btn-primary"
                onClick={() => navigate(`/ai/requests/create?patientId=${patientId}`)}
              >
                AI 추론 요청
              </button>
            </div>
            <div className="ai-model-info">
              <p className="info-text">환자의 검사 데이터를 기반으로 AI 분석을 요청합니다.</p>
              <div className="model-badges">
                <span className="model-badge" title="MRI 4-Channel (T1, T2, T1C, FLAIR)">M1 - MRI 분석</span>
                <span className="model-badge" title="Genetic Analysis (RNA_seq)">MG - 유전자 분석</span>
                <span className="model-badge" title="Multimodal (MRI + 유전 + 단백질)">MM - 멀티모달</span>
              </div>
            </div>
          </section>

          {/* 검사 결과 (LIS) */}
          <section className="exam-section result-card">
            <h4>
              <span className="card-icon">🔬</span>
              검사 결과
              <span className="result-count">
                ({ocsList.filter(o => o.job_role === 'LIS' && ['RESULT_READY', 'CONFIRMED'].includes(o.ocs_status)).length})
              </span>
            </h4>
            {(() => {
              const lisResults = ocsList.filter(o => o.job_role === 'LIS');
              const confirmedResults = lisResults.filter(o => ['RESULT_READY', 'CONFIRMED'].includes(o.ocs_status));

              if (confirmedResults.length === 0) {
                return <div className="empty-message">검사 결과가 없습니다.</div>;
              }

              return (
                <div className="result-list">
                  {confirmedResults.slice(0, 5).map((result) => (
                    <div
                      key={result.id}
                      className="result-item"
                      onClick={() => navigate(`/ocs/lis/${result.id}`)}
                    >
                      <div className="result-item-content">
                        <div className="result-item-title">
                          {JOB_TYPE_LABELS[result.job_type] || result.job_type}
                        </div>
                        <div className="result-item-subtitle">
                          {result.ocs_id} | {result.created_at?.slice(0, 10)}
                        </div>
                      </div>
                      <span className={`status-badge ${result.ocs_status.toLowerCase()}`}>
                        {OCS_STATUS_LABELS[result.ocs_status] || result.ocs_status}
                      </span>
                    </div>
                  ))}
                </div>
              );
            })()}
          </section>
        </div>
      </div>

      {/* Alert 추가/편집 모달 */}
      {showAlertModal && (
        <AlertModal
          alertData={editingAlert}
          onClose={() => setShowAlertModal(false)}
          onSave={handleSaveAlert}
        />
      )}
    </div>
  );
}

// Alert 모달 컴포넌트 (인라인)
interface AlertModalProps {
  alertData: PatientAlert | null;
  onClose: () => void;
  onSave: (data: PatientAlertCreateData) => void;
}

function AlertModal({ alertData, onClose, onSave }: AlertModalProps) {
  const [formData, setFormData] = useState<PatientAlertCreateData>({
    alert_type: alertData?.alert_type || 'PRECAUTION',
    severity: alertData?.severity || 'MEDIUM',
    title: alertData?.title || '',
    description: alertData?.description || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      window.alert('제목을 입력하세요.');
      return;
    }
    onSave(formData);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>{alertData ? '주의사항 편집' : '주의사항 추가'}</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>유형</label>
            <select
              value={formData.alert_type}
              onChange={(e) => setFormData({ ...formData, alert_type: e.target.value as AlertType })}
            >
              <option value="ALLERGY">알러지</option>
              <option value="CONTRAINDICATION">금기</option>
              <option value="PRECAUTION">주의</option>
              <option value="OTHER">기타</option>
            </select>
          </div>
          <div className="form-group">
            <label>심각도</label>
            <select
              value={formData.severity}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as AlertSeverity })}
            >
              <option value="HIGH">높음</option>
              <option value="MEDIUM">중간</option>
              <option value="LOW">낮음</option>
            </select>
          </div>
          <div className="form-group">
            <label>제목 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="예: 페니실린 알러지"
            />
          </div>
          <div className="form-group">
            <label>설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="추가 설명..."
              rows={3}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              취소
            </button>
            <button type="submit" className="btn btn-primary">
              저장
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
