import './RiskImpactCard.css';

const LEVEL_COLORS = { Critical: '#fb7185', High: 'var(--danger)', Medium: 'var(--warning)', Low: 'var(--info)' };

export default function RiskImpactCard({ icon: Icon, label, value, description }) {
  const color = LEVEL_COLORS[value] || 'var(--text-secondary)';
  return <div className="risk-impact-card"><div className="risk-impact-icon" style={{ color }}>{Icon && <Icon size={20} />}</div><div className="risk-impact-label">{label}</div><div className="risk-impact-value" style={{ color }}>{value}</div>{description && <p>{description}</p>}</div>;
}
