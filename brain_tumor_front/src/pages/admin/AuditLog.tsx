import { useState, useEffect } from 'react';
import { getAuditLogs } from '@/services/audit.api';
import type { AuditLog as AuditLogType } from '@/services/audit.api';

// 시스템 접근 감사 로그 페이지
export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogType[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 필터 상태
  const [userIdFilter, setUserIdFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, dateFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {
        page,
        page_size: pageSize,
      };
      if (userIdFilter) params.user_login_id = userIdFilter;
      if (actionFilter) params.action = actionFilter;
      if (dateFilter) params.date = dateFilter;

      const response = await getAuditLogs(params);
      setLogs(response.results || []);
      setTotalCount(response.count || 0);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchLogs();
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getResultClass = (action: string) => {
    if (action === 'LOGIN_SUCCESS' || action === 'LOGOUT') return 'success';
    if (action === 'LOGIN_FAIL' || action === 'LOGIN_LOCKED') return 'fail';
    return '';
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="admin-card">
      <div className="admin-toolbar">
        <input
          placeholder="사용자 ID"
          value={userIdFilter}
          onChange={(e) => setUserIdFilter(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <input
          type="date"
          value={dateFilter}
          onChange={(e) => {
            setDateFilter(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">전체</option>
          <option value="LOGIN_SUCCESS">로그인 성공</option>
          <option value="LOGIN_FAIL">로그인 실패</option>
          <option value="LOGIN_LOCKED">계정 잠금</option>
          <option value="LOGOUT">로그아웃</option>
        </select>
        <button className="search-btn" onClick={handleSearch}>검색</button>
      </div>

      {loading ? (
        <div className="loading-state">로딩 중...</div>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>시간</th>
                <th>사용자</th>
                <th>이름</th>
                <th>역할</th>
                <th>액션</th>
                <th>IP 주소</th>
                <th>결과</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-row">데이터가 없습니다.</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td>{formatDate(log.created_at)}</td>
                    <td>{log.user_login_id || '-'}</td>
                    <td>{log.user_name || '-'}</td>
                    <td>{log.user_role || '-'}</td>
                    <td>{log.action_display}</td>
                    <td>{log.ip_address || '-'}</td>
                    <td className={getResultClass(log.action)}>
                      {log.action === 'LOGIN_SUCCESS' || log.action === 'LOGOUT' ? '성공' : '실패'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                이전
              </button>
              <span>{page} / {totalPages}</span>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                다음
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
