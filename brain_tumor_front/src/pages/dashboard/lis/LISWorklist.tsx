export function LISWorklist() {
  return (
    <section className="card lis-worklist">
      <header className="card-header">
        <h3>검사 작업 목록</h3>
      </header>

      <table className="table">
        <thead>
          <tr>
            <th>환자</th>
            <th>검사</th>
            <th>상태</th>
            <th>접수시간</th>
          </tr>
        </thead>
        <tbody>
          <LISRow
            patient="김영희"
            test="혈액검사"
            status="분석중"
            time="09:20"
          />
        </tbody>
      </table>
    </section>
  );
}

function LISRow({ patient, test, status, time }: any) {
  return (
    <tr className="clickable">
      <td>{patient}</td>
      <td>{test}</td>
      <td>
        <span className="badge in-progress">{status}</span>
      </td>
      <td>{time}</td>
    </tr>
  );
}
