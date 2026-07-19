import './RiskImpactCard.css';

const LEVEL_COLORS = {
  Critical: '#B91C3C', High: 'var(--danger)', Medium: 'var(--warning)', Low: 'var(--info)',
};

export default function RiskImpactCard({ label, value }) {
  const color = LEVEL_COLORS[value] || 'var(--text-secondary)';
  return (
    <div className="risk-impact-card">
      <div className="risk-impact-label">{label}</div>
      <div className="risk-impact-value" style={{ color }}>{value}</div>
    </div>
  );
}
