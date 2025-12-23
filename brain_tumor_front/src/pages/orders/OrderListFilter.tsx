import type { Role } from '@/types/role';

export default function OrderListFilter({ role }: { role: Role }) {

    return (
         <div className="filters-bar">
          <input placeholder="환자명 / ID 검색" />
        </div>
    );
};