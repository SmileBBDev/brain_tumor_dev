// Header영역 메뉴 navigator
import { useLocation } from 'react-router-dom';
import type { MenuNode } from '@/types/menu';

interface BreadcrumbItem {
  id: string;
  label: string;
  path?: string;
}

function findBreadcrumbPath(
  menus: MenuNode[],
  pathname: string,
  role: string | null,
  parents: BreadcrumbItem[] = [],
): BreadcrumbItem[] | null {
  for (const menu of menus) {
    let matched = false;
    let params: Record<string, string> = {};

    // path 매칭 시도
    if (menu.path) {
      const result = matchPathPattern(menu.path, pathname);
      matched = result.matched;
      params = result.params;
    }

    if (!matched && !menu.children) continue;

    // group 메뉴 (path 없음) → breadcrumb에는 제외
    if (!menu.path && menu.children) {
      const childResult = findBreadcrumbPath(
        menu.children,
        pathname,
        role,
        parents
      );
      if (childResult) return childResult;
      continue;
    }

    const roleKey = role ?? 'DEFAULT';
    const current: BreadcrumbItem = {
      id: menu.code,
      label:
        menu.labels?.[roleKey] ??
        menu.labels?.['DEFAULT'] ??
        menu.code,
      path: menu.breadcrumbOnly ? undefined : menu.path,
    };

    // children 탐색
    if (menu.children) {
      const childResult = findBreadcrumbPath(
        menu.children,
        pathname,
        role,
        [...parents, current]
      );
      if (childResult) return childResult;
    }

    // leaf 매칭
    if (matched) {
      return [...parents, current];
    }
  }

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

export default function useBreadcrumb(
  menus: MenuNode[],
  role: string | null
) {
  const location = useLocation();

  const breadcrumb =
    findBreadcrumbPath(menus, location.pathname, role) ?? [];

  return breadcrumb;
}