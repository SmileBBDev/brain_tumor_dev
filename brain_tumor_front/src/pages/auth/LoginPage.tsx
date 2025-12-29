// 로그인 화면
/**
 * 로그인 처리 플로우
 * [LoginPage]
    ↓
    POST /api/auth/login/
    ↓
    accessToken / refreshToken 발급
    ↓
    GET /api/auth/me
    ↓
    GET /api/menus
    ↓
    AuthProvider 상태 갱신
    ↓
    Sidebar 자동 갱신

 */
import { useState } from 'react';
import { login, fetchMe, fetchMenu } from './auth.api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/pages/auth/AuthProvider';

import '@/assets/style/login.css';
import { api } from '@/services/api';

export default function LoginPage(){
    const [id, setId] = useState('');
    const [pw, setPw] = useState('');    
    const navigate = useNavigate();

    const { setAuth } = useAuth();

    const handleLogin = async () => {
        //api 호출해서 로그인 처리 기능
        try{
            /** 로그인 API 호출 */
            const res = await login(id, pw);
            // 로그인 성공
            localStorage.setItem('accessToken', res.data.access); // access 토큰 저장
            localStorage.setItem('refreshToken', res.data.refresh); // refresh 토큰도 저장

            api.interceptors.request.use((config) => {
                const token = localStorage.getItem("accessToken");
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
            return config;
            });
            
            const meRes = await fetchMe(); // 내 정보
            const menuRes = await fetchMenu(); // 메뉴

            setAuth({
                role : meRes.data.role,
                menus : menuRes.data.menus,
            })

            // 새로고침 대비용
            localStorage.setItem('role', meRes.data.role);
            localStorage.setItem('menu', JSON.stringify(menuRes.data.menus));

            //  홈으로 이동
            navigate('/dashboard', {replace : true});

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
        }catch(error){
            alert("로그인 실패")
            console.error(error);
        }
        
    //     // 임시 로그인 처리
    //     // 🔥 1. 임시 토큰
    //     localStorage.setItem('accessToken', 'mock-token');

    //     // 🔥 2. role 지정 (테스트하고 싶은 거로)
    //     const getTestRole = (): Role => {
    //         return 'SYSTEMMANAGER';
    //         //return 'ADMIN';
    //         //return 'DOCTOR';
    //         // return 'NURSE';
    //         // return 'RIS';
    //         // return 'LIS';
    //         // return 'PATIENT';
    //     };

    //     let role: Role = getTestRole();

    //     localStorage.setItem('accessToken', 'mock-token');
    //     localStorage.setItem('role', role);
    //     localStorage.setItem('menus', JSON.stringify([]));

    //     // AuthContext 갱신 (🔥 이게 핵심)
    //     setRole(role);

    //     // 🔥 3. 해당 role에 맞는 메뉴a
    //     let menus: MenuId[] = [];

    //     switch (role) {
    //         case 'SYSTEMMANAGER':
    //             menus = []; // 모든 메뉴 접근 가능
    //             break;
    //         case 'ADMIN':
    //             menus = [
    //                 'ADMIN_USER',
    //                 'ADMIN_ROLE',
    //                 'ADMIN_MENU_PERMISSION',
    //                 'ADMIN_AUDIT_LOG',
    //                 'ADMIN_SYSTEM_MONITOR',
    //             ];
    //             break;
    //         case 'DOCTOR':
    //             menus = [
    //                 'DASHBOARD',
    //                 'PATIENT_LIST',
    //                 'PATIENT_DETAIL',
    //                 'PATIENT_SUMMARY',
    //                 'PATIENT_IMAGING',
    //                 'PATIENT_LAB_RESULT',
    //                 'PATIENT_AI_SUMMARY',
    //                 'ORDER_LIST',
    //                 'ORDER_CREATE',
    //                 'IMAGE_VIEWER',
    //                 'AI_SUMMARY',
    //             ];
    //             break;

    //         case 'NURSE':
    //             menus = [
    //                 'DASHBOARD',
    //                 'PATIENT_LIST',
    //                 'PATIENT_DETAIL',
    //                 'PATIENT_SUMMARY',
    //                 'PATIENT_IMAGING',
    //                 'PATIENT_LAB_RESULT',
    //                 'ORDER_LIST',
    //                 'IMAGE_VIEWER',
    //             ];
    //             break;

    //         case 'RIS':
    //             menus = [
    //                 'IMAGE_VIEWER',
    //                 'RIS_WORKLIST',
    //                 'RIS_READING',
    //             ];
    //             break;

    //         case 'LIS':
    //             menus = [
    //                 'LAB_RESULT_UPLOAD',
    //                 'LAB_RESULT_VIEW',
    //             ];
    //             break;
    //     }

    //     localStorage.setItem('menus', JSON.stringify(menus));

    // // 🔁 4. 홈 이동 → HomeRedirect가 Role_Home 처리
    //     navigate('/dashboard', { replace: true });

        
    }

    return(
        <div className="login-page">
            <div className="login-overlay" />

            <header className="login-header">
                <div className="logo">                
                <span className="logo-icon">
                    <i className="fa-solid fa-brain"></i>
                </span>
                <div>
                    <strong>CDSS</strong>
                    <span className="sub">(brain_tumor)</span>
                    <div className="desc">CLINICAL DECISION SUPPORT SYSTEM</div>
                </div>
                </div>
            </header>

            <div className="login-container">
                <div className="login-card">
                <h2>로그인</h2>

                <div className="login-field">
                    <input
                    placeholder="아이디"
                    onChange={(e) => setId(e.target.value)}
                    />
                </div>

                <div className="login-field">
                    <input
                    type="password"
                    placeholder="비밀번호"
                    onChange={(e) => setPw(e.target.value)}
                    />
                </div>

                <button className="login-button" onClick={handleLogin}>
                    로그인
                </button>

                <div className="login-footer">
                    <a href="#">비밀번호를 잊으셨나요?</a>
                </div>
                </div>
            </div>
        </div>
    )
}