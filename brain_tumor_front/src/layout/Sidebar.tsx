import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '@/pages/auth/AuthProvider';
import SidebarItem from './SidebarItem';
import '@/assets/style/sidebarStyle.css'

export default function Sidebar() {
  const { menus, isAuthReady } = useAuth();
  const [openGroup, setOpenGroup] = useState<string | null>(null);

  const handleToggle = (menuId: string) => {
    setOpenGroup(prev => (prev === menuId ? null : menuId));
  };

  if (!isAuthReady) return null;

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">

        <ul  className="menu-list">
          {menus.map(menu => (
            <SidebarItem
              key={menu.id}
              menu={menu}
              isOpen={openGroup === menu.code}
              onToggle={()=> handleToggle(menu.code)}
            />
          ))}
        </ul>
      </nav>
    </aside>
  );
}

function MenuItem({ menu }: { menu: any }) {
  if (menu.children?.length) {
    return (
      <div className="menu-group">
        <span className="menu-title">{menu.label}</span>
        {menu.children.map((child: any) => (
          <MenuItem key={child.id} menu={child} />
        ))}
      </div>
    );
  }

  return (
    <NavLink to={menu.path!} className="menu-item">
      {menu.label}
    </NavLink>
  );
}