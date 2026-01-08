import { NavLink } from 'react-router-dom';
import type { MenuNode } from '@/types/menu';
import { useAuth } from '@/pages/auth/AuthProvider';

interface SidebarItemProps {
  menu: MenuNode;
  isOpen: boolean;
  onToggle: () => void;
}

export default function SidebarItem({
  menu,
  isOpen,
  onToggle,
}: SidebarItemProps) {
  const { role } = useAuth();
  const roleKey = role ?? 'DEFAULT';
  const label =
    menu.labels?.[roleKey] ||
    menu.labels?.['DEFAULT'] ||
    menu.code;
  const isGroup = !menu.path && menu.children && menu.children.length > 0;

  return (
    <li className="menu-item">
      {isGroup ? (
        <>
          {/* Group Header */}
          <button
            type="button"
            className={`menu-group ${isOpen ? 'open' : ''}`}
            onClick={onToggle}
          >
            <span className="menu-group-left">
              {menu.icon && (
                <i className={`menu-icon fa fa-${menu.icon}`} />
              )}
              <span className="menu-label">{label}</span>
            </span>

            <i
              className={`menu-chevron fa fa-chevron-${
                isOpen ? 'down' : 'right'
              }`}
            />
          </button>

          {/* Children */}
          {isOpen && (
            <ul className="menu-children">
              {menu.children!.map(child => (
                <SidebarItem
                  key={child.id}
                  menu={child}
                  isOpen={false}
                  onToggle={() => {}}
                />
              ))}
            </ul>
          )}
        </>
      ) : (
        /* Leaf Menu */
        <NavLink
          to={menu.path!}
          end
          className={({ isActive }) =>
            `menu-link ${isActive ? 'active' : ''}`
          }
        >
          {menu.icon && (
            <i className={`menu-icon fa fa-${menu.icon}`} />
          )}
          <span className="menu-label">{label}</span>
        </NavLink>
      )}
    </li>
  );
}