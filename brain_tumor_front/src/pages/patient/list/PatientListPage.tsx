import type { Role } from '@/types/role';
import DoctorPatientList from '../../doctor/patients/DoctorPatientList';
import NursePatientList from '../../nurse/patients/NursePatientList';
import MyRecordList from './MyRecordList';

export default function PatientListPage() {
  const role = localStorage.getItem('role') as Role | null;

  if(!role){
    return <div>접근 권한 정보 없음</div>;
  }

  const titleByRole: Record<Role, string> = {
    DOCTOR: '환자 목록',
    NURSE: '환자 관리',
    PATIENT: '내 진료 기록',
    ADMIN: '환자 관리',
    RIS: '환자 목록',
    LIS: '환자 목록',
  };

  <h1>{titleByRole[role]}</h1>

  switch (role) {
    case 'DOCTOR':
      return <DoctorPatientList />;
    case 'NURSE':
      return <NursePatientList />;
    case 'PATIENT':
      return <MyRecordList />;
    default:
      return <div>접근 권한 정보 없음</div>;
  }
}