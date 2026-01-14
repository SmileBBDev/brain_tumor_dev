import { RISSummaryCards } from "./RISSummaryCards";
import { RISWorklist } from "./RISWorklist";
import { RISPendingReports } from "./RISPendingReports";
import { UnifiedCalendar } from "@/components/calendar/UnifiedCalendar";

export default function RISDashboard() {
  return (
    <div className="dashboard ris">
      <RISSummaryCards />
      <div className="dashboard-row">
        <RISWorklist />
        <UnifiedCalendar title="RIS 통합 캘린더" />
      </div>
      <RISPendingReports />
    </div>
  );
}
