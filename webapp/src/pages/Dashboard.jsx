import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, Download, RotateCw, ExternalLink } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import RiskGauge from '../components/dashboard/RiskGauge';
import RiskBadge from '../components/dashboard/RiskBadge';
import ConfidenceBar from '../components/dashboard/ConfidenceBar';
import ScoreBreakdownChart from '../components/dashboard/ScoreBreakdownChart';
import SignalList from '../components/dashboard/SignalList';
import InfoGrid from '../components/dashboard/InfoGrid';
import { fetchChains, analyzeToken, ADDRESS_RE } from '../api/client';
import './Dashboard.css';

const LOADING_MESSAGES = [
  'Checking ownership…',
  'Inspecting liquidity…',
  'Analyzing holder concentration…',
  'Calculating deterministic score…',
  'Generating AI explanation…',
];

// Verified explorer domains per chain — same mapping validated for the
// vanilla frontend (Mantle/opBNB run their own explorer, X Layer uses OKLink).
const EXPLORERS = {
  1: 'https://etherscan.io/address/', 56: 'https://bscscan.com/address/',
  137: 'https://polygonscan.com/address/', 42161: 'https://arbiscan.io/address/',
  10: 'https://optimistic.etherscan.io/address/', 8453: 'https://basescan.org/address/',
  43114: 'https://snowtrace.io/address/', 324: 'https://explorer.zksync.io/address/',
  59144: 'https://lineascan.build/address/', 534352: 'https://scrollscan.com/address/',
  5000: 'https://mantlescan.xyz/address/', 204: 'https://opbnbscan.com/address/',
  196: 'https://www.oklink.com/xlayer/address/', 25: 'https://cronoscan.com/address/',
  100: 'https://gnosisscan.io/address/',
};

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [chains, setChains] = useState([]);
  const [chainId, setChainId] = useState(searchParams.get('chain') || '1');
  const [addressInput, setAddressInput] = useState(searchParams.get('address') || '');
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [duration, setDuration] = useState(null);

  useEffect(() => {
    fetchChains().then(d => setChains(d.chains || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (status !== 'loading') return;
    setLoadingMsgIndex(0);
    const interval = setInterval(() => {
      setLoadingMsgIndex(i => (i + 1) % LOADING_MESSAGES.length);
    }, 1000);
    return () => clearInterval(interval);
  }, [status]);

  const runAnalysis = useCallback(async (chain, address) => {
    if (!ADDRESS_RE.test(address)) {
      setStatus('error');
      setErrorMsg('Invalid contract address — must be 0x followed by 40 hex characters.');
      return;
    }
    setStatus('loading');
    setErrorMsg('');
    const start = performance.now();
    try {
      const data = await analyzeToken(Number(chain), address);
      setResult(data);
      setDuration(((performance.now() - start) / 1000).toFixed(2));
      setStatus('success');
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Unable to analyze this contract.');
    }
  }, []);

  // Auto-run if the page was opened with query params (e.g. from Home)
  useEffect(() => {
    const chain = searchParams.get('chain');
    const address = searchParams.get('address');
    if (chain && address && ADDRESS_RE.test(address)) {
      runAnalysis(chain, address);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    setSearchParams({ chain: chainId, address: addressInput.trim() });
    runAnalysis(chainId, addressInput.trim());
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

  const groupedChains = chains.reduce((acc, c) => {
    (acc[c.ecosystem] ||= []).push(c);
    return acc;
  }, {});
  const chainName = chains.find(c => String(c.id) === String(chainId))?.name;

  return (
    <div className="dashboard">

      {/* ── Address input — always available so this page works when visited directly ── */}
      <Card className="dashboard-input-card">
        <form onSubmit={handleSubmit} className="dashboard-input-row">
          <select value={chainId} onChange={e => setChainId(e.target.value)} className="dashboard-select" aria-label="Blockchain">
            {Object.entries(groupedChains).map(([eco, list]) => (
              <optgroup key={eco} label={eco}>
                {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
            ))}
          </select>
          <input
            type="text"
            className="dashboard-address-input"
            placeholder="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
          />
          <Button type="submit" variant="primary" loading={status === 'loading'}>Analyze</Button>
        </form>
      </Card>

      {/* ── Empty state ── */}
      {status === 'idle' && (
        <Card className="dashboard-empty">
          <p>No analysis available. Paste a contract address above to begin.</p>
        </Card>
      )}

      {/* ── Loading state ── */}
      {status === 'loading' && (
        <Card className="dashboard-loading">
          <div className="dashboard-loading-spinner" />
          <p>{LOADING_MESSAGES[loadingMsgIndex]}</p>
        </Card>
      )}

      {/* ── Error state ── */}
      {status === 'error' && (
        <Card className="dashboard-error">
          <div className="dashboard-error-title"><AlertCircle size={18} /> Unable to analyze this contract</div>
          <ul className="dashboard-error-reasons">
            <li>Invalid contract address for the selected chain</li>
            <li>Wrong blockchain selected for this token</li>
            <li>Token not supported, or GoPlus returned no data</li>
          </ul>
          <p className="dashboard-error-detail">{errorMsg}</p>
          <Button variant="secondary" onClick={() => runAnalysis(chainId, addressInput.trim())}>
            <RotateCw size={14} /> Retry
          </Button>
        </Card>
      )}

      {/* ── Success — full report ── */}
      {status === 'success' && result && (
        <>
          <Card className="dashboard-summary-card">
            <div className="dashboard-summary-header">
              <RiskGauge score={result.risk_score} riskLevel={result.risk_level} />
              <div className="dashboard-summary-meta">
                <h2>{result.token_name || 'Unknown token'}</h2>
                <span className="dashboard-symbol">{result.token_symbol ? `$${result.token_symbol}` : ''}</span>
                <div className="dashboard-badge-row"><RiskBadge riskLevel={result.risk_level} /></div>
              </div>
            </div>

            <ConfidenceBar
              confidence={result.confidence}
              known={result.confidence_known_signals}
              total={result.confidence_total_signals}
            />

            <div className="dashboard-action-row">
              <Button variant="secondary" onClick={downloadJson}><Download size={14} /> Export JSON</Button>
              {EXPLORERS[chainId] && (
                <a
                  className="btn btn-secondary"
                  href={EXPLORERS[chainId] + addressInput.trim()}
                  target="_blank" rel="noopener noreferrer"
                >
                  View on explorer <ExternalLink size={14} />
                </a>
              )}
              {duration && <span className="dashboard-duration">Completed in {duration}s</span>}
            </div>
          </Card>

          <Card>
            <h3 className="dashboard-section-title">AI executive summary</h3>
            <p className="dashboard-verdict">{result.summary}</p>
          </Card>

          <Card>
            <h3 className="dashboard-section-title">Score breakdown</h3>
            <ScoreBreakdownChart triggeredRules={result.triggered_rules} />
          </Card>

          <div className="dashboard-signal-grid">
            <Card>
              <h3 className="dashboard-section-title">Warning signals</h3>
              <SignalList variant="warning" items={(result.triggered_rules || []).map(r => r.reason)} />
            </Card>
            <Card>
              <h3 className="dashboard-section-title">Positive signals</h3>
              <SignalList
                variant="positive"
                items={[
                  ...(result.positive_signals || []),
                  ...((result.not_triggered_rules || []).map(r => r.reason)),
                ]}
              />
            </Card>
          </div>

          <Card>
            <h3 className="dashboard-section-title">Recommended checks</h3>
            <ol className="dashboard-checks">
              {(result.recommended_checks || []).map((c, i) => <li key={i}>{c}</li>)}
            </ol>
          </Card>

          <Card>
            <h3 className="dashboard-section-title">Technical details</h3>
            <InfoGrid
              normalizedSignals={result.normalized_signals}
              technicalData={result.technical_data}
              chainName={chainName}
              address={addressInput.trim()}
            />
            <details className="dashboard-raw">
              <summary>Raw GoPlus response</summary>
              <pre>{JSON.stringify(result.technical_data, null, 2)}</pre>
            </details>
          </Card>
        </>
      )}
    </div>
  );
}
