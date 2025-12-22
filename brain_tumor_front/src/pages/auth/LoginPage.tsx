// 로그인 화면
import { useState } from 'react';
import { login, fetchMe, fetchMenu } from './auth.api';
import { useNavigate } from 'react-router-dom';

import type { Role } from '@/types/role';
import type { MenuId } from '@/types/menu';

export default function LoginPage(){
    const [id, setId] = useState('');
    const [pw, setPw] = useState('');    
    const navigate = useNavigate();

    const handleLogin = async () => {
        // 임시 로그인 처리
        // 🔥 1. 임시 토큰
        localStorage.setItem('accessToken', 'mock-token');

        // 🔥 2. role 지정 (테스트하고 싶은 거로)
        const getTestRole = (): Role => {
            //return 'ADMIN';
            // return 'DOCTOR';
             return 'NURSE';
            // return 'RIS';
            // return 'LIS';
        };

        let role: Role = getTestRole();

        localStorage.setItem('role', role);

        // 🔥 3. 해당 role에 맞는 메뉴
        let menus: MenuId[] = [];

        switch (role) {
            case 'ADMIN':
                menus = [
                    'ADMIN_USER',
                    'ADMIN_MENU_PERMISSION',
                    'ADMIN_AUDIT_LOG',
                    'ADMIN_SYSTEM_MONITOR',
                ];
                break;
            case 'DOCTOR':
                menus = [
                    'DASHBOARD',
                    'PATIENT_LIST',
                    'PATIENT_DETAIL',
                    'PATIENT_SUMMARY',
                    'PATIENT_IMAGING',
                    'PATIENT_LAB_RESULT',
                    'PATIENT_AI_SUMMARY',
                    'ORDER_LIST',
                    'ORDER_CREATE',
                    'IMAGE_VIEWER',
                    'AI_SUMMARY',
                ];
                break;

            case 'NURSE':
                menus = [
                    'DASHBOARD',
                    'PATIENT_LIST',
                    'PATIENT_DETAIL',
                    'PATIENT_SUMMARY',
                    'PATIENT_IMAGING',
                    'PATIENT_LAB_RESULT',
                    'ORDER_LIST',
                    'IMAGE_VIEWER',
                ];
                break;

            case 'RIS':
                menus = [
                    'IMAGE_VIEWER',
                    'RIS_WORKLIST',
                    'RIS_READING',
                ];
                break;

            case 'LIS':
                menus = [
                    'LAB_RESULT_UPLOAD',
                    'LAB_RESULT_VIEW',
                ];
                break;
        }

        localStorage.setItem('menus', JSON.stringify(menus));

    // 🔁 4. 홈 이동 → HomeRedirect가 Role_Home 처리
        navigate('/');



        // api 호출해서 로그인 처리 기능
        // try{
        //     const res = await login(id, pw);
        //     localStorage.setItem('accessToken', res.data.token);

        //     const me = await fetchMe();
        //     const menu = await fetchMenu();

        //     localStorage.setItem('role', me.data.role);
        //     localStorage.setItem('menu', JSON.stringify(menu.data.menus));

        //     navigate('/patients');

        /**
         * 
         * // 로그인 성공 후
            localStorage.setItem('role', role);
            localStorage.setItem(
            'menus',
            JSON.stringify(
                JSON.parse(localStorage.getItem(`menus:${role}`) || '[]')
            )
            );

         */




        // }catch(error){
        //     alert("로그인 실패")
        //     console.error(error);
        // }
        
    }

    return(
        <div>
             <input placeholder="ID" onChange={(e) => setId(e.target.value)} />
            <input type="password" placeholder="PW" onChange={(e) => setPw(e.target.value)} />
            <button onClick={handleLogin}>로그인</button>

        </div>
    )
}