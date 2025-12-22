import {api} from '@/services/api';

// 인증 API 모음
export const login = (id : string, password : string) =>
    api.post('/auth/login', {id, password});

export const fetchMe = () =>
    api.get('/auth/me');

export const fetchMenu = () =>
    api.get('/auth/menu');
