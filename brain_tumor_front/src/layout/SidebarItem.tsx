import { NavLink } from 'react-router-dom';
import type { MenuNode } from '@/pages/auth/AuthProvider';

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
              <span className="menu-label">{menu.label}</span>
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
          className={({ isActive }) =>
            `menu-link ${isActive ? 'active' : ''}`
          }
        >
          <span className="menu-label">{menu.label}</span>
        </NavLink>
      )}
    </li>
  );
}

// import { NavLink } from 'react-router-dom';
// import type{ MenuNode } from '@/pages/auth/AuthProvider';
// import type { MenuConfig } from '@/config/menuConfig';
// import type { Role } from '@/types/role';

// interface SidebarItemProps {
//   // menu: MenuConfig;
//   menu: MenuNode;
//   // role: Role;
//   // canAccess: (menu: MenuConfig) => boolean;
//   isOpen :  boolean;
//   onToggle : () => void;
// }

// export default function SidebarItem({
//   menu,
//   // role,
//   // canAccess,
//   isOpen,
//   onToggle,
// }: SidebarItemProps) {

//   /** 접근 불가 or breadcrumb 전용 메뉴는 숨김 */
//   if (!canAccess(menu) || menu.breadcrumbOnly) return null;

//   const label =
//     menu.label?.[role] ??
//     menu.label?.DEFAULT ??
//     menu.id;

//   const isGroup = !menu.path && menu.children?.length;

//   return (
//     <li className="menu-item">
//       {isGroup ? (
//         <>
//           {/* Group Header */}
//           <button
//             type="button"
//             className={`menu-group ${isOpen ? 'open' : ''}`}
//             // onClick={() => setOpen(prev => !prev)}
//             onClick={onToggle}
//           >
//             <span className="menu-group-left">
//               {menu.icon && (
//                 <i className={`menu-icon fa fa-${menu.icon}`} />
//               )}
//               <span className="menu-label">
//                 {menu.groupLabel ?? label}
//               </span>
//             </span>

//             <i
//               className={`menu-chevron fa fa-chevron-${
//                 isOpen ? 'down' : 'right'
//               }`}
//             />
//           </button>

//           {/* Children */}
//           {isOpen && (
//             <ul className="menu-children">
//               {menu.children!.map(child => (
//                 <SidebarItem
//                   key={child.id}
//                   menu={child}
//                   // role={role}
//                   // canAccess={canAccess}
//                   isOpen = {false} // 자식은 단일 그룹 열림 관리 없음(현재는)
//                   onToggle={()=>{}} // 자식은 토글 없음(현재는)
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
