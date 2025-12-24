import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { MENU_CONFIG } from '@/config/menuConfig';
import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';
import { MENU_LABEL_BY_ROLE } from '@/config/menuLabelByRole';
import type{ MenuConfig } from '@/config/menuConfig';
import SidebarItem from '@/layout/SidebarItem';
import '@/assets/style/sidebarStyle.css'

interface Props {
  role: Role;
}
export default function Sidebar( { role } : Props) {
  const menus: MenuId[] = JSON.parse(
    localStorage.getItem('menus') || '[]'
  );

  const isSystemManager = role === 'SYSTEMMANAGER';

  /** 권한 체크 */
  const hasMenu = (menuId: MenuId) => {
    return menus.includes(menuId);
  };

  const canAccess = (menu: MenuConfig): boolean => {
    if (isSystemManager) return true;

    // leaf
    if (menu.path) {
      // breadcrumb-only 메뉴는 sidebar에 안 나옴
      if (menu.breadcrumbOnly) return false;
      return menu.roles.includes(role) && hasMenu(menu.id);
    }

    // group → children 중 하나라도 접근 가능하면 노출
    return (
      menu.children?.some(child => canAccess(child)) ?? false
    );
  };

    
  /** 메뉴 라벨 결정 */
  const getMenuLabel = (menuId: MenuId) => {
    return (
      MENU_LABEL_BY_ROLE[menuId]?.[role] ??
      MENU_CONFIG.find(m => m.id === menuId)?.label?.[role] ??
      MENU_CONFIG.find(m => m.id === menuId)?.label?.DEFAULT ??
      menuId
    );
  };

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <ul className="menu-list">
          {MENU_CONFIG.map(menu => (
            <SidebarItem
              key={menu.id}
              menu={menu}
              role={role}
              canAccess={canAccess}
            />
          ))}
        </ul>

        {/* <ul className="menu-list">
          {MENU_CONFIG
            .filter(menu => 
              isSystemManager || menu.roles.includes(role) // role 필터링
            ) 
            .filter(menu => isSystemManager ||hasMenu(menu.id)) // 권한 체크
            .map(menu => (
              <li key={menu.id} className="menu-item">
                <NavLink to={menu.path ?? '#'} end className={({ isActive }) =>
                  `menu-link ${isActive ? 'active' : ''}`
                }>
                  {menu.icon && <i className={`menu-icon fa fa-${menu.icon}`} />}
                  <span className="menu-label">{getMenuLabel(menu.id)}</span>
                </NavLink>
              </li>
            ))}
        </ul> */}
      </nav>
    </aside>
  );
}