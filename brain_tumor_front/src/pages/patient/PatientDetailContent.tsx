import { useSearchParams } from 'react-router-dom';
import SummaryTab from './tabs/SummaryTab';
import ImagingTab from './tabs/ImagingTab';
import LabResultTab from './tabs/LabResultTab';
import AiSummaryTab from './tabs/AiSummaryTab';

type Props = {
  role: string;
};

export default function PatientDetailContent({ role }: Props) {
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';

  const [params] = useSearchParams();
  const tab = params.get('tab') ?? 'summary';

  if (tab === 'summary') return <SummaryTab role={role} />;
  if (tab === 'imaging') return <ImagingTab role={role} />;
  if (tab === 'lab') return <LabResultTab role={role} />;
  if (tab === 'ai')
    return isDoctor || isSystemManager ? <AiSummaryTab role={role} /> : null;

  return <div>잘못된 접근</div>;
}
