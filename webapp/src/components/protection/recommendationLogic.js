// Deterministic recommendation engine. AI never decides these — every
// function here derives its output purely from the already-computed
// /analyze/token response (risk_score, triggered_rules, not_triggered_rules,
// normalized_signals). Same principle as compareLogic.js.
//
// NOTE: these thresholds (0-25/26-50/51-75/76-100) are a distinct bucketing
// from the scoring engine's own risk_level (Low/Medium/High/Critical, which
// uses different cutoffs — see app/services/scoring.py). Both are
// deterministic, but they answer different questions: risk_level classifies
// the token, this classifies the recommended *action*.
import { deriveOwnershipRenounced } from '../../utils/derived';

export function getOverallRecommendation(score) {
  if (score <= 25) {
    return { level: 'proceed', label: 'Proceed', desc: 'Proceed with normal due diligence.', color: 'var(--success)' };
  }
  if (score <= 50) {
    return { level: 'caution', label: 'Caution', desc: 'Proceed with caution — review the flagged items below first.', color: 'var(--warning)' };
  }
  if (score <= 75) {
    return { level: 'high-risk', label: 'High Risk', desc: 'High risk — extensive verification is needed before interacting with this token.', color: 'var(--danger)' };
  }
  return { level: 'avoid', label: 'Avoid', desc: 'Avoid unless you fully understand and accept the risks identified.', color: '#B91C3C' };
}

// Maps a triggered rule's field to actionable, specific guidance — falls
// back to the rule's own reason text if a field isn't in this table, so
// nothing triggered by the backend is ever silently dropped.
const IMMEDIATE_ACTION_MAP = {
  is_honeypot: 'Do not transact with this token — honeypot behavior was detected.',
  is_mintable: 'Confirm whether additional minting is governed by a multisig or timelock.',
  cannot_sell_all: 'Test with a small transaction before committing significant funds.',
  is_blacklisted: 'Verify who controls the blacklist function and under what conditions it can be used.',
  hidden_owner: 'Investigate hidden owner controls before proceeding.',
  can_take_back_ownership: 'Confirm ownership cannot silently be reclaimed after appearing renounced.',
  selfdestruct: 'Confirm the self-destruct function cannot be triggered unilaterally.',
  is_proxy: 'Review what the upgradeable contract logic actually controls before relying on current behavior.',
  top_lp_holder_percent: 'Verify liquidity lock status independently — concentrated liquidity increases rug-pull risk.',
  top_holder_percent: 'Monitor large holder wallets for movement before investing.',
  insider_percent: 'Monitor the owner/creator wallet for movement before investing.',
  is_open_source: 'Request contract source verification from the team before proceeding.',
  trading_cooldown: 'Understand cooldown mechanics before attempting to trade.',
};

export function getImmediateActions(result) {
  const triggered = result?.triggered_rules || [];
  return triggered.map(rule => ({
    text: IMMEDIATE_ACTION_MAP[rule.field] || rule.reason,
    priority: rule.severity || 'Medium',
  }));
}

// Monitoring items combine one derived, always-relevant check (ownership
// renouncement) with any triggered rules whose nature is ongoing risk
// (things worth watching over time, not just verifying once).
const MONITORING_FIELDS = ['is_mintable', 'top_holder_percent', 'insider_percent', 'top_lp_holder_percent', 'can_take_back_ownership'];

export function getMonitoringChecklist(result) {
  const items = [];
  const renounced = deriveOwnershipRenounced(result?.technical_data?.owner_address);

  if (renounced === false) {
    items.push({ text: 'Ownership is not renounced — monitor owner wallet activity before investing.', priority: 'High' });
  } else if (renounced === true) {
    items.push({ text: 'Ownership is renounced — no owner wallet to monitor for this risk.', priority: null });
  }

  (result?.triggered_rules || [])
    .filter(rule => MONITORING_FIELDS.includes(rule.field))
    .forEach(rule => {
      if (rule.field === 'top_lp_holder_percent') {
        items.push({ text: 'Watch for liquidity removal — concentrated liquidity was detected.', priority: rule.severity });
      } else if (rule.field === 'is_mintable') {
        items.push({ text: 'Watch total supply for unexpected mint events.', priority: rule.severity });
      } else {
        items.push({ text: 'Track holder distribution for sudden concentration changes.', priority: rule.severity });
      }
    });

  return items;
}

// Before-investing checklist mixes fixed best-practice items with one
// conditional item pulled directly from the backend's own not_triggered_rules
// reasoning (e.g. "liquidity is fragmented" — a genuinely positive finding
// that still deserves a caveat, per the spec's own example).
export function getBeforeInvestingChecklist(result) {
  const items = [
    { text: 'Read the contract source code, or a summary from a trusted auditor.' },
    { text: 'Confirm the contract address on the official project website or socials.' },
    { text: 'Cross-check the contract on a block explorer for verification status.' },
  ];

  const fragmentedLp = (result?.not_triggered_rules || []).find(r => r.field === 'top_lp_holder_percent');
  if (fragmentedLp) {
    items.push({ text: `${fragmentedLp.reason} — lower rug-pull risk, but still verify lock status independently.` });
  }

  return items;
}

export function getGoodSigns(result) {
  return [
    ...(result?.positive_signals || []),
    ...((result?.not_triggered_rules || []).map(r => r.reason)),
  ];
}
