export default function SystemMonitorPage() {
  return (
    <div className="admin-page">
      <h2 className="admin-section-title">시스템 모니터링</h2>

      <div className="monitor-grid">
        <div className="monitor-card ok">
          <h3>서버 상태</h3>
          <p>정상</p>
        </div>

        <div className="monitor-card">
          <h3>활성 세션</h3>
          <p>124</p>
        </div>

        <div className="monitor-card">
          <h3>금일 로그인</h3>
          <p>312</p>
        </div>

        <div className="monitor-card warning">
          <h3>오류 발생</h3>
          <p>2건</p>
        </div>
      </div>
    </div>
  );
}
