export default function UserListPage(){
    return(
        <div className="admin-card">
            <div className="admin-toolbar">
            <input placeholder="사용자명 / ID 검색" />
            <button className="primary">사용자 추가</button>
            </div>

            <table className="admin-table">
            <thead>
                <tr>
                <th>ID</th>
                <th>이름</th>
                <th>역할</th>
                <th>상태</th>
                <th>최근 로그인</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <td>doctor01</td>
                <td>홍길동</td>
                <td>DOCTOR</td>
                <td><span className="badge active">활성</span></td>
                <td>2025-01-23 10:12</td>
                </tr>
                <tr>
                <td>admin01</td>
                <td>관리자</td>
                <td>ADMIN</td>
                <td><span className="badge inactive">비활성</span></td>
                <td>2025-01-20 18:44</td>
                </tr>
            </tbody>
            </table>
        </div>
  );
};