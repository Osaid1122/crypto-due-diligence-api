import { Trophy, Scale } from 'lucide-react';
import { compareResults } from './compareLogic';
import './ComparisonSummary.css';

export default function ComparisonSummary({ resultA, resultB }) {
  const { winner, reason } = compareResults(resultA, resultB);
  if (!winner) return null;

  if (winner === 'tie') {
    return (
      <div className="comparison-summary comparison-summary-tie">
        <Scale size={20} />
        <div>
          <div className="comparison-summary-title">Equivalent risk profile</div>
          <div className="comparison-summary-reason">{reason}</div>
        </div>
      </div>
    );
  }

  const winnerResult = winner === 'A' ? resultA : resultB;
  return (
    <div className="comparison-summary comparison-summary-winner">
      <Trophy size={20} />
      <div>
        <div className="comparison-summary-title">
          {winnerResult.token_symbol || `Token ${winner}`} appears safer based on deterministic analysis
        </div>
        <div className="comparison-summary-reason">{reason}</div>
      </div>
    </div>
  );
}
