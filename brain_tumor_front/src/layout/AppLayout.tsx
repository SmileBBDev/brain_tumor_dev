import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout() {
  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <main style={{ padding: 16, flex: 1 }}>
        <Outlet />
      </main>
    </div>
  );
}
