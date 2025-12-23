import type { Role } from '@/types/role';

// role에 따른 header 제목 매핑 컴포넌트
const TITLE_BY_ROLE: Partial<Record<Role, string>> = {
  SYSTEMMANAGER: '오더 관리',
  DOCTOR: '오더 목록',
  RIS: '오더 목록',
};

export default function OrderListHeader({ role }: { role: Role }) {
  return (
    <header className="page-header">
      <h2>{TITLE_BY_ROLE[role]}</h2>
    </header>
  );
}
