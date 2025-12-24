import { Outlet } from 'react-router-dom';

export default function OrdersLayout() {
  return (
    <div className="page orders">
      {/* 
        여기에 나중에:
        - Orders 탭
        - Breadcrumb
        - 상태 필터
        같은 공통 UI 들어가면 됨
      */}
      <Outlet />
    </div>
  );
}
