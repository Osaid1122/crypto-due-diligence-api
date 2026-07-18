// Values derived from raw backend data that more than one page needs.
// These are NOT returned directly by GoPlus — they're computed here, once,
// so every page that shows them agrees. Extracted from InfoGrid.jsx so
// Protection Advisor can reuse the identical logic rather than reimplement it.

const BURN_ADDRESSES = [
  '0x0000000000000000000000000000000000000000',
  '0x000000000000000000000000000000000000dead',
];

/**
 * Returns true/false/null (unknown) — derived from owner_address being a
 * zero/burn address.
 */
export function deriveOwnershipRenounced(ownerAddress) {
  const addr = (ownerAddress || '').toLowerCase();
  if (!addr) return null;
  return BURN_ADDRESSES.includes(addr);
}

/**
 * Plain-language rollup of trading-restriction flags.
 */
export function deriveTradingRestrictions(normalizedSignals = {}) {
  const restrictions = [];
  if (normalizedSignals.trading_cooldown === true) restrictions.push('Trading cooldown');
  if (normalizedSignals.cannot_sell_all === true) restrictions.push('Cannot sell full balance');
  if (restrictions.length) return restrictions.join(', ');
  if (normalizedSignals.trading_cooldown == null && normalizedSignals.cannot_sell_all == null) return 'Unknown';
  return 'None detected';
}
