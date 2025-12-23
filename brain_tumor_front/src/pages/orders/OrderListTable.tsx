import type { Role } from '@/types/role';

// role에 따른 테이블 컬럼 매핑 컴포넌트
export default function OrderListTable({ role }: { role: Role }) {
  return (
    <table>
      <thead>
        <tr>
          <th>환자ID</th>
          <th>이름</th>

          {role !== 'PATIENT' && <th>성별</th>}
          {role !== 'PATIENT' && <th>나이</th>}

          {role === 'DOCTOR' && <th>진료과</th>}
          {role === 'NURSE' && <th>병동</th>}

          <th>상태</th>
        </tr>
      </thead>

      <tbody>
        <tr>
          <td colSpan={6} align="center">
            데이터 없음
          </td>
        </tr>
      </tbody>
    </table>
  );
}
