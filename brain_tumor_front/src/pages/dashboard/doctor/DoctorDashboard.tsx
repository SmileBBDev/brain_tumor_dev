import { DoctorSummaryCards } from "./DoctorSummaryCards";
import { DoctorWorklist } from "./DoctorWorklist";
import { AiAlertPanel } from "./AiAlertPanel";
import { RecentPatients } from "./RecentPatients";

export default function DoctorDashboard() {
  return (
    <div className="dashboard doctor">
      <DoctorSummaryCards />
      <div className="dashboard-row">
        <DoctorWorklist />
        <AiAlertPanel />
      </div>
      <RecentPatients />
    </div>
  );
}
