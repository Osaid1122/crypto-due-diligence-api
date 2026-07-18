import { deriveOwnershipRenounced, deriveTradingRestrictions } from '../../utils/derived';
import './InfoGrid.css';

function yesNo(v) {
  if (v === true) return <span className="info-value info-yes">Yes</span>;
  if (v === false) return <span className="info-value info-no">No</span>;
  return <span className="info-value info-unknown">Unknown</span>;
}

export default function InfoGrid({ normalizedSignals = {}, technicalData = {}, chainName, address }) {
  const ns = normalizedSignals;
  const td = technicalData;
  const renounced = deriveOwnershipRenounced(td.owner_address);

  const items = [
    { label: 'Chain', value: chainName || '—' },
    { label: 'Contract', value: address, mono: true },
    { label: 'Holder count', value: td.holder_count ? Number(td.holder_count).toLocaleString() : '—' },
    { label: 'Liquidity positions', value: ns.lp_position_count ?? '—' },
    { label: 'Largest holder', value: ns.top_holder_percent != null ? `${ns.top_holder_percent.toFixed(1)}%` : '—' },
    { label: 'Owner / creator holds', value: ns.insider_percent != null ? `${ns.insider_percent.toFixed(1)}%` : '—' },
  ];

  const boolItems = [
    { label: 'Proxy contract', value: ns.is_proxy },
    { label: 'Mint function', value: ns.is_mintable },
    { label: 'Blacklist capability', value: ns.is_blacklisted },
    { label: 'Trust list', value: ns.trust_list },
    { label: 'Source code verified', value: ns.is_open_source },
  ];

  return (
    <div className="info-grid">
      {items.map(({ label, value, mono }) => (
        <div className="info-item" key={label}>
          <div className="info-key">{label}</div>
          <div className={`info-value${mono ? ' info-mono' : ''}`}>{value}</div>
        </div>
      ))}
      {boolItems.map(({ label, value }) => (
        <div className="info-item" key={label}>
          <div className="info-key">{label}</div>
          {yesNo(value)}
        </div>
      ))}
      <div className="info-item">
        <div className="info-key">Ownership renounced</div>
        {yesNo(renounced)}
      </div>
      <div className="info-item">
        <div className="info-key">Trading restrictions</div>
        <div className="info-value">{deriveTradingRestrictions(ns)}</div>
      </div>
    </div>
  );
}
