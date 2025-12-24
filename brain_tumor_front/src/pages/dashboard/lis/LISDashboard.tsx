import { LISSummary } from "./LISSummary";
import { LISWorklist } from "./LISWorklist";
import { LISAbnormalAlert } from "./LISAbnormalAlert";
// 검사 중심 Workflow
/**
 * [LIS Summary]
    - 오늘 접수 검사
    - 분석 중
    - 결과 입력 대기
    - 결과 전송 완료

    [LIS Worklist]
    - 검사 목록 (검사종류 / 환자 / 상태)

    [Abnormal Result Alert]
    - Critical 수치 알림
 */
export default function LISDashboard() {
  return (
    <div className="dashboard lis">
      <LISSummary />
      <LISWorklist />
      <LISAbnormalAlert />
    </div>
  );
}
