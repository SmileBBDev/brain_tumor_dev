import { useLocation } from 'react-router-dom';
import { MENU_CONFIG } from '@/config/menuConfig';
import type{ MenuConfig } from '@/config/menuConfig';
import type { Role } from '@/types/role';

interface BreadcrumbItem {
    id : string;
    label : string;
    path? : string;
}

function findBreadcrumbPath(
    menus : MenuConfig[],
    pathname : string,
    role : Role,
    parents : BreadcrumbItem[] = [],
): BreadcrumbItem[] | null {
    for (const menu of menus){

        let matched = false;
        let params: Record<string, string> = {};

        // path가 있을 때 매칭 시도
        if(menu.path) {
            const result = matchPathPattern(
                menu.path,
                pathname,
            );
            matched = result.matched;
            params = result.params;
        }

        if(!matched && !menu.children) continue;

        // 현재 menu label 결정
        const label = 
            menu.dynamicLabel?.(params) ??
            menu.label[role] ?? 
            menu.label.DEFAULT ?? '';

        // ✅ 수정
        const current: BreadcrumbItem | null = menu.path
        ? {
            id: menu.id,
            label,
            path: menu.breadcrumbOnly ? undefined : menu.path,
            }
        : null;


        // children이 있는 경우 재귀 탐색
        if (menu.children) {
            const childResult = findBreadcrumbPath(
                menu.children,
                pathname,
                role,
                current ? [...parents, current] : parents
            );
            if (childResult) return childResult;
        }

        // leaf match
        if (matched && current) {
            return [...parents, current];
        }

                
    };

    return null;
}

function matchPathPattern(
  pattern: string,
  pathname: string
): { matched: boolean; params: Record<string, string> } {
    const paramNames: string[] = [];

    const regexPath = pattern.replace(
    /:([^/]+)/g,
    (_, key) => {
        paramNames.push(key);
        return '([^/]+)';
    }
    );

    const regex = new RegExp(`^${regexPath}`);

    const match = pathname.match(regex);

    if (!match) return { matched: false, params: {} };

    const params = paramNames.reduce((acc, key, idx) => {
    acc[key] = match[idx + 1];
    return acc;
    }, {} as Record<string, string>);

    return { matched: true, params };
}


export default function useBreadcrumb(role:Role){
    
    const location = useLocation();

    const breadcrumb = findBreadcrumbPath(
        MENU_CONFIG,
        location.pathname,
        role
    )?? [];
    

    return breadcrumb;
}