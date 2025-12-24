export function DoctorWorklist() {
  return (
    <section className="card worklist">
      <header className="card-header">
        <h3>오늘 진료 목록</h3>
        <a href="/patients">전체 보기</a>
      </header>

      <table className="table">
        <thead>
          <tr>
            <th>환자명</th>
            <th>상태</th>
            <th>진료 유형</th>
            <th>예약 시간</th>
          </tr>
        </thead>
        <tbody>
          <WorklistRow
            name="홍길동"
            status="진료중"
            type="외래"
            time="10:30"
          />
          <WorklistRow
            name="김영희"
            status="대기"
            type="병동"
            time="11:00"
          />
        </tbody>
      </table>
    </section>
  );
}

function WorklistRow({
  name,
  status,
  type,
  time,
}: {
  name: string;
  status: string;
  type: string;
  time: string;
}) {
  return (
    <tr className="clickable">
      <td>{name}</td>
      <td>
        <span className={`badge ${status === '진료중' ? 'in-progress' : ''}`}>
          {status}
        </span>
      </td>
      <td>{type}</td>
      <td>{time}</td>
    </tr>
  );
}
