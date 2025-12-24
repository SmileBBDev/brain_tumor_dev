export function RISWorklist() {
  return (
    <section className="card ris-worklist">
      <header className="card-header">
        <h3>영상 판독 목록</h3>
      </header>

      <table className="table">
        <thead>
          <tr>
            <th>환자</th>
            <th>검사</th>
            <th>AI</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <RISRow
            patient="박민수"
            modality="MRI Brain"
            ai="Positive"
            status="대기"
          />
        </tbody>
      </table>
    </section>
  );
}

function RISRow({ patient, modality, ai, status }: any) {
  return (
    <tr className="clickable">
      <td>{patient}</td>
      <td>{modality}</td>
      <td>
        <span className={`badge ${ai === 'Positive' ? 'danger' : ''}`}>
          {ai}
        </span>
      </td>
      <td>{status}</td>
    </tr>
  );
}
