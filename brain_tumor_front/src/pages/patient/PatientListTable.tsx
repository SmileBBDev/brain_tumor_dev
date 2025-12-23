import { useNavigate } from 'react-router-dom';
import type { Role } from '@/types/role';

interface Props {
  role: Role;
}
// role에 따른 테이블 컬럼 매핑 컴포넌트
export default function PatientListTable({ role}: Props) {
  const navigate = useNavigate();
  const isDoctor = role === 'DOCTOR'; 
  const isSystemManager = role === 'SYSTEMMANAGER';

  // 환자 상세 페이지로 이동
  const goDetail = (patientId: string) => {
    navigate(`/patients/${patientId}`);
  };

  // TODO: 환자 더미데이터 - 실제로는 API 호출로 데이터를 받아와야 함
    const patients = [
    { id: 'P001', name: '홍길동', gender: 'M', age: 45, phoneNumber: '010-1234-5678', address: '서울시 강남구', lastVisit: '2024-12-01' },
    { id: 'P002', name: '김영희', gender: 'F', age: 52, phoneNumber: '010-5678-1234', address: '서울시 마포구', lastVisit: '2024-12-02' },
  ];

  return (
    <table className="table patient-table">
      <thead>
        <tr>
          <th>환자ID</th>
          <th>환자명</th>
          <th>성별</th>
          <th>나이</th>
          <th>연락처</th>
          <th>주소</th>
          <th>최근 방문일</th>
          {role !== 'PATIENT' && <th>진료과</th>}
          <th>상태</th>
          {(isDoctor || isSystemManager) && (
          <th>AI 요약 보기</th>
          )}
        </tr>
      </thead>

      <tbody>
        {patients.map(p=>(
          <tr onClick={() => goDetail(p.id)} className="clickable">
          <td>{p.id}</td>
          <td>{p.name}</td>
          <td>{p.gender === 'M' ? '남성' : '여성'}</td>
          <td>{p.age}</td>
          <td>{p.phoneNumber}</td>
          <td>{p.address}</td>
          <td>{p.lastVisit}</td>
          {role !== 'PATIENT' && <td>신경외과</td>}
          <td>진료중</td>
          {(isDoctor || isSystemManager) && (
          <td>
              <button
                className="btn small"
                onClick={e => {
                  e.stopPropagation();
                  navigate(`/patients/${p.id}?tab=ai`);
                }}
              >
                AI 분석
              </button>
          </td>
          )}
        </tr>

      ))}
        
      </tbody>
    </table>
  );
}
