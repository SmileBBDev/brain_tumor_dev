// 오늘 진료 요약 (카드형 KPI)
import SummaryCard from '@/pages/common/SummaryCard';

export function DoctorSummaryCards() {
  return (
    <section className="summary-cards">
      <SummaryCard title="오늘 진료 예정" value={12} />
      <SummaryCard title="진료 중" value={3} highlight />
      <SummaryCard title="AI Alert" value={2} danger />
      <SummaryCard title="완료" value={8} />
    </section>
  );
}
