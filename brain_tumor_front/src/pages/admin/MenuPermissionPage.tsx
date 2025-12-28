// Admin 메뉴 권한 관리 구현 코드
import { useEffect, useState } from 'react';
import { MENU_CONFIG } from '@/config/menuConfig';
import type { Role } from '@/types/role';
import type { MenuId } from '@/types/menu';
import { useAuth } from '@/pages/auth/AuthProvider';

const ROLES : Role[] = ['ADMIN','DOCTOR','NURSE','LIS', 'RIS', 'PATIENT'];

function updateMenus(checkedMenus: MenuId[]) {
    throw new Error('Function not implemented.');
}

export default function MenuPermissionPage(){
    const { role: currentRole, setMenus } = useAuth();
    const [selectedRole, setSelectedRole] = useState<Role>('ADMIN');
    const [checkedMenus, setCheckedMenus] = useState<MenuId[]>([]);
    const [originMenus, setOriginMenus] = useState<MenuId[]>([]);

    /* Role 변경 시 권한 로딩 */
    useEffect(() => {
        const stored = JSON.parse(
            localStorage.getItem(`menus:${selectedRole}`) || '[]'
        );
        setCheckedMenus(stored);
        setOriginMenus(stored);
    }, [selectedRole]);

    /* 메뉴 체크 상태 변경시 발생 이벤트 */
    const toggleMenu = (menuId : MenuId) => {
        setCheckedMenus(prev => 
            prev.includes(menuId) 
            ? prev.filter(id => id !== menuId)
            : [...prev, menuId]
        );
    };

    /* 메뉴 권한 변경 저장 */
    const savePermissions = () =>{
        // localStorage.setItem(
        //     `menus:${selectedRole}`,
        //     JSON.stringify(checkedMenus)
        // );

        // 현재 로그인한 Role인 경우 즉시 반영
        if(currentRole === selectedRole){
            setMenus(checkedMenus); // 메뉴 변경 상태를 반영
            localStorage.setItem(
                'menus',
                JSON.stringify(checkedMenus) // 메뉴 저장
            );
        }

        setOriginMenus(checkedMenus);
        // sweetAlert로 변경
        alert('접근 권한이 변경되었습니다.');
    };

    const isChanged = JSON.stringify(checkedMenus) !== JSON.stringify(originMenus);

    return (
        <div>
            <h2>메뉴 권한 관리</h2>

            {/* Role 선택 */}
            <select 
                value={selectedRole}
                onChange = {e => setSelectedRole(e.target.value as Role)}
            >
                {ROLES.map(role => (
                    <option key={role} value={role}>{role}</option>
                ))}
            </select>

            {/* 메뉴 리스트 */}
            <ul>
                {MENU_CONFIG.map(menu => (
                    <li key = {menu.id}>
                        <label>
                            <input type = "checkbox"
                                checked = {checkedMenus.includes(menu.id)}
                                onChange ={()=> toggleMenu(menu.id)}
                            />
                            {menu.id}
                        </label>
                    </li>
                ))}
            </ul>

            {/* 저장 버튼 */}
            <div>
                <button onClick={savePermissions} disabled={!isChanged}>저장</button>
            </div>
        </div>
    );

}