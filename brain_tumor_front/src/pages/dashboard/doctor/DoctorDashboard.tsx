import { DoctorSummaryCards } from "./DoctorSummaryCards";
import { DoctorWorklist } from "./DoctorWorklist";
import { DoctorScheduleCalendar } from "./DoctorScheduleCalendar";
import { AiAlertPanel } from "./AiAlertPanel";
import PatientListWidget from "../common/PatientListWidget";
import '@/assets/style/patientListView.css';

export default function DoctorDashboard() {
  return (
    <div className="dashboard doctor">
      <DoctorSummaryCards />
      <div className="dashboard-row">
        <DoctorWorklist />
        <DoctorScheduleCalendar />
      </div>
      <div className="dashboard-row">
        <AiAlertPanel />
        <PatientListWidget
          title="최근 환자"
          limit={5}
          showViewAll={true}
        />
      </div>
    </div>
  );
}
