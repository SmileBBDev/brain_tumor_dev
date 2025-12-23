import type { Role } from '@/types/role';
import OrderListHeader from './OrderListHeader';
import OrderListFilter from './OrderListFilter';
import OrderListTable from './OrderListTable';

export default function OrderListPage() {
  const role = localStorage.getItem('role') as Role | null;
  if (!role) return <div>접근 권한 정보 없음</div>;

  return (
    <div className="page">
      <OrderListHeader role={role} />
      <OrderListFilter role={role} />
      <OrderListTable role={role} />
    </div>
  );
}
