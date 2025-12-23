import type { Role } from '@/types/role';

export default function ImagingTab({ role }: { role: Role }) {
  return (
    <div className="imaging-layout">

      {/* Viewer 영역 */}
      <div className="viewer-area">
        <div className="viewer-placeholder">
          <span>영상 Viewer 영역 (OHIF)</span>

          {/* AI Overlay 자리 */}
          <div className="ai-overlay">
            AI Overlay (Heatmap / Bounding Box)
          </div>
        </div>
      </div>

      {/* AI 패널 */}
      <div className="ai-panel">

        <div className="ai-score card">
          <h4>AI Score</h4>
          <strong>0.82</strong>
        </div>

        <div className="ai-lesions card">
          <h4>탐지 병변</h4>
          <ul>
            <li>좌측 전두엽 – High</li>
            <li>우측 측두엽 – Medium</li>
          </ul>
        </div>

        <div className="ai-summary card">
          <h4>AI 요약</h4>
          <p>
            교모세포종 의심 병변이 관찰됩니다.
          </p>
        </div>

      </div>

      {/* 하단 액션 */}
      <div className="imaging-actions">
        <button>AI 결과 숨기기</button>
        <button className="primary">
          AI 요약 Report 삽입
        </button>
      </div>

    </div>
  );
}
