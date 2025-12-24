import type { Role } from '@/types/role';

import DoctorDashboard from '@/pages/dashboard/doctor/DoctorDashboard';
import NurseDashboard from '@/pages/dashboard/nurse/NurseDashboard';
import LISDashboard from '@/pages/dashboard/lis/LISDashboard';
import RISDashboard from '@/pages/dashboard/ris/RISDashboard';
import CommingSoon from '@/pages/common/CommingSoon';
import SystemManagerDashboard from './systemManager/SystemManagerDashboard';


interface Props {
  role: Role;
}

export default function DashboardRouter({ role }: Props) {
  switch (role) {
    case 'DOCTOR':
      return <DoctorDashboard />;

    case 'NURSE':
      return <NurseDashboard />;

    case 'LIS':
      return <LISDashboard />;

    case 'RIS':
      return <RISDashboard />;

    case 'SYSTEMMANAGER':
      return <SystemManagerDashboard />;
    case 'ADMIN':
        return <CommingSoon />;

    default:
      return <div>대시보드를 찾을 수 없습니다.</div>;
  }
}
