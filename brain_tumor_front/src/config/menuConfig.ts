import type { MenuId } from '@/types/menu';
import type { Role } from '@/types/role';

// TODO : 메뉴가 추가되는 경우 - 여기에도 추가 필요
export interface MenuConfig {
  id: MenuId;
  path?: string; // sidebar & routing 
  icon?: string; 
  roles: Role[];
  label: Partial<Record<Role | 'DEFAULT', string>>;
  groupLabel?: string; // Sidebar 그룹용
  children?: MenuConfig[]; // sidebar group

  // 실제 sidebar 메뉴로 구성되어있지는 않지만 상세메뉴로 화면이 바뀔 때
  breadcrumbOnly?: boolean; // breadcrumb 전용
  dynamicLabel?: (params : Record<string, string>) => string; // 상세 페이지용
}

export const MENU_CONFIG: MenuConfig[] = [
  // Dashboard
  {
    id: 'DASHBOARD',
    path: '/dashboard',
    icon: 'home',
    roles: ['DOCTOR', 'NURSE'],
    label: {
      DEFAULT: '대시보드',
      DOCTOR: '의사 대시보드',
      NURSE: '간호 대시보드',
    },
  },

 
  // Patient - 환자 관리
  // {
  //   id: 'PATIENT_LIST',
  //   path: '/patients',
  //   icon: 'users',
  //   roles: ['DOCTOR', 'NURSE'],
  //   label: {
  //     DEFAULT: '환자 목록',
  //     DOCTOR: '환자 목록',
  //     NURSE: '환자 목록',
  //   },
  //   children: [
  //     {
  //       id: 'PATIENT_DETAIL',
  //       path: '/patients/:id',
  //       roles: ['DOCTOR', 'NURSE'],
  //       breadcrumbOnly: true, // 🔥 핵심
  //       label: {
  //         DEFAULT: '환자 상세',
  //       },
  //     },
  //   ],
  // },
  {
    id: 'PATIENT',
    roles: ['DOCTOR', 'NURSE'],
    groupLabel : '환자',
    label: { DEFAULT: '환자' },
    children: [
      {
        id: 'PATIENT_LIST',
        path: '/patients',
        icon: 'users',
        roles: ['DOCTOR', 'NURSE'],
        label: { DEFAULT: '환자 목록' },
      },
      {
        id: 'PATIENT_DETAIL',
        path: '/patients/:id',
        roles: ['DOCTOR', 'NURSE'],
        breadcrumbOnly: true,
        label: { DEFAULT: '환자 상세' },
      },
    ],
  },




 
  // Order
  {
    id: 'ORDER',
    roles: ['DOCTOR', 'NURSE'],
    groupLabel : '검사 오더',
    label: {
      DEFAULT: '검사 오더',
      DOCTOR: '검사 오더',
      NURSE: '검사 현황',
    },
    children: [
      {
        id: 'ORDER_LIST',
        path: '/orders',
        icon: 'clipboard',
        roles: ['DOCTOR', 'NURSE'],
        label: {
          DEFAULT: '오더 목록',
        },
      },
      {
        id: 'ORDER_CREATE',
        path: '/orders/create',
        roles: ['DOCTOR'],
        breadcrumbOnly: true,
        label: {
          DEFAULT: '오더 생성',
        },
      },
    ],
  },

 
  // Imaging / RIS
  {
    id: 'IMAGING',
    roles: ['DOCTOR', 'RIS'],
    groupLabel : '영상',
    label: {
      DEFAULT: '영상',
    },
    children: [
      {
        id: 'IMAGE_VIEWER',
        path: '/imaging',
        icon: 'image',
        roles: ['DOCTOR', 'RIS'],
        label: {
          DEFAULT: '영상 조회',
        },
      },
      {
        id: 'RIS_WORKLIST',
        path: '/ris/worklist',
        icon: 'x-ray',
        roles: ['RIS'],
        label: {
          DEFAULT: '판독 Worklist',
        },
      },
    ],
  },

  // AI
  {
    id: 'AI_SUMMARY',
    path: '/ai',
    icon: 'brain',
    roles: ['DOCTOR', 'NURSE'],
    label: {
      DEFAULT: 'AI 분석 요약',
    },
  },

 
  // LIS
  {
    id: 'LAB',
    roles: ['DOCTOR', 'NURSE', 'LIS'],
    groupLabel : '검사',
    label: {
      DEFAULT: '검사',
    },
    children: [
      {
        id: 'LAB_RESULT_VIEW',
        path: '/lab',
        icon: 'book',
        roles: ['DOCTOR', 'NURSE'],
        label: {
          DEFAULT: '검사 결과 조회',
        },
      },
      {
        id: 'LAB_RESULT_UPLOAD',
        path: '/lab/upload',
        roles: ['LIS'],
        breadcrumbOnly: true,
        label: {
          DEFAULT: '검사 결과 업로드',
        },
      },
    ],
  },

 
  // Admin
  {
    id: 'ADMIN',
    icon: 'settings',
    roles: ['ADMIN'],
    label: {
      DEFAULT: '관리자',
    },
    children: [
      {
        id: 'ADMIN_USER',
        path: '/admin/users',
        roles: ['ADMIN'],
        label: {
          DEFAULT: '사용자 관리',
        },
      },
      {
        id: 'ADMIN_MENU_PERMISSION',
        path: '/admin/permissions',
        roles: ['ADMIN'],
        label: {
          DEFAULT: '메뉴 권한 관리',
        },
      },
      {
        id: 'ADMIN_AUDIT_LOG',
        path: '/admin/audit',
        roles: ['ADMIN'],
        breadcrumbOnly: true,
        label: {
          DEFAULT: '접근 감사 로그',
        },
      },
      {
        id: 'ADMIN_SYSTEM_MONITOR',
        path: '/admin/monitor',
        roles: ['ADMIN'],
        breadcrumbOnly: true,
        label: {
          DEFAULT: '시스템 모니터링',
        },
      },
    ],
  },
];

// export const MENU_CONFIG: MenuConfig[] = [
//   // Dashboard
//   {
//     id: 'DASHBOARD',
//     path: '/dashboard',
//     icon: 'home',
//     roles: ['DOCTOR', 'NURSE'],
//     label: {
//       DEFAULT: '대시보드',
//       DOCTOR: '의사 대시보드',
//       NURSE: '간호 대시보드',
//     },
//   },

//   // Patient
//   {
//     id: 'PATIENT_LIST',
//     icon: 'users',
//     roles: ['DOCTOR', 'NURSE'],
//     label: {
//       DEFAULT: '환자 관리',
//       DOCTOR: '환자 관리',
//       NURSE: '환자 목록',
//     },
//   },
//   {
//     id: 'PATIENT_DETAIL',
//     path: '/patients/:id',
//     roles: ['DOCTOR', 'NURSE'],
//     breadcrumbOnly: true,
//     label: {
//       DEFAULT: '환자 상세',
//       DOCTOR: '환자 상세',
//       NURSE: '환자 상세',
//     },
//   },

//   // Order
//   {
//     id: 'ORDER_LIST',
//     path: '/orders',
//     icon: 'clipboard',
//     roles: ['DOCTOR', 'NURSE'],
//     label: {
//       DEFAULT: '검사 오더',
//       DOCTOR: '검사 오더',
//       NURSE: '검사 현황',
//     },
//   },

//   {
//     id: 'ORDER_CREATE',
//     path: '/orders/create',
//     icon: 'clipboard',
//     roles: ['DOCTOR'],
//     label: {
//       DEFAULT: '오더 생성',
//       DOCTOR: '오더 생성',
//     },
//   },

//   // Imaging / RIS

//   {
//     id: 'IMAGE_VIEWER',
//     path: '/imaging',
//     icon: 'image',
//     roles: ['DOCTOR', 'RIS'],
//     label: {
//       DEFAULT: '영상 판독(RIS)',
//       DOCTOR: '영상 조회',
//       RIS: '영상 판독',
//     },
//   },

//   {
//     id: 'RIS_WORKLIST',
//     path: '/ris/worklist',
//     icon: 'x-ray',
//     roles: ['RIS'],
//     label: {
//       DEFAULT: '판독 Worklist(RIS)',
//       RIS: '판독 Worklist',
//     },
//   },

//   // AI
//   {
//     id: 'AI_SUMMARY',
//     path: '/ai',
//     icon: 'brain',
//     roles: ['DOCTOR', 'NURSE'],
//     label: {
//       DEFAULT: 'AI 분석 요약',
//       DOCTOR: 'AI 분석 요약',
//       NURSE: 'AI 결과 조회',
//     },
//   },

//   // LIS
//   {
//     id: 'LAB_RESULT_VIEW',
//     path: '/lab',
//     icon: 'book',
//     roles: ['DOCTOR', 'NURSE'],
//     label: {
//       DEFAULT: '검사 결과 조회',
//       DOCTOR: '검사 결과',
//       NURSE: '검사 결과 조회',
//     },
//   },
//   {
//     id: 'LAB_RESULT_UPLOAD',
//     path: '/lab/upload',
//     icon: 'flask',
//     roles: ['LIS'],
//     label: {
//       DEFAULT: '검사 결과 업로드',
//       LIS: '검사 결과 업로드',
//     },
//   },


//   // Admin
//   {
//     id: 'ADMIN_USER',
//     path: '/admin/users',
//     icon: 'users',
//     roles: ['ADMIN'],
//     label: {
//       DEFAULT: '사용자 관리',
//       ADMIN: '사용자 관리',
//     },
//   },

//   {
//     id: 'ADMIN_MENU_PERMISSION',
//     path: '/admin/permissions',
//     icon: 'list',
//     roles: ['ADMIN'],
//     label: {
//       DEFAULT: '메뉴 권한 관리',
//       ADMIN: '메뉴 권한 관리',
//     },
//   },

//   {
//     id: 'ADMIN_AUDIT_LOG',
//     path: '/admin/audit',
//     icon: 'check',
//     roles: ['ADMIN'],
//     label: {
//       ADMIN: '접근 감사 로그',
//     },
//   },

//   {
//     id: 'ADMIN_SYSTEM_MONITOR',
//     path: '/admin/monitor',
//     icon: 'eye',
//     roles: ['ADMIN'],
//     label: {
//       ADMIN: '시스템 모니터링',
//     },
//   },
// ];
