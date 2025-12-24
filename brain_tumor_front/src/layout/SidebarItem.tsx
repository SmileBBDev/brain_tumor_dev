// import { NavLink, useLocation } from 'react-router-dom';
// import { useEffect, useMemo, useState } from 'react';
// import type { MenuConfig } from '@/config/menuConfig';
// import type { Role } from '@/types/role';

// interface SidebarItemProps {
//   menu: MenuConfig;
//   role: Role;
//   canAccess: (menu: MenuConfig) => boolean;
// }

// export default function SidebarItem({
//   menu,
//   role,
//   canAccess,
// }: SidebarItemProps) {
//   const location = useLocation();

//   /** 접근 불가 or breadcrumb 전용 메뉴는 숨김 */
//   if (!canAccess(menu) || menu.breadcrumbOnly) return null;

//   const label =
//     menu.label[role] ??
//     menu.label.DEFAULT ??
//     menu.id;

//   const isGroup = !menu.path && menu.children?.length;

//   /** 현재 경로가 하위에 포함되면 자동 open */
//   const isActiveGroup = useMemo(() => {
//     if (!menu.children) return false;
//     return menu.children.some(child =>
//       child.path && location.pathname.startsWith(child.path.split('/:')[0])
//     );
//   }, [location.pathname, menu.children]);

//   const [open, setOpen] = useState(isActiveGroup);

//   useEffect(() => {
//     if (isActiveGroup) setOpen(true);
//   }, [isActiveGroup]);

//   return (
//     <li className="menu-item">
//       {isGroup ? (
//         <>
//           {/* Group Header */}
//           <button
//             type="button"
//             className={`menu-group ${open ? 'open' : ''}`}
//             onClick={() => setOpen(prev => !prev)}
//           >
//             <span className="menu-group-left">
//               {menu.icon && (
//                 <i className={`menu-icon fa fa-${menu.icon}`} />
//               )}
//               <span className="menu-label">{label}</span>
//             </span>

//             <i
//               className={`menu-chevron fa fa-chevron-${
//                 open ? 'down' : 'right'
//               }`}
//             />
//           </button>

//           {/* Children */}
//           {open && (
//             <ul className="menu-children">
//               {menu.children!.map(child => (
//                 <SidebarItem
//                   key={child.id}
//                   menu={child}
//                   role={role}
//                   canAccess={canAccess}
//                 />
//               ))}
//             </ul>
//           )}
//         </>
//       ) : (
//         /* Leaf Menu */
//         <NavLink
//           to={menu.path!}
//           className={({ isActive }) =>
//             `menu-link ${isActive ? 'active' : ''}`
//           }
//         >
//           {menu.icon && (
//             <i className={`menu-icon fa fa-${menu.icon}`} />
//           )}
//           <span className="menu-label">{label}</span>
//         </NavLink>
//       )}
//     </li>
//   );
// }
import { NavLink, useLocation } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import type { MenuConfig } from '@/config/menuConfig';
import type { Role } from '@/types/role';

interface SidebarItemProps {
  menu: MenuConfig;
  role: Role;
  canAccess: (menu: MenuConfig) => boolean;
}

export default function SidebarItem({
  menu,
  role,
  canAccess,
}: SidebarItemProps) {
  const location = useLocation();

  /** 접근 불가 or breadcrumb 전용 메뉴는 숨김 */
  if (!canAccess(menu) || menu.breadcrumbOnly) return null;

  const label =
    menu.label?.[role] ??
    menu.label?.DEFAULT ??
    menu.id;

  const isGroup = !menu.path && menu.children?.length;

  /** 현재 경로가 하위에 포함되면 자동 open */
  const isActiveGroup = useMemo(() => {
    if (!menu.children) return false;
    return menu.children.some(child =>
      child.path &&
      location.pathname.startsWith(child.path.split('/:')[0])
    );
  }, [location.pathname, menu.children]);

  const [open, setOpen] = useState(isActiveGroup);

  useEffect(() => {
    if (isActiveGroup) setOpen(true);
  }, [isActiveGroup]);

  return (
    <li className="menu-item">
      {isGroup ? (
        <>
          {/* Group Header */}
          <button
            type="button"
            className={`menu-group ${open ? 'open' : ''}`}
            onClick={() => setOpen(prev => !prev)}
          >
            <span className="menu-group-left">
              {menu.icon && (
                <i className={`menu-icon fa fa-${menu.icon}`} />
              )}
              <span className="menu-label">
                {menu.groupLabel ?? label}
              </span>
            </span>

            <i
              className={`menu-chevron fa fa-chevron-${
                open ? 'down' : 'right'
              }`}
            />
          </button>

          {/* Children */}
          {open && (
            <ul className="menu-children">
              {menu.children!.map(child => (
                <SidebarItem
                  key={child.id}
                  menu={child}
                  role={role}
                  canAccess={canAccess}
                />
              ))}
            </ul>
          )}
        </>
      ) : (
        /* Leaf Menu */
        <NavLink
          to={menu.path!}
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
