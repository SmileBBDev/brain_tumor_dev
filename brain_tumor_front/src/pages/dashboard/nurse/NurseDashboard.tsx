import NurseSummary from "./NurseSummary";
import NurseTaskBoard from "./NurseTaskBoard";
import PatientStatusList from "./PatientStatusList";

export default function NurseDashboard() {
  return (
    <div className="dashboard nurse">
      <NurseSummary />
      <NurseTaskBoard />
      <PatientStatusList />
    </div>
  );
}
