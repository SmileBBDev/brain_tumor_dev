import { NavLink } from 'react-router-dom';
import type { Role } from '@/types/role';

interface Props {
  role: Role;
}

export default function PatientDetailTabs({ role }: Props) {
  const isSystemManager = role === 'SYSTEMMANAGER';
  const tabs = [
    { key: 'summary', label: '요약', roles: ['DOCTOR', 'NURSE', 'PATIENT'] },
    { key: 'imaging', label: '영상', roles: ['DOCTOR', 'NURSE', 'RIS'] },
    { key: 'lab', label: '검사 결과', roles: ['DOCTOR', 'NURSE', 'LIS'] },
    { key: 'ai', label: 'AI 분석', roles: ['DOCTOR'] },
  ];

  return (
    <div className="tabs">
      {tabs
        .filter(tab => isSystemManager ||tab.roles.includes(role))
        .map(tab => (
          <NavLink
            key={tab.key}
            to={`?tab=${tab.key}`}
            className={({ isActive }) =>
              isActive ? 'tab active' : 'tab'
            }
          >
            {tab.label}
          </NavLink>
        ))}
    </div>
  );
}
