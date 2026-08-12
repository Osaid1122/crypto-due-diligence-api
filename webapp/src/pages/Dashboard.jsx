import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, ChevronRight, CircleDollarSign, Code2, Download, ExternalLink, FileSearch, Layers3, LoaderCircle, LockKeyhole, RotateCw, ScanLine, ShieldAlert, ShieldCheck, Sparkles, Users, WandSparkles } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import ChainLogo from '../components/ChainLogo';
import RiskGauge from '../components/dashboard/RiskGauge';
import RiskBadge from '../components/dashboard/RiskBadge';
import ConfidenceBar from '../components/dashboard/ConfidenceBar';
import ScoreBreakdownChart from '../components/dashboard/ScoreBreakdownChart';
import SignalList from '../components/dashboard/SignalList';
import InfoGrid from '../components/dashboard/InfoGrid';
import SecurityRadar from '../components/dashboard/SecurityRadar';
import { analyzeToken } from '../api/client';
import ChainSelector, { addressPlaceholder, isValidAddress } from '../components/ChainSelector';
import { getNetwork, isNetworkKey } from '../config/networks';
import './Dashboard.css';

const ANALYSIS_STEPS = ['Contract Found', 'Reading Metadata', 'Checking Ownership', 'Checking Liquidity', 'Running AI Analysis', 'Generating Recommendations'];

// Severity ordering mirrors the backend (Critical > High > Medium > Low >
// Informational). Used only to pick the WORST triggered finding to surface —
// never to compute a risk level, which is always the backend's `risk_level`.
const SEVERITY_RANK = { Critical: 4, High: 3, Medium: 2, Low: 1, Informational: 0 };

// The single most severe triggered rule's reason. triggered_rules arrives in
// rule-declaration order, not severity order, so [0] can be a mild finding while
// a Critical one sits later; pick by severity so the headline concern is the
// worst one, never whichever happened to be listed first.
function mostSevereConcern(triggeredRules) {
  const rules = Array.isArray(triggeredRules) ? triggeredRules : [];
  let worst = null;
  for (const rule of rules) {
    const rank = SEVERITY_RANK[rule?.severity] ?? 0;
    if (!worst || rank > worst.rank) worst = { rank, reason: rule?.reason };
  }
  return worst?.reason || null;
}

function signalValue(value) {
  if (value === true) return { label: 'Detected', tone: 'warning' };
  if (value === false) return { label: 'Clear', tone: 'positive' };
  return { label: 'Unknown', tone: 'neutral' };
}

function KPI({ icon: Icon, label, value, tone = 'neutral' }) {
  return <div className={`dashboard-kpi dashboard-kpi--${tone}`}><div className="dashboard-kpi-icon"><Icon size={16} /></div><div><span>{label}</span><strong><i />{value}</strong></div></div>;
}

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [chainType, setChainType] = useState(isNetworkKey(searchParams.get('chain_type')) ? searchParams.get('chain_type') : 'ethereum');
  const [addressInput, setAddressInput] = useState(searchParams.get('address') || '');
  const [status, setStatus] = useState('idle');
  const [analysisStep, setAnalysisStep] = useState(0);
  const [revealedSections, setRevealedSections] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [duration, setDuration] = useState(null);

  useEffect(() => {
    if (status !== 'loading') return;
    setAnalysisStep(0);
    const interval = setInterval(() => setAnalysisStep(i => Math.min(i + 1, ANALYSIS_STEPS.length - 1)), 580);
    return () => clearInterval(interval);
  }, [status]);

  useEffect(() => {
    if (status !== 'success' || !result) return;
    setAnalysisStep(ANALYSIS_STEPS.length - 1);
    setRevealedSections(0);
    const timers = [0, 220, 460, 700, 940, 1180].map((delay, index) => setTimeout(() => setRevealedSections(index + 1), delay));
    return () => timers.forEach(clearTimeout);
  }, [status, result]);

  const runAnalysis = useCallback(async (chain, address) => {
    if (!isValidAddress(chain, address)) {
      setStatus('error');
      setErrorMsg(chain === 'solana' ? 'Invalid Solana mint address.' : `Invalid ${getNetwork(chain).label} address — must be 0x followed by 40 hex characters.`);
      return;
    }
    setStatus('loading');
    setRevealedSections(0);
    setErrorMsg('');
    const start = performance.now();
    try {
      const data = await analyzeToken(chain, address);
      setResult(data);
      setDuration(((performance.now() - start) / 1000).toFixed(2));
      setStatus('success');
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Unable to analyze this contract.');
    }
  }, []);

  useEffect(() => {
    const chain = isNetworkKey(searchParams.get('chain_type')) ? searchParams.get('chain_type') : 'ethereum';
    const address = searchParams.get('address');
    if (address && isValidAddress(chain, address)) runAnalysis(chain, address);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    setSearchParams({ chain_type: chainType, address: addressInput.trim() });
    runAnalysis(chainType, addressInput.trim());
  }

  function downloadJson() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.token_symbol || 'token'}-due-diligence-report.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const resultNetwork = getNetwork(result?.network || chainType);
  const chainName = resultNetwork.label;
  const ns = result?.normalized_signals || {};
  const td = result?.technical_data || {};
  const confidencePct = Math.round((result?.confidence || 0) * 100);
  const explorerUrl = resultNetwork.explorer + addressInput.trim();
  const kpis = result ? [
    { icon: Users, label: 'Holder count', value: td.holder_count ? Number(td.holder_count).toLocaleString() : 'Unknown', tone: 'info' },
    { icon: CircleDollarSign, label: 'Largest holder', value: ns.top_holder_percent != null ? `${ns.top_holder_percent.toFixed(1)}%` : 'Unknown', tone: ns.top_holder_percent > 25 ? 'warning' : 'positive' },
    { icon: Code2, label: 'Source verified', value: ns.is_open_source === true ? 'Verified' : ns.is_open_source === false ? 'Not verified' : 'Unknown', tone: ns.is_open_source === true ? 'positive' : ns.is_open_source === false ? 'warning' : 'neutral' },
    { icon: Layers3, label: 'Proxy contract', value: ns.is_proxy === true ? 'Upgradeable' : ns.is_proxy === false ? 'None detected' : 'Unknown', tone: signalValue(ns.is_proxy).tone },
    { icon: WandSparkles, label: 'Mint authority', value: ns.is_mintable === true ? 'Active' : ns.is_mintable === false ? 'Disabled' : 'Unknown', tone: signalValue(ns.is_mintable).tone },
    { icon: LockKeyhole, label: 'Blacklist capability', value: ns.is_blacklisted === true ? 'Enabled' : ns.is_blacklisted === false ? 'None detected' : 'Unknown', tone: signalValue(ns.is_blacklisted).tone },
  ] : [];

  return <div className="dashboard">
    <Card className="dashboard-input-card">
      <form onSubmit={handleSubmit} className="dashboard-input-row">
        <ChainSelector value={chainType} onChange={setChainType} />
        <input type="text" className="dashboard-address-input" placeholder={addressPlaceholder(chainType)} value={addressInput} onChange={e => setAddressInput(e.target.value)} />
        <Button type="submit" variant="primary" loading={status === 'loading'}>Analyze</Button>
      </form>
    </Card>

    {status === 'idle' && <Card className="dashboard-empty"><div className="dashboard-empty-icon"><ShieldCheck size={34} /></div><h2>Ready for a security review</h2><p>Paste a contract address to begin analysis.</p><span>On-chain signals, risk scoring, and AI guidance in one workspace.</span></Card>}

    {status === 'loading' && <div className="dashboard-loading-workspace" aria-live="polite"><Card className="dashboard-live-analysis"><div className="dashboard-live-heading"><div className="dashboard-live-icon"><ScanLine size={19} /></div><div><span className="dashboard-live-eyebrow">LIVE ANALYSIS</span><h2>Inspecting token security</h2></div><span className="dashboard-live-count">{analysisStep + 1} / {ANALYSIS_STEPS.length}</span></div><div className="dashboard-analysis-progress"><i style={{ width: `${((analysisStep + 1) / ANALYSIS_STEPS.length) * 100}%` }} /></div><div className="dashboard-live-steps">{ANALYSIS_STEPS.map((step, index) => { const complete = index < analysisStep; const active = index === analysisStep; return <div className={`dashboard-live-step ${complete ? 'is-complete' : ''} ${active ? 'is-active' : ''}`} key={step}><span className="dashboard-live-marker">{complete ? <CheckCircle2 size={17} /> : active ? <LoaderCircle size={17} /> : <span />}</span><span>{step}</span></div>; })}</div></Card><div className="dashboard-skeleton-grid" aria-hidden="true"><span /><span /><span /><span /></div></div>}

    {status === 'error' && <Card className="dashboard-error"><div className="dashboard-error-title"><AlertCircle size={18} /> Unable to analyze this contract</div><ul className="dashboard-error-reasons"><li>Invalid contract address for the selected chain</li><li>Wrong blockchain selected for this token</li><li>Token not supported, or GoPlus returned no data</li></ul><p className="dashboard-error-detail">{errorMsg}</p><Button variant="secondary" onClick={() => runAnalysis(chainType, addressInput.trim())}><RotateCw size={14} /> Retry</Button></Card>}

    {status === 'success' && result && <><div className="dashboard-analysis-complete" aria-live="polite"><CheckCircle2 size={16} /> Analysis complete — security report ready</div>
      {revealedSections >= 1 && <Card className="dashboard-summary-card dashboard-reveal"><div className="dashboard-hero-grid"><RiskGauge score={result.risk_score} riskLevel={result.risk_level} /><div className="dashboard-summary-meta"><div className="dashboard-token-heading"><div className="dashboard-token-logo"><ChainLogo chain={resultNetwork.key} size={28} /></div><div><span className="dashboard-overline">Token intelligence report</span><h2>{result.token_name || 'Unknown token'}</h2><span className="dashboard-symbol">{result.token_symbol ? `$${result.token_symbol}` : 'Symbol unavailable'}</span></div></div><div className="dashboard-badge-row"><RiskBadge riskLevel={result.risk_level} /><span className="dashboard-chain-badge"><ChainLogo chain={resultNetwork.key} size={14} /> {chainName}</span></div></div><div className="dashboard-hero-side"><div><span>Confidence</span><strong>{confidencePct}%</strong></div><div><span>Analysis time</span><strong>{duration ? `${duration}s` : '—'}</strong></div></div></div><ConfidenceBar confidence={result.confidence} known={result.confidence_known_signals} total={result.confidence_total_signals} /><div className="dashboard-action-row"><Button className="dashboard-export-button" variant="secondary" onClick={downloadJson}><Download size={14} /> Export JSON</Button><a className="btn btn-secondary dashboard-explorer-button" href={explorerUrl} target="_blank" rel="noopener noreferrer" aria-label="View token on blockchain explorer" title="View on explorer"><ExternalLink size={16} /></a></div></Card>}
      <div className="dashboard-workspace"><main className="dashboard-primary-column">
        {revealedSections >= 2 && <Card className="dashboard-ai-summary dashboard-reveal"><div className="dashboard-ai-heading"><div><Sparkles size={18} /><span>AI verdict</span></div><span className="dashboard-ai-verdict">{result.risk_level} risk</span></div><div className="dashboard-verdict-grid"><div className="dashboard-verdict-primary"><span>Assessment</span><strong>This token appears {String(result.risk_level || 'unknown').toLowerCase()} risk.</strong><p>{result.summary}</p></div><div className="dashboard-verdict-facts"><div><span>Confidence</span><strong>{confidencePct}%</strong></div><div><span>Max severity</span><strong>{result.max_severity && result.max_severity !== 'None' ? result.max_severity : 'None detected'}</strong></div><div><span>Main concern</span><strong>{mostSevereConcern(result.triggered_rules) || 'No material risk signal detected.'}</strong></div><div><span>Recommendation</span><strong>{result.recommended_checks?.[0] || (result.risk_level === 'Low' ? 'Safe for routine monitoring.' : 'Review before interacting.')}</strong></div></div></div></Card>}
        {revealedSections >= 3 && <div className="dashboard-kpi-grid dashboard-reveal">{kpis.map(kpi => <KPI key={kpi.label} {...kpi} />)}</div>}
        {revealedSections >= 5 && <Card className="dashboard-recommendations dashboard-reveal"><div className="dashboard-section-heading"><div><h3 className="dashboard-section-title">Recommended actions</h3><p>Suggested next checks based on the detected security signals.</p></div><FileSearch size={19} /></div><ol className="dashboard-checks">{(result.recommended_checks || []).map((c, i) => <li key={i}><CheckCircle2 size={17} /><span>{c}</span><ChevronRight size={16} /></li>)}</ol></Card>}
        {revealedSections >= 6 && <Card className="dashboard-technical dashboard-reveal"><div className="dashboard-section-heading"><div><h3 className="dashboard-section-title">Technical details</h3><p>Contract and permission signals returned by the analysis provider.</p></div><Code2 size={19} /></div><InfoGrid normalizedSignals={result.normalized_signals} technicalData={result.technical_data} chainName={chainName} address={addressInput.trim()} /><details className="dashboard-raw"><summary>Raw GoPlus response</summary><pre>{JSON.stringify(result.technical_data, null, 2)}</pre></details></Card>}
      </main><aside className="dashboard-secondary-column">
        {revealedSections >= 3 && <Card className="dashboard-radar-card dashboard-reveal"><h3 className="dashboard-section-title">Security posture</h3><p className="dashboard-card-caption">Risk resistance across key on-chain dimensions.</p><SecurityRadar triggeredRules={result.triggered_rules} /></Card>}
        {revealedSections >= 3 && <Card className="dashboard-breakdown-card dashboard-reveal"><h3 className="dashboard-section-title">Risk breakdown</h3><ScoreBreakdownChart triggeredRules={result.triggered_rules} /></Card>}
        {revealedSections >= 4 && <Card className="dashboard-signals-card dashboard-reveal"><div className="dashboard-signal-section dashboard-signal-section--warning"><div className="dashboard-signal-heading"><div><ShieldAlert size={17} /><h3 className="dashboard-section-title">Warning signals</h3></div><span>{(result.triggered_rules || []).length}</span></div><SignalList variant="warning" items={(result.triggered_rules || []).map(r => r.reason)} /></div><div className="dashboard-signal-section dashboard-signal-section--positive"><div className="dashboard-signal-heading is-positive"><div><ShieldCheck size={17} /><h3 className="dashboard-section-title">Positive signals</h3></div><span>{(result.positive_signals || []).length + (result.not_triggered_rules || []).length}</span></div><SignalList variant="positive" items={[...(result.positive_signals || []), ...((result.not_triggered_rules || []).map(r => r.reason))]} /></div></Card>}
      </aside></div>
    </>}
  </div>;
}
