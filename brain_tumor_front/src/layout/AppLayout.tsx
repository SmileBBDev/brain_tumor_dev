import { Outlet, Navigate } from 'react-router-dom';
import { useState } from 'react';
import type { Role } from '@/types/role';
import Sidebar from './Sidebar';
import AppHeader from './AppHeader';
import { useAuth } from '@/pages/auth/AuthProvider';



export default function AppLayout() {
  const { role } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  if (!role) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className='app-layout'>
      {role && <AppHeader role={role} onToggleSidebar={toggleSidebar} /> }

      <div className='app-body'>      
        {role && isSidebarOpen && <Sidebar role={role}/> }
        <main className='app-content'>
          <Outlet />
        </main>
      </div>

    </div>
    
  );
}
