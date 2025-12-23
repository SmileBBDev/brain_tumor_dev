import { Outlet } from 'react-router-dom';
import type { Role } from '@/types/role';
import Sidebar from './Sidebar';
import AppHeader from './AppHeader';


export default function AppLayout() {
  const role = localStorage.getItem('role') as Role;

  if(!role){ 
   return <div>접근 권한 정보 없음</div>; 
  }

  return (
    <div className='app-layout'>
      <Sidebar role={role}/>

      <div className='app-body'>      
        <AppHeader role={role} />
        <main className='app-content'>
          <Outlet />
        </main>
      </div>

    </div>
    
  );
}
