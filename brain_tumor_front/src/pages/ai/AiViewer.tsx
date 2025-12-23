export default function AiViewer() {
  return (
    <div className="ai-viewer">
      <div className="viewer-toolbar">
        <button>AI 결과 숨기기</button>
        <button>Heatmap</button>
        <button>Bounding Box</button>
      </div>

      <div className="viewer-canvas">
        {/* OHIF / medDream iframe 들어갈 자리 */}
        <div className="mock-image">
          영상 Viewer 영역
          <div className="overlay">AI Overlay 표시</div>
        </div>
      </div>
    </div>
  );
}
