import type { Encounter } from '@/types/encounter';

type Props = {
  role: string;
  encounters: Encounter[];
  onEdit: (encounter: Encounter) => void;
  onDelete: (encounter: Encounter) => void;
};

export default function EncounterListTable({ role, encounters, onEdit, onDelete }: Props) {
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';
  const canEdit = isDoctor || isSystemManager;

  // Handle undefined encounters
  if (!encounters) {
    return (
      <table className="table encounter-table">
        <thead>
          <tr>
            <th>환자명</th>
            <th>환자번호</th>
            <th>진료유형</th>
            <th>진료과</th>
            <th>담당의사</th>
            <th>입원일시</th>
            <th>퇴원일시</th>
            <th>상태</th>
            <th>주호소</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={10} style={{ textAlign: 'center', padding: '2rem' }}>
              로딩 중...
            </td>
          </tr>
        </tbody>
      </table>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'status-badge status-scheduled';
      case 'in-progress':
        return 'status-badge status-in-progress';
      case 'completed':
        return 'status-badge status-completed';
      case 'cancelled':
        return 'status-badge status-cancelled';
      default:
        return 'status-badge';
    }
  };

  return (
    <table className="table encounter-table">
      <thead>
        <tr>
          <th>환자명</th>
          <th>환자번호</th>
          <th>진료유형</th>
          <th>진료과</th>
          <th>담당의사</th>
          <th>입원일시</th>
          <th>퇴원일시</th>
          <th>상태</th>
          <th>주호소</th>
          <th>작업</th>
        </tr>
      </thead>

      <tbody>
        {encounters.length === 0 ? (
          <tr>
            <td colSpan={10} style={{ textAlign: 'center', padding: '2rem' }}>
              등록된 진료가 없습니다.
            </td>
          </tr>
        ) : (
          encounters.map((e) => (
            <tr key={e.id}>
              <td>{e.patient_name}</td>
              <td>{e.patient_number}</td>
              <td>{e.encounter_type_display}</td>
              <td>{e.department_display}</td>
              <td>{e.attending_doctor_name}</td>
              <td>{formatDateTime(e.admission_date)}</td>
              <td>{e.discharge_date ? formatDateTime(e.discharge_date) : <span style={{ color: '#1976d2', fontWeight: 500 }}>(입원중)</span>}</td>
              <td>
                <span className={getStatusBadgeClass(e.status)}>
                  {e.status_display}
                </span>
              </td>
              <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {e.chief_complaint}
              </td>
              <td>
                <div className="action-buttons">
                  {canEdit && (
                    <>
                      <button
                        className="btn small primary"
                        onClick={() => onEdit(e)}
                      >
                        편집
                      </button>
                      {isSystemManager && (
                        <button
                          className="btn small btn-danger"
                          onClick={() => onDelete(e)}
                        >
                          삭제
                        </button>
                      )}
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
