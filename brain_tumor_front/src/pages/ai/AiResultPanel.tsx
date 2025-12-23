import AiLesionList from './AiLesionList';

export default function AiResultPanel() {
  return (
    <aside className="ai-panel">
      <section className="ai-score">
        <h3>AI Score</h3>
        <div className="score-value">0.87</div>
      </section>

      <section className="ai-lesions">
        <h3>탐지 병변</h3>
        <AiLesionList />
      </section>

      <section className="ai-summary-text">
        <h3>AI 요약</h3>
        <p>
          좌측 측두엽 부위에서 종양으로 의심되는 병변이 탐지되었습니다.
          추가적인 판독이 필요합니다.
        </p>
      </section>

      <section className="ai-actions">
        <button className="btn primary">Report에 삽입</button>
      </section>
    </aside>
  );
}
