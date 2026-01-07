import { useNavigate } from 'react-router-dom';
import type { Patient } from '@/types/patient';

type Props = {
  role: string;
  patients: Patient[];
  onEdit: (patient: Patient) => void;
  onDelete: (patient: Patient) => void;
};

// role에 따른 테이블 컬럼 매핑 컴포넌트
export default function PatientListTable( {role, patients, onEdit, onDelete} : Props ) {
  const navigate = useNavigate();
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';
  const canEdit = role === 'DOCTOR' || role === 'NURSE' || isSystemManager;

  const getGenderDisplay = (gender: string) => {
    const genderMap: Record<string, string> = {
      'M': '남성',
      'F': '여성',
      'O': '기타',
    };
    return genderMap[gender] || gender;
  };

  const getStatusDisplay = (status: string) => {
    const statusMap: Record<string, string> = {
      'active': '활성',
      'inactive': '비활성',
      'deceased': '사망',
    };
    return statusMap[status] || status;
  };

  return (
    <table className="table patient-table">
      <thead>
        <tr>
          <th>환자번호</th>
          <th>환자명</th>
          <th>성별</th>
          <th>나이</th>
          <th>연락처</th>
          <th>혈액형</th>
          <th>상태</th>
          <th>등록일</th>
          <th>작업</th>
        </tr>
      </thead>

      <tbody>
        {patients.length === 0 ? (
          <tr>
            <td colSpan={9} style={{ textAlign: 'center', padding: '2rem' }}>
              등록된 환자가 없습니다.
            </td>
          </tr>
        ) : (
          patients.map(p=>(
            <tr key={p.id}>
              <td>{p.patient_number}</td>
              <td>{p.name}</td>
              <td>{getGenderDisplay(p.gender)}</td>
              <td>{p.age}세</td>
              <td>{p.phone}</td>
              <td>{p.blood_type || '-'}</td>
              <td>{getStatusDisplay(p.status)}</td>
              <td>{new Date(p.created_at).toLocaleDateString('ko-KR')}</td>
              <td>
                <div className="action-buttons">
                  <button
                    className="btn small"
                    onClick={() => navigate(`/patients/${p.id}`)}
                  >
                    상세
                  </button>
                  {canEdit && (
                    <>
                      <button
                        className="btn small primary"
                        onClick={() => onEdit(p)}
                      >
                        편집
                      </button>
                      <button
                        className="btn small btn-danger"
                        onClick={() => onDelete(p)}
                      >
                        삭제
                      </button>
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
