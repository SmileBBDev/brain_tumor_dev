import type { Role } from '@/types/role';
import AiViewer from './AiViewer';
import AiResultPanel from './AiResultPanel';

export default function AiSummaryPage() {
  const role = localStorage.getItem('role') as Role | null;
  if (!role) return <div>접근 권한 정보 없음</div>;

  return (
    <div className="page ai-summary">
      {/* <AiSummaryHeader /> */}
      <h1>AI 분석 결과</h1>
      <div className="ai-body">
        {/* 좌측 Viewer */}
        <section className="ai-viewer-area">
          <AiViewer />
        </section>
        {/* 우측 Result Panel */}
        <aside className="ai-panel-area">
          <AiResultPanel />
        </aside>
      </div>
    </div>
  );
}
