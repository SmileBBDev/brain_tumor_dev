import { useState } from 'react';
import { deleteEncounter } from '@/services/encounter.api';
import type { Encounter } from '@/types/encounter';
import '@/pages/patient/PatientCreateModal.css';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  encounter: Encounter;
};

export default function EncounterDeleteModal({ isOpen, onClose, onSuccess, encounter }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleDelete = async () => {
    setError('');
    setLoading(true);

    try {
      await deleteEncounter(encounter.id);
      alert('진료가 삭제되었습니다.');
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || '진료 삭제에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>진료 삭제</h2>

        {error && <div className="error-message">{error}</div>}

        <div className="form-section">
          <p>다음 진료를 삭제하시겠습니까?</p>
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8fafc', borderRadius: '4px' }}>
            <p><strong>환자:</strong> {encounter.patient_name} ({encounter.patient_number})</p>
            <p><strong>진료유형:</strong> {encounter.encounter_type_display}</p>
            <p><strong>진료과:</strong> {encounter.department_display}</p>
            <p><strong>담당의사:</strong> {encounter.attending_doctor_name}</p>
            <p><strong>입원일시:</strong> {new Date(encounter.admission_date).toLocaleString('ko-KR')}</p>
            <p><strong>상태:</strong> {encounter.status_display}</p>
          </div>
          <p style={{ marginTop: '1rem', color: '#ef4444' }}>
            ⚠️ 이 작업은 되돌릴 수 없습니다.
          </p>
        </div>

        <div className="modal-footer">
          <button className="btn" onClick={handleClose} disabled={loading}>
            취소
          </button>
          <button
            className="btn btn-danger"
            onClick={handleDelete}
            disabled={loading}
          >
            {loading ? '삭제 중...' : '삭제'}
          </button>
        </div>
      </div>
    </div>
  );
}
