// // Admin 메뉴 권한 관리 구현 코드
import { useEffect, useState } from 'react';
import type { MenuNode } from '@/types/menu';
import type { Role } from '@/types/adminManager';

import {
  fetchRoles,
  fetchMenuTree,
  fetchRoleMenus,
  saveRoleMenus,
} from '@/services/admin.permission';

export default function MenuPermissionPage() {
    const [roles, setRoles] = useState<Role[]>([]);
    const [menuTree, setMenuTree] = useState<MenuNode[]>([]);
    const [selectedRole, setSelectedRole] = useState<Role | null>(null);

    const [checkedMenuIds, setCheckedMenuIds] = useState<number[]>([]);
    const [originMenuIds, setOriginMenuIds] = useState<number[]>([]);

    /** 초기 로딩 */
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

    /** Role 변경 시 권한 조회 */
    useEffect(() => {
    if (!selectedRole) return;

    fetchRoleMenus(selectedRole.code).then(ids => {
        setCheckedMenuIds(ids);
        setOriginMenuIds(ids);
    });
    }, [selectedRole]);

  
    // Role과 무관하게 메뉴 이름 호출 함수
    const getMenuLabel = (node: MenuNode) =>
    node.labels?.['DEFAULT'] ??
    Object.values(node.labels ?? {})[0] ??
    node.id;

    // 부모, 자식 메뉴 연결 함수
    const collectMenuIds = (node: MenuNode): number[] => {
        const ids = [node.id];
        if (node.children) {
            node.children.forEach(c => {
            ids.push(...collectMenuIds(c));
            });
        }
        return ids;
    };

    const toggleMenu = (node: MenuNode) => {
        const ids = collectMenuIds(node);

        setCheckedMenuIds(prev =>
            prev.some(id => ids.includes(id))
            ? prev.filter(id => !ids.includes(id))
            : [...prev, ...ids]
        );
    };


    const renderMenu = (nodes: MenuNode[], depth = 0) => (
        <ul>
            {nodes.map(node => {
            const disabled = node.breadcrumbOnly;

            return (
                <li key={node.id} style={{ marginLeft: depth * 16 }}>
                <label style={{ opacity: disabled ? 0.5 : 1 }}>
                    <input
                    type="checkbox"
                    disabled={disabled}
                    checked={checkedMenuIds.includes(node.id)}
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


    // 접근 권한 메뉴 변경 저장 API 호출
    const save = async () => {
        if (!selectedRole) return;

        await saveRoleMenus(
            selectedRole.code,
            checkedMenuIds,
        );

        setOriginMenuIds(checkedMenuIds);
        alert('저장 완료');
    };

    const isChanged =
    JSON.stringify(checkedMenuIds) !== JSON.stringify(originMenuIds);

    return (
    <section className="page-content grid">
        <div className="card">
        <h3>Role</h3>
        <select
            value={selectedRole?.code}
            onChange={e =>
            setSelectedRole(
                roles.find(r => r.code === e.target.value) ?? null
            )
            }
        >
            {roles.map(role => (
            <option key={role.code} value={role.code}>
                {role.name}
            </option>
            ))}
        </select>
        </div>

        <div className="card">
        <h3>메뉴 권한</h3>
        {renderMenu(menuTree)}

        <button disabled={!isChanged} onClick={save}>
            저장
        </button>
        </div>
    </section>
    );
}
