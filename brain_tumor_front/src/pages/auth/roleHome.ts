import type {Role} from '@/types/role'; 

// Role별 기본 진입 화면 설정
export const Role_Home: Record<Role, string> = {
    'ADMIN' : '/admin/users',
    'DOCTOR' : '/dashboard',
    'NURSE' : '/patients',
    'RIS' : '/imaging',
    'LIS' : '/lab',
    'PATIENT' : 'my',
};
