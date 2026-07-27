import { useState } from 'react';
import { Braces, CheckCircle2, ChevronDown, Copy, ExternalLink, FileJson, Layers, ShieldCheck, Terminal } from 'lucide-react';
import Button from '../components/Button';
import Card from '../components/Card';
import './Docs.css';

const API_BASE_URL = 'https://crypto-due-diligence-api.onrender.com';

const endpoints = [
  { title: 'Health & service status', method: 'GET', path: '/', description: 'Check that the API is reachable.', request: 'GET /', response: { status: 'ok', service: 'crypto-due-diligence-api' }, codes: ['200 OK'] },
  { title: 'Service health', method: 'GET', path: '/health', description: 'Confirm the health endpoint responds successfully.', request: 'GET /health', response: { status: 'healthy' }, codes: ['200 OK'] },
  { title: 'Supported chains', method: 'GET', path: '/chains', description: 'Read network metadata and supported operations.', request: 'GET /chains', response: { chains: [{ key: 'ethereum', id: 1, name: 'Ethereum', family: 'evm', token_security: true }, { key: 'arbitrum', id: 42161, name: 'Arbitrum', family: 'evm', token_security: true }, { key: 'optimism', id: 10, name: 'Optimism', family: 'evm', token_security: true }, { key: 'base', id: 8453, name: 'Base', family: 'evm', token_security: true }, { key: 'linea', id: 59144, name: 'Linea', family: 'evm', token_security: true }, { key: 'scroll', id: 534352, name: 'Scroll', family: 'evm', token_security: true }, { key: 'zksync-era', id: 324, name: 'zkSync Era', family: 'evm', token_security: true }, { key: 'bnb-chain', id: 56, name: 'BNB Chain', family: 'evm', token_security: true }, { key: 'opbnb', id: 204, name: 'opBNB', family: 'evm', token_security: true }, { key: 'polygon', id: 137, name: 'Polygon', family: 'evm', token_security: true }, { key: 'avalanche-c-chain', id: 43114, name: 'Avalanche C-Chain', family: 'evm', token_security: true }, { key: 'cronos', id: 25, name: 'Cronos', family: 'evm', token_security: true }, { key: 'mantle', id: 5000, name: 'Mantle', family: 'evm', token_security: true }, { key: 'gnosis', id: 100, name: 'Gnosis', family: 'evm', token_security: true }, { key: 'xlayer', id: 196, name: 'X Layer', family: 'evm', token_security: true }, { key: 'solana', id: null, name: 'Solana', family: 'solana' }] }, codes: ['200 OK'] },
  { title: 'Wallet analysis', method: 'POST', path: '/analyze/wallet', description: 'Run a live wallet-intelligence scan for a valid EVM or Solana address.', request: { address: '0x28ec3f0ba70df3f8ba0ed9ee6dfde86791688c22' }, response: { status: 'success', address: '0x28ec3f0ba70df3f8ba0ed9ee6dfde86791688c22', chain_type: 'evm', portfolio_score: 62, risk_level: 'Medium', assets: [], transactions: [] }, codes: ['200 OK', '400 Invalid Request', '422 Validation Error', '502 Provider Unavailable'] },
  { title: 'EVM token risk analysis', method: 'POST', path: '/analyze/token', description: 'Analyze a token on a selected provider-supported EVM network. A 0x address does not identify its own chain.', request: { chain_type: 'evm', chain_id: 1, address: '0xdAC17F958D2ee523a2206206994597C13D831ec7' }, response: { token_name: 'Tether USD', token_symbol: 'USDT', chain_type: 'evm', network: 'ethereum', chain_id: 1, risk_score: 35, risk_level: 'Low', confidence: 0.92, triggered_rules: [] }, codes: ['200 OK', '404 Not Found', '422 Validation Error', '502 Provider Unavailable'] },
  { title: 'X Layer token risk analysis', method: 'POST', path: '/analyze/token', description: 'Use the EVM route with X Layer’s explicit GoPlus chain ID (196).', request: { chain_type: 'evm', chain_id: 196, address: '0x0000000000000000000000000000000000000000' }, response: { network: 'xlayer', chain_type: 'evm', chain_id: 196 }, codes: ['200 OK', '404 Not Found', '502 Bad Gateway'] },
  { title: 'Solana token risk analysis', method: 'POST', path: '/analyze/token', description: 'Analyze a Solana SPL mint through the separate Solana provider path.', request: { chain_type: 'solana', address: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' }, response: { network: 'solana', chain_type: 'solana', chain_id: null }, codes: ['200 OK', '404 Not Found', '422 Validation Error', '502 Provider Unavailable'] },
  { title: 'Raw GoPlus token debug', method: 'GET', path: '/analyze/token/raw', description: 'Return the raw EVM provider response for debugging and schema inspection.', request: 'GET /analyze/token/raw?chain_id=1&address=0xdAC17F958D2ee523a2206206994597C13D831ec7', response: { note: 'Raw provider response varies by token and network.' }, codes: ['200 OK', '400 Bad Request', '502 Bad Gateway'] },
];

const endpointGroups = [
  { title: 'Wallet Intelligence', description: 'Live address-based portfolio and risk summaries.', icon: Layers, endpoints: [endpoints[3]] },
  { title: 'Token Intelligence', description: 'Provider-backed token-security analysis across selected networks.', icon: ShieldCheck, endpoints: endpoints.slice(4, 8) },
  { title: 'Network Discovery', description: 'Configured networks and their analysis capabilities.', icon: FileJson, endpoints: [endpoints[2]] },
  { title: 'System', description: 'Service reachability and health checks.', icon: Terminal, endpoints: endpoints.slice(0, 2) },
];

const groupId = title => title.toLowerCase().replace(/\s+/g, '-');
const pretty = value => JSON.stringify(value, null, 2);

function EndpointCard({ endpoint, copiedId, onCopy }) {
  const endpointId = `${endpoint.method.toLowerCase()}-${endpoint.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
  return <details id={endpointId} className="docs-endpoint-card">
    <summary>
      <span className={`docs-badge docs-badge-${endpoint.method.toLowerCase()}`}>{endpoint.method}</span>
      <span className="docs-endpoint-summary-copy"><code>{endpoint.path}</code><span>{endpoint.title} — {endpoint.description}</span></span>
      <ChevronDown className="docs-endpoint-chevron" size={18} />
    </summary>
    <div className="docs-endpoint-detail">
      <div className="docs-endpoint-meta"><span className="docs-meta-label">Request</span><code>{typeof endpoint.request === 'string' ? endpoint.request : `${endpoint.method} ${endpoint.path}`}</code></div>
      {typeof endpoint.request === 'object' && <CodeBlock label="Request body" value={endpoint.request} copyId={`req-${endpointId}`} copiedId={copiedId} onCopy={onCopy} />}
      <CodeBlock label="Response" value={endpoint.response} copyId={`resp-${endpointId}`} copiedId={copiedId} onCopy={onCopy} />
      <div className="docs-endpoint-codes"><span className="docs-meta-label">Status codes</span><span>{endpoint.codes.join(' · ')}</span></div>
    </div>
  </details>;
}

function CodeBlock({ label, value, copyId, copiedId, onCopy }) {
  const valueText = pretty(value);
  return <div className="docs-code-block"><div><span className="docs-meta-label">{label}</span><Button variant="secondary" onClick={() => onCopy(valueText, copyId)}>{copiedId === copyId ? 'Copied' : <><Copy size={13} /> Copy</>}</Button></div><pre>{valueText}</pre></div>;
}

export default function Docs() {
  const [copiedId, setCopiedId] = useState('');
  const handleCopy = async (text, id) => { try { await navigator.clipboard.writeText(text); setCopiedId(id); window.setTimeout(() => setCopiedId(''), 1600); } catch { setCopiedId(''); } };

  return <div className="docs-page">
    <section className="docs-hero">
      <div className="docs-hero-copy"><div className="docs-eyelet"><Braces size={14} /> API v1.0</div><h1>Build with Crypto Due Diligence</h1><p>Inspect supported networks, submit wallet reviews, and request explainable token-security analysis from the same FastAPI backend used by the product.</p><div className="docs-hero-actions"><a className="docs-action docs-action-primary" href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">Open Swagger UI <ExternalLink size={15} /></a><Button variant="secondary" onClick={() => handleCopy(API_BASE_URL, 'base-url')}>{copiedId === 'base-url' ? 'Copied' : 'Copy Base URL'}</Button></div></div>
      <Card className="docs-hero-card"><div className="docs-hero-card-top"><span>Configured base URL</span><CheckCircle2 size={18} /></div><code>{API_BASE_URL}</code><div className="docs-hero-meta"><div><small>Content type</small><strong>application/json</strong></div><div><small>Authentication</small><strong>Not required</strong></div><div><small>Networks</small><strong>15 EVM + Solana</strong></div></div></Card>
    </section>

    <section className="docs-quickstart"><div><span>QUICK START</span><h2>Analyze a selected EVM contract</h2><p>Supply both the EVM family and the selected chain ID. A 0x address cannot identify its own network.</p></div><CodeBlock label="POST /analyze/token" value={{ chain_type: 'evm', chain_id: 1, address: '0xdAC17F958D2ee523a2206206994597C13D831ec7' }} copyId="quick-start" copiedId={copiedId} onCopy={handleCopy} /></section>

    <nav className="docs-nav-card" aria-label="Documentation sections"><span>REFERENCE INDEX</span>{endpointGroups.map(group => <a key={group.title} href={`#${groupId(group.title)}`}>{group.title}</a>)}</nav>

    <section className="docs-sections">{endpointGroups.map(group => { const Icon = group.icon; return <section id={groupId(group.title)} className="docs-section" key={group.title}><div className="docs-section-heading"><div className="docs-section-icon"><Icon size={19} /></div><div><h2>{group.title}</h2><p>{group.description}</p></div></div><div className="docs-section-content">{group.endpoints.map(endpoint => <EndpointCard key={`${endpoint.title}-${endpoint.path}`} endpoint={endpoint} copiedId={copiedId} onCopy={handleCopy} />)}</div></section>; })}</section>

    <section className="docs-notes"><div className="docs-notes-heading"><FileJson size={20} /><div><span>DEVELOPER NOTES</span><h2>Formats and error handling</h2></div></div><div className="docs-notes-grid"><div><h3>Network routing</h3><p>EVM requests require <code>chain_type: "evm"</code> and a provider-supported <code>chain_id</code>; X Layer is <code>196</code>. Solana uses <code>chain_type: "solana"</code>.</p></div><div><h3>Response handling</h3><p>Successful responses are JSON. Handle <code>400</code>, <code>404</code>, <code>422</code>, and <code>502</code> explicitly; provider fields that are unavailable are not safe findings.</p></div></div></section>
  </div>;
}
