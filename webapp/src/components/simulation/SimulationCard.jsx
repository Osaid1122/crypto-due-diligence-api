import Card from '../Card';
import AttackTimeline from './AttackTimeline';
import RiskImpactCard from './RiskImpactCard';
import './SimulationCard.css';

export default function SimulationCard({ scenario }) {
  return (
    <Card className="simulation-card">
      <h3 className="simulation-card-title">{scenario.title}</h3>
      <p className="simulation-card-desc">{scenario.description}</p>

      <div className="simulation-card-stats">
        <RiskImpactCard label="Probability" value={scenario.probability} />
        <RiskImpactCard label="Impact" value={scenario.impact} />
        <RiskImpactCard label="Difficulty" value={scenario.difficulty} />
      </div>

      <p className="simulation-card-section-label">Timeline</p>
      <AttackTimeline steps={scenario.timeline} />

      <p className="simulation-card-section-label">Mitigation</p>
      <p className="simulation-card-mitigation">{scenario.mitigation}</p>
    </Card>
  );
}
