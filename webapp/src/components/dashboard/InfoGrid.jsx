import { ChevronDown } from 'lucide-react';
import { deriveOwnershipRenounced, deriveTradingRestrictions } from '../../utils/derived';
import './InfoGrid.css';

function value(v, mono = false) {
  if (v === true) return <span className="info-value info-yes">Enabled</span>;
  if (v === false) return <span className="info-value info-no">Not detected</span>;
  if (v === undefined || v === null || v === '') return <span className="info-value info-unknown">Unknown</span>;
  return <span className={`info-value${mono ? ' info-mono' : ''}`}>{v}</span>;
}

function Group({ title, items, open = false }) {
  return <details className="info-group" open={open}><summary><span>{title}</span><ChevronDown size={16} /></summary><div className="info-grid">{items.map(({ label, data, mono }) => <div className="info-item" key={label}><span className="info-key">{label}</span>{value(data, mono)}</div>)}</div></details>;
}

export default function InfoGrid({ normalizedSignals = {}, technicalData = {}, chainName, address }) {
  const ns = normalizedSignals;
  const td = technicalData;
  return <div className="info-groups">
    <Group open title="Contract information" items={[{ label: 'Chain', data: chainName }, { label: 'Contract address', data: address, mono: true }, { label: 'Holder count', data: td.holder_count ? Number(td.holder_count).toLocaleString() : null }, { label: 'Liquidity positions', data: ns.lp_position_count }]} />
    <Group title="Ownership" items={[{ label: 'Ownership renounced', data: deriveOwnershipRenounced(td.owner_address) }, { label: 'Owner / creator holds', data: ns.insider_percent != null ? `${ns.insider_percent.toFixed(1)}%` : null }, { label: 'Largest holder', data: ns.top_holder_percent != null ? `${ns.top_holder_percent.toFixed(1)}%` : null }]} />
    <Group title="Liquidity" items={[{ label: 'LP positions', data: ns.lp_position_count }, { label: 'Largest LP holder', data: ns.top_lp_holder_percent != null ? `${ns.top_lp_holder_percent.toFixed(1)}%` : null }]} />
    <Group title="Permissions" items={[{ label: 'Mint authority', data: ns.is_mintable }, { label: 'Blacklist capability', data: ns.is_blacklisted }, { label: 'Proxy contract', data: ns.is_proxy }, { label: 'Trading restrictions', data: deriveTradingRestrictions(ns) }]} />
    <Group title="Verification" items={[{ label: 'Source code verified', data: ns.is_open_source }, { label: 'Trust list', data: ns.trust_list }]} />
  </div>;
}
