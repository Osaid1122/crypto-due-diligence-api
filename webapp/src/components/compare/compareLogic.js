// Deterministic comparison logic — never AI, matches the "AI never decides
// the winner" principle used throughout this project. Purely derives a
// verdict from scores/confidence the backend already computed.

const RISK_RANK = { Low: 0, Medium: 1, High: 2, Critical: 3 };

/**
 * Returns { winner: 'A' | 'B' | 'tie', reason: string } given two /analyze/token
 * results. Lower risk_score wins; a tie in score falls back to risk_level rank,
 * then to confidence (more complete data is more trustworthy at equal risk).
 */
export function compareResults(resultA, resultB) {
  if (!resultA || !resultB) return { winner: null, reason: '' };

  const scoreDiff = resultA.risk_score - resultB.risk_score;
  if (scoreDiff !== 0) {
    const winner = scoreDiff < 0 ? 'A' : 'B';
    const [safer, other] = winner === 'A' ? [resultA, resultB] : [resultB, resultA];
    return {
      winner,
      reason: `${safer.token_symbol || 'Token ' + winner} scored ${safer.risk_score}/100 versus ${other.risk_score}/100 — a lower deterministic risk score.`,
    };
  }

  const rankDiff = RISK_RANK[resultA.risk_level] - RISK_RANK[resultB.risk_level];
  if (rankDiff !== 0) {
    const winner = rankDiff < 0 ? 'A' : 'B';
    return { winner, reason: `Scores are tied, but ${winner === 'A' ? resultA.token_symbol : resultB.token_symbol} carries a lower risk level classification.` };
  }

  const confDiff = resultA.confidence - resultB.confidence;
  if (Math.abs(confDiff) > 0.001) {
    const winner = confDiff > 0 ? 'A' : 'B';
    return { winner, reason: `Scores and risk levels are tied — ${winner === 'A' ? resultA.token_symbol : resultB.token_symbol} has more complete on-chain security data available.` };
  }

  return { winner: 'tie', reason: 'Both tokens show an equivalent risk profile based on available data.' };
}
