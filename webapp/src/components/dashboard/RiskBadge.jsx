import { RISK_COLORS } from './RiskGauge';
import './RiskBadge.css';

export default function RiskBadge({ riskLevel }) {
  const color = RISK_COLORS[riskLevel] || RISK_COLORS.Medium;
  return (
    <span className="risk-badge" style={{ color, background: `${color}1A`, borderColor: `${color}55` }}>
      {riskLevel} risk
    </span>
  );
}
