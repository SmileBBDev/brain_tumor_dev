import { NavLink } from 'react-router-dom';
import { MENU_CONFIG } from '@/config/menuConfig';
import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';
import { MENU_LABEL_BY_ROLE } from '@/config/menuLabelByRole';

export default function Sidebar() {
  const menus: MenuId[] = JSON.parse(
    localStorage.getItem('menus') || '[]'
  );
  const role = localStorage.getItem('role') as Role;

  /** 권한 체크 */
  const hasMenu = (menuId: MenuId) => {
    return menus.includes(menuId);
  };

  /** 메뉴 라벨 결정 */
  const getMenuLabel = (menuId: MenuId) => {
    return (
      MENU_LABEL_BY_ROLE[menuId]?.[role] ??
      MENU_CONFIG.find(m => m.id === menuId)?.label?.[role] ??
      menuId
    );
  };

  return (
    <aside className="sidebar">
      <ul>
        {MENU_CONFIG
          .filter(menu => menu.roles.includes(role)) // role 필터링
          .filter(menu => hasMenu(menu.id)) // 권한 체크
          .map(menu => (
            <li key={menu.id}>
              <NavLink to={menu.path ?? '#'}>
                {menu.icon && <i className={`icon-${menu.icon}`} />}
                <span>{getMenuLabel(menu.id)}</span>
              </NavLink>
            </li>
          ))}
      </ul>
    </aside>
  );
}
