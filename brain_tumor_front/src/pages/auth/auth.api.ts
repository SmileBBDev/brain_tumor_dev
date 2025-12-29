import {api} from '@/services/api';

// 인증 API 모음
export const login = (login_id : string, password : string) =>
    api.post('/auth/login/', {login_id, password});

export const fetchMe = () =>
    api.get('/auth/me/');

export const fetchMenu = () =>
    api.get('/auth/menu/');
