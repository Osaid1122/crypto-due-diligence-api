// Deterministic attack-scenario derivation. Educational only — never claims
// an attack happened, never fabricates a scenario not grounded in a real
// backend finding, never uses AI or randomness. Every scenario maps to a
// field the backend either flagged in triggered_rules, or (for ownership
// renouncement, which isn't a scored field) derived the same way
// Protection Advisor does.
import { deriveOwnershipRenounced } from './derived.js';

const TIMELINE_STEPS = ['Risk Detected', 'Potential Abuse', 'Immediate Effect', 'Possible Outcome', 'Recommended Mitigation'];

// Fixed order — most severe/likely-to-matter first. This list, not the
// order triggered_rules happens to arrive in, is what determines output
// order, so ordering is deterministic regardless of backend array order.
const ORDERED_SCENARIO_KEYS = [
  'is_honeypot', 'is_blacklisted', 'cannot_sell_all', 'is_mintable',
  'hidden_owner', 'can_take_back_ownership', 'ownership_not_renounced',
  'selfdestruct', 'is_proxy', 'top_lp_holder_percent', 'top_holder_percent',
  'insider_percent', 'is_open_source', 'trading_cooldown',
];

// impact/difficulty are fixed per capability — never derived from severity,
// never invented per-instance. probability alone comes from the backend's
// own severity rating for that finding.
const SCENARIO_DEFINITIONS = {
  is_honeypot: {
    title: 'Honeypot Behavior Detected',
    description: 'This token is flagged as a honeypot. This configuration permits blocking sales entirely, which could prevent holders from exiting their position.',
    timeline: ['Risk detected', 'Sell transactions blocked', 'Holders cannot exit position', 'Funds effectively locked', 'Avoid transacting until independently verified'],
    impact: 'Critical', difficulty: 'Low',
    mitigation: 'Avoid this token until honeypot status is independently verified.',
  },
  is_blacklisted: {
    title: 'Blacklist Capability',
    description: 'This contract includes a blacklist function. If abused, this capability could allow specific addresses to be blocked from transferring tokens.',
    timeline: ['Risk detected', 'Address added to blacklist', 'Transfers restricted', 'Funds become difficult to move', 'Review blacklist permissions'],
    impact: 'High', difficulty: 'Low',
    mitigation: 'Review who controls the blacklist function and under what conditions it can be used.',
  },
  cannot_sell_all: {
    title: 'Partial Sell Restriction',
    description: 'This contract may restrict holders from selling their full balance. If abused, this could prevent a complete exit from the position.',
    timeline: ['Risk detected', 'Partial sell restriction triggered', 'Full exit prevented', 'Position cannot be fully closed', 'Test with a small transaction first'],
    impact: 'High', difficulty: 'Low',
    mitigation: 'Test sell functionality with a small amount before committing further funds.',
  },
  is_mintable: {
    title: 'Mint Enabled',
    description: "This contract's owner retains the ability to mint additional tokens. If abused, this capability could allow supply inflation that dilutes existing holders.",
    timeline: ['Risk detected', 'Owner mints additional tokens', 'Supply increases', 'Existing holders diluted', 'Monitor mint authority'],
    impact: 'High', difficulty: 'Low',
    mitigation: 'Confirm whether minting is governed by a multisig or timelock, and monitor mint authority.',
  },
  hidden_owner: {
    title: 'Hidden Owner Control',
    description: 'This contract has a hidden owner. This increases the possibility that control persists even if ownership appears renounced.',
    timeline: ['Risk detected', 'Hidden owner executes a privileged function', 'Control persists undetected', 'Apparent renouncement is misleading', 'Investigate hidden owner controls'],
    impact: 'High', difficulty: 'Medium',
    mitigation: 'Investigate hidden owner controls independently before relying on renouncement.',
  },
  can_take_back_ownership: {
    title: 'Reclaimable Ownership',
    description: 'Ownership can reportedly be reclaimed after being renounced. If abused, this could allow administrative control to be silently restored.',
    timeline: ['Risk detected', 'Ownership reclaimed after appearing renounced', 'Administrative control restored', 'Prior safety assumptions invalidated', 'Confirm ownership cannot be reclaimed'],
    impact: 'High', difficulty: 'Medium',
    mitigation: 'Confirm independently that ownership cannot be silently reclaimed.',
  },
  ownership_not_renounced: {
    title: 'Ownership Not Renounced',
    description: 'Contract ownership has not been renounced. This increases the possibility that a privileged function could be used to change administrative settings or token behavior.',
    timeline: ['Risk detected', 'Owner executes a privileged function', 'Administrative settings change', 'Token behavior changes', 'Monitor owner wallet'],
    impact: 'Medium', difficulty: 'Low',
    // Not a scored field in the deterministic engine, so it has no rule
    // severity to inherit — fixed at Medium, same as every other instance
    // of this scenario. Never random.
    fixedProbability: 'Medium',
    mitigation: 'Monitor the owner wallet for privileged function calls before investing.',
  },
  selfdestruct: {
    title: 'Self-Destruct Function',
    description: 'This contract contains a self-destruct function. If triggered, this could render the contract non-functional and tokens unusable.',
    timeline: ['Risk detected', 'Self-destruct function triggered', 'Contract state erased', 'Token becomes non-functional', 'Confirm self-destruct requires multi-party approval'],
    impact: 'High', difficulty: 'Low',
    mitigation: 'Confirm the self-destruct function cannot be triggered unilaterally.',
  },
  is_proxy: {
    title: 'Proxy Contract',
    description: 'This is an upgradeable proxy contract. This configuration permits the underlying logic to change after deployment, which could alter security assumptions without a new deployment.',
    timeline: ['Risk detected', 'Implementation contract upgraded', 'Logic changes', 'Security assumptions change', 'Review upgrade permissions'],
    impact: 'Medium', difficulty: 'Medium',
    mitigation: 'Review who holds upgrade permissions on the proxy admin.',
  },
  top_lp_holder_percent: {
    title: 'Liquidity Risk',
    description: 'Liquidity is concentrated in very few positions. If that liquidity is removed, this could allow high slippage and price instability.',
    timeline: ['Risk detected', 'Liquidity decreases', 'High slippage', 'Price instability', 'Monitor liquidity pools'],
    impact: 'High', difficulty: 'Medium',
    mitigation: 'Verify liquidity lock status independently and monitor liquidity pools.',
  },
  top_holder_percent: {
    title: 'High Holder Concentration',
    description: 'A small number of wallets hold a large share of supply. This increases the possibility of heavy sell pressure and volatility if a large holder exits.',
    timeline: ['Risk detected', 'Large holder sells', 'Heavy market pressure', 'High volatility', 'Monitor whale wallets'],
    impact: 'Medium', difficulty: 'Low',
    mitigation: 'Track whale wallets for sudden movement before investing.',
  },
  insider_percent: {
    title: 'Concentrated Owner/Creator Holdings',
    description: 'The owner or creator wallet holds a large share of supply directly. This increases the possibility of significant price impact if that wallet sells.',
    timeline: ['Risk detected', 'Owner/creator wallet sells', 'Concentrated selling pressure', 'Price impact from insider wallet', 'Monitor owner/creator wallet movements'],
    impact: 'High', difficulty: 'Low',
    mitigation: 'Monitor the owner/creator wallet for movement before investing.',
  },
  is_open_source: {
    title: 'Unverified Source Code',
    description: 'This contract\u2019s source code is not verified. This increases the possibility that functions exist which cannot be independently reviewed.',
    timeline: ['Risk detected', 'Contract logic cannot be independently reviewed', 'Hidden functions cannot be ruled out', 'Trust relies on team claims alone', 'Request contract verification'],
    impact: 'Medium', difficulty: 'Medium',
    mitigation: 'Request contract source verification from the team before proceeding.',
  },
  trading_cooldown: {
    title: 'Trading Cooldown',
    description: 'This contract enforces a trading cooldown. This configuration permits restrictions on transaction timing that could affect trading strategies.',
    timeline: ['Risk detected', 'Cooldown mechanics enforced', 'Trading temporarily restricted', 'Timing-sensitive strategies affected', 'Understand cooldown mechanics before trading'],
    impact: 'Low', difficulty: 'Low',
    mitigation: 'Understand cooldown mechanics before attempting to trade.',
  },
};

/**
 * Returns an array of populated attack scenario objects for the given
 * /analyze/token result, in a fixed deterministic order. Returns an empty
 * array for a clean token — no scenario is ever fabricated.
 */
export function getAttackScenarios(result) {
  if (!result) return [];

  const ruleByField = new Map((result.triggered_rules || []).map(r => [r.field, r]));
  const ownershipRenounced = deriveOwnershipRenounced(result?.technical_data?.owner_address);

  const scenarios = [];
  for (const key of ORDERED_SCENARIO_KEYS) {
    const def = SCENARIO_DEFINITIONS[key];

    if (key === 'ownership_not_renounced') {
      if (ownershipRenounced === false) {
        scenarios.push({ key, ...def, probability: def.fixedProbability });
      }
      continue;
    }

    const rule = ruleByField.get(key);
    if (rule) {
      scenarios.push({ key, ...def, probability: rule.severity || 'Medium' });
    }
  }

  return scenarios;
}

export { TIMELINE_STEPS };
