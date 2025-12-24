export default function SummaryCard({
  title,
  value,
  highlight,
  danger,
}: {
  title: string;
  value: number;
  highlight?: boolean;
  danger?: boolean;
}) {
  return (
    <div
      className={`card summary ${
        highlight ? 'highlight' : ''
      } ${danger ? 'danger' : ''}`}
    >
      <span className="title">{title}</span>
      <strong className="value">{value}</strong>
    </div>
  );
}
