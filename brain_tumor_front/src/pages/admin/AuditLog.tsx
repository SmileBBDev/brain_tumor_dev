export default function AuditLog() {
  return (
    <div className="admin-card">
      <h2 className="admin-section-title">접근 감사 로그</h2>

      <div className="admin-toolbar">
        <input placeholder="사용자 ID" />
        <input type="date" />
        <select>
          <option>전체</option>
          <option>성공</option>
          <option>실패</option>
        </select>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>시간</th>
            <th>사용자</th>
            <th>역할</th>
            <th>메뉴</th>
            <th>결과</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>2025-01-23 14:21</td>
            <td>doctor01</td>
            <td>DOCTOR</td>
            <td>PATIENT_DETAIL</td>
            <td className="success">성공</td>
          </tr>
          <tr>
            <td>2025-01-23 14:05</td>
            <td>nurse02</td>
            <td>NURSE</td>
            <td>ORDER_CREATE</td>
            <td className="fail">차단</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
