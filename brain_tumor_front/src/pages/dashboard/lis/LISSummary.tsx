import SummaryCard from '@/pages/common/SummaryCard';

export function LISSummary() {
  return (
    <section className="summary-cards lis">
      <SummaryCard title="오늘 접수" value={42} />
      <SummaryCard title="분석 중" value={6} highlight />
      <SummaryCard title="결과 입력 대기" value={4} />
      <SummaryCard title="Critical" value={1} danger />
    </section>
  );
}
