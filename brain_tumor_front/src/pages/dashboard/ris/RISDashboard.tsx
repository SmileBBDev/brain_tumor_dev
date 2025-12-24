import { RISSummary } from './RISSummary';
import { RISWorklist } from './RISWorklist';
import { RISAIFlagPanel } from './RISAIFlagPanel';
/**
    [RIS Summary]
    - 판독 대기
    - 판독 중
    - AI Flag
    - 완료

    [RIS Reading Worklist]
    - 영상 목록

    [AI Flag Panel]
    - AI 이상 탐지
 */
export default function RISDashboard() {
  return (
    <div className="dashboard ris">
      <RISSummary />
      <RISWorklist />
      <RISAIFlagPanel />
    </div>
  );
}
