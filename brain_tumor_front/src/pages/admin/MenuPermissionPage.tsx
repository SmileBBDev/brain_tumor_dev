// // // Admin 메뉴 권한 관리 구현 코드
// import { useEffect, useState } from 'react';
// import type { MenuNode } from '@/types/menu';
// import type { Role } from '@/types/adminManager';

// import {
//   fetchRoles,
//   fetchMenuTree,
//   fetchRoleMenus,
//   saveRoleMenus,
// } from '@/services/admin.permission';

// import '@/assets/style/adminMenuControlPageStyle.css';

// export default function MenuPermissionPage() {
//     const [roles, setRoles] = useState<Role[]>([]);
//     const [menuTree, setMenuTree] = useState<MenuNode[]>([]);
//     const [selectedRole, setSelectedRole] = useState<Role | null>(null);

//     const [checkedMenuIds, setCheckedMenuIds] = useState<number[]>([]); // UI
//     const [originLeafMenuIds, setOriginLeafMenuIds] = useState<number[]>([]); // 서버 기준

//     // checkedMenuIds        → UI 체크 상태 (부모 포함)
//     // originLeafMenuIds     → 서버 기준 권한 (leaf only)
//     // getLeafMenuIds()      → 저장 & 변경 여부 판단용

//     /** 초기 로딩 */
//     useEffect(() => {
//     Promise.all([fetchRoles(), fetchMenuTree()]).then(
//         ([roles, menus]) => {
//             setRoles(roles);
//             setMenuTree(menus);
//             if (roles.length > 0) {
//                 setSelectedRole(roles[0]);
//             }

//         }
//     );
//     }, []);

//     /** Role 변경 시 권한 조회 */
//     useEffect(() => {
//         if (!selectedRole) return;

//         fetchRoleMenus(selectedRole.id).then(ids => {
//             console.log('권한 IDs:', ids); // 👈 이거 꼭 찍어봐
//             setCheckedMenuIds(ids);          // UI 초기 체크
//             setOriginLeafMenuIds(ids);       // 서버 기준 leaf

//         });
//     }, [selectedRole]);

  
//     // Role과 무관하게 메뉴 이름 호출 함수
//     const getMenuLabel = (node: MenuNode) =>
//     node.labels?.['DEFAULT'] ??
//     Object.values(node.labels ?? {})[0] ??
//     node.id;

//     // 부모, 자식 메뉴 연결 함수
//     const collectMenuIds = (node: MenuNode): number[] => {
//         const ids = [node.id];
//         if (node.children) {
//             node.children.forEach(c => {
//             ids.push(...collectMenuIds(c));
//             });
//         }
//         return ids;
//     };

//     // 부모 노드 찾기
//     const findParent = (
//         nodes: MenuNode[],
//         childId: number,
//         parent: MenuNode | null = null
//         ): MenuNode | null => {
//         for (const node of nodes) {
//             if (node.id === childId) return parent;
//             if (node.children) {
//             const found = findParent(node.children, childId, node);
//             if (found) return found;
//             }
//         }
//         return null;
//     };

//     const toggleMenu = (node: MenuNode) => {
//         // if (node.breadcrumbOnly) return;

//         setCheckedMenuIds(prev => {
//             const next = new Set(prev);
//             const ids = collectMenuIds(node);
//             const isChecked = next.has(node.id);

//             // 1️⃣ 해제: 자신 + 자식 제거
//             if (isChecked) {
//                 ids.forEach(id => next.delete(id));
//             }else{
//                 ids.forEach(id => next.add(id))
//             }
//             return Array.from(next);
//         });
//     };

//      // indeterminate 계산
//     const isIndeterminate = (node: MenuNode): boolean => {
//         if (!node.children || node.children.length === 0) return false;

//         const childIds = node.children.flatMap(collectMenuIds);
//         const checkedCount = childIds.filter(id =>
//         checkedMenuIds.includes(id)
//         ).length;

//         return (
//         checkedCount > 0 &&
//         checkedCount < childIds.length
//         );
//     };
    
//     const renderMenu = (nodes: MenuNode[], depth = 0) => (
//     <ul>
//         {nodes.map(node => {
//         // const disabled = node.breadcrumbOnly === true;
//         const disabled = false;


//         const checked = checkedMenuIds.includes(node.id);
//         const indeterminate = isIndeterminate(node);

//         return (
//             <li key={node.id} style={{ marginLeft: depth * 16 }}>
//             <label
//                 style={{
//                 opacity: disabled ? 0.4 : 1,
//                 cursor: disabled ? 'not-allowed' : 'pointer',
//                 }}
//             >
//                 <input
//                 type="checkbox"
//                 disabled={disabled}
//                 checked={checked}
//                 ref={el => {
//                     if (el) el.indeterminate = indeterminate;
//                 }}
//                 onChange={() => toggleMenu(node)}
//                 />
//                 {getMenuLabel(node)}
//             </label>

//             {node.children && renderMenu(node.children, depth + 1)}
//             </li>
//         );
//         })}
//     </ul>
//     );

//     // const renderMenu = (nodes: MenuNode[], depth = 0) => (
//     //     <ul>
//     //     {nodes.map(node => {
//     //         const isLeaf = !node.children || node.children.length === 0;
//     //         const disabled = node.breadcrumbOnly === true && isLeaf;
//     //         const checked = checkedMenuIds.includes(node.id);
//     //         const indeterminate = isIndeterminate(node);

//     //         return (
//     //         <li key={node.id} style={{ marginLeft: depth * 16 }}>
//     //             <label style={{
//     //                     opacity: disabled ? 0.4 : 1,
//     //                     cursor: disabled ? 'not-allowed' : 'pointer'
//     //                 }}
//     //             >
//     //             <input
//     //                 type="checkbox"
//     //                 disabled={disabled}
//     //                 checked={checked}
//     //                 ref={el => {
//     //                 if (el) el.indeterminate = indeterminate;
//     //                 }}
//     //                 onChange={() => toggleMenu(node)}
//     //             />
//     //             {getMenuLabel(node)}
//     //             </label>

//     //             {node.children && renderMenu(node.children, depth + 1)}
//     //         </li>
//     //         );
//     //     })}
//     //     </ul>
//     // );

//     // 접근 권한 메뉴 변경 저장 API 호출
//     const save = async () => {
//         if (!selectedRole) return;

//         // 체크된 모든 메뉴 ID 저장 (백엔드에서 자식 메뉴 자동 포함)
//         await saveRoleMenus(selectedRole.id, checkedMenuIds);
//         // 서버 기준 갱신
//         setOriginLeafMenuIds([...checkedMenuIds]);

//         alert('저장 완료');
//     };

//     const normalize = (arr: number[]) =>
//         [...arr].sort((a, b) => a - b);

//     const isChanged =
//     JSON.stringify(normalize(checkedMenuIds)) !==
//     JSON.stringify(normalize(originLeafMenuIds));

//     return (
//         <section className="admin-layout">
//             {/* 좌측 Role 리스트 */}
//             <aside className="role-panel">
//             <h3>Role</h3>
//             <ul className="role-list">
//                 {roles.map(role => (
//                 <li
//                     key={role.id}
//                     className={selectedRole?.id === role.id ? 'active' : ''}
//                     onClick={() => setSelectedRole(role)}
//                 >
//                     {role.name}
//                 </li>
//                 ))}
//             </ul>
//             </aside>

//             {/* 우측 상세 */}
//             <main className="permission-panel">
//             <h2>Role : {selectedRole?.name}</h2>

//             {/* 접근 가능 화면 */}
//             <section className="card">
//                 <h4>접근 가능 화면</h4>
//                 <div className="menu-tree">
//                 {renderMenu(menuTree)}
//                 </div>

//                 <div className="actions">
//                 <button disabled={!isChanged} onClick={save}>
//                     저장
//                 </button>
//                 </div>
//             </section>

//             {/* 변경 이력 */}
//             <section className="card">
//                 <h4>접근 권한 변경 이력</h4>
//                 <table className="history-table">
//                 <thead>
//                     <tr>
//                     <th>변경일시</th>
//                     <th>변경자</th>
//                     <th>변경 Role</th>
//                     <th>변경내용</th>
//                     </tr>
//                 </thead>
//                 <tbody>
//                     <tr>
//                     <td>2025-12-02</td>
//                     <td>시스템 관리자</td>
//                     <td>Doctor</td>
//                     <td>환자 관리 메뉴 접근 권한 부여</td>
//                     </tr>
//                     <tr>
//                     <td>2025-12-01</td>
//                     <td>시스템 관리자</td>
//                     <td>Nurse</td>
//                     <td>검사 관리 메뉴 접근 권한 부여</td>
//                     </tr>
//                 </tbody>
//                 </table>
//             </section>
//             </main>
//         </section>
//     );
// //     return (
// //     <section className="page-content grid">
// //       <div className="card">
// //         <h3>Role</h3>
// //         <select
// //           value={selectedRole?.code}
// //           onChange={e =>
// //             setSelectedRole(
// //               roles.find(r => r.code === e.target.value) ?? null
// //             )
// //           }
// //         >
// //           {roles.map(role => (
// //             <option key={role.code} value={role.code}>
// //               {role.name}
// //             </option>
// //           ))}
// //         </select>
// //       </div>

// //       <div className="card">
// //         <h3>메뉴 권한</h3>
// //         {renderMenu(menuTree)}

// //         <button disabled={!isChanged} onClick={save}>
// //           저장
// //         </button>
// //       </div>
// //     </section>
// //   );

// }


// Admin 메뉴 권한 관리 구현 코드
import { useEffect, useState } from 'react';
import type { MenuNode } from '@/types/menu';
import type { Role } from '@/types/adminManager';

import {
  fetchRoles,
  fetchMenuTree,
  fetchRoleMenus,
  saveRoleMenus,
} from '@/services/admin.permission';

import '@/assets/style/adminMenuControlPageStyle.css';

export default function MenuPermissionPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [menuTree, setMenuTree] = useState<MenuNode[]>([]);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  const [checkedMenuIds, setCheckedMenuIds] = useState<number[]>([]);
  const [originLeafMenuIds, setOriginLeafMenuIds] = useState<number[]>([]);

  /* =========================
     초기 로딩
  ========================= */
  useEffect(() => {
    Promise.all([fetchRoles(), fetchMenuTree()]).then(
      ([roles, menus]) => {
        setRoles(roles);
        setMenuTree(menus);
        if (roles.length > 0) {
          setSelectedRole(roles[0]);
        }
      }
    );
  }, []);

  /* =========================
     Role 변경 시 권한 조회
  ========================= */
  useEffect(() => {
    if (!selectedRole) return;

    fetchRoleMenus(selectedRole.id).then(ids => {
      setCheckedMenuIds(ids);
      setOriginLeafMenuIds(ids);
    });
  }, [selectedRole]);

  /* =========================
     공통 유틸
  ========================= */
  const getMenuLabel = (node: MenuNode) =>
    node.labels?.['DEFAULT'] ??
    Object.values(node.labels ?? {})[0] ??
    node.id;

  const collectMenuIds = (node: MenuNode): number[] => {
    const ids = [node.id];
    if (node.children) {
      node.children.forEach(c => {
        ids.push(...collectMenuIds(c));
      });
    }
    return ids;
  };

  /* =========================
     체크 / 전체선택 로직
  ========================= */
  const toggleMenu = (node: MenuNode, force?: boolean) => {
    setCheckedMenuIds(prev => {
      const next = new Set(prev);
      const ids = collectMenuIds(node);

      const shouldCheck =
        typeof force === 'boolean'
          ? force
          : !next.has(node.id);

      if (shouldCheck) {
        ids.forEach(id => next.add(id));
      } else {
        ids.forEach(id => next.delete(id));
      }

      return Array.from(next);
    });
  };

  const isIndeterminate = (node: MenuNode): boolean => {
    if (!node.children || node.children.length === 0) return false;

    const childIds = node.children.flatMap(collectMenuIds);
    const checkedCount = childIds.filter(id =>
      checkedMenuIds.includes(id)
    ).length;

    return checkedCount > 0 && checkedCount < childIds.length;
  };

  /* =========================
     하위 메뉴 렌더링
  ========================= */
  const renderMenu = (nodes: MenuNode[], depth = 0) => (
    <ul>
      {nodes.map(node => {
        const checked = checkedMenuIds.includes(node.id);
        const indeterminate = isIndeterminate(node);

        return (
          <li key={node.id} style={{ marginLeft: depth * 16 }}>
            <label>
              <input
                type="checkbox"
                checked={checked}
                ref={el => {
                  if (el) el.indeterminate = indeterminate;
                }}
                onChange={() => toggleMenu(node)}
              />
              {getMenuLabel(node)}
            </label>

            {node.children && renderMenu(node.children, depth + 1)}
          </li>
        );
      })}
    </ul>
  );

  /* =========================
     카테고리 카드 렌더링
  ========================= */
  const renderCategory = (node: MenuNode) => {
    const checked = checkedMenuIds.includes(node.id);
    const indeterminate = isIndeterminate(node);

    return (
      <section key={node.id} className="menu-category">
        <div className="menu-category-header">
          <label>
            <input
              type="checkbox"
              checked={checked}
              ref={el => {
                if (el) el.indeterminate = indeterminate;
              }}
              onChange={() => toggleMenu(node)}
            />
            <strong>{getMenuLabel(node)}</strong>
          </label>

          <div className="menu-actions">
            <button onClick={() => toggleMenu(node, true)}>
              전체 선택
            </button>
            <button onClick={() => toggleMenu(node, false)}>
              전체 해제
            </button>
          </div>
        </div>

        <div className="menu-category-body">
          {node.children && renderMenu(node.children, 1)}
        </div>
      </section>
    );
  };

  /* =========================
     저장 로직
  ========================= */
  const save = async () => {
    if (!selectedRole) return;

    await saveRoleMenus(selectedRole.id, checkedMenuIds);
    setOriginLeafMenuIds([...checkedMenuIds]);
    alert('저장 완료');
  };

  const normalize = (arr: number[]) =>
    [...arr].sort((a, b) => a - b);

  const isChanged =
    JSON.stringify(normalize(checkedMenuIds)) !==
    JSON.stringify(normalize(originLeafMenuIds));

  /* =========================
     Render
  ========================= */
  return (
    <section className="admin-layout">
      {/* 좌측 Role 리스트 */}
      <aside className="role-panel">
        <h3>Role</h3>
        <ul className="role-list">
          {roles.map(role => (
            <li
              key={role.id}
              className={selectedRole?.id === role.id ? 'active' : ''}
              onClick={() => setSelectedRole(role)}
            >
              {role.name}
            </li>
          ))}
        </ul>
      </aside>

      {/* 우측 상세 */}
      <main className="permission-panel">
        <h2>Role : {selectedRole?.name}</h2>

        <section className="card">
          <h4>접근 가능 화면</h4>

          <div className="menu-tree">
            {menuTree.map(root => renderCategory(root))}
          </div>

          <div className="actions">
            <button disabled={!isChanged} onClick={save}>
              저장
            </button>
          </div>
        </section>

        <section className="card">
          <h4>접근 권한 변경 이력</h4>
          <table className="history-table">
            <thead>
              <tr>
                <th>변경일시</th>
                <th>변경자</th>
                <th>변경 Role</th>
                <th>변경내용</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2025-12-02</td>
                <td>시스템 관리자</td>
                <td>Doctor</td>
                <td>환자 관리 메뉴 접근 권한 부여</td>
              </tr>
              <tr>
                <td>2025-12-01</td>
                <td>시스템 관리자</td>
                <td>Nurse</td>
                <td>검사 관리 메뉴 접근 권한 부여</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </section>
  );
}
