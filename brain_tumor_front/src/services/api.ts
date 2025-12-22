import axios from 'axios';

// 비동기 api 통신 기본 세팅
// Axios 인스턴스
export const api = axios.create({
    baseURL : '/api',
    withCredentials : true,
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("accessToken");
    // token 정보 확인
    if(token){
        config.headers.Authorization = `Bearer${token}` 
    }
    return config;
})