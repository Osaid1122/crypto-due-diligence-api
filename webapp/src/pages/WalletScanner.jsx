import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, Download, LoaderCircle, Package, RefreshCw, Search, ShieldCheck, Sparkles, TrendingUp, Copy } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import Card from '../components/Card';
import Button from '../components/Button';
import { analyzeWallet } from '../api/client';
import { exportJsonReport, exportPdfReport } from '../utils/reportExport';
import './WalletScanner.css';

const WORKFLOW_STEPS = [
  'Address validated',
  'Detecting blockchain',
  'Fetching assets',
  'Fetching token metadata',
  'Running AI analysis',
  'Calculating portfolio score',
  'Generating AI summary',
];

// Severity ordering mirrors the backend (Critical > High > Medium > Low). Used
// to rank assets severity-first so a Critical holding is never ordered below a
// lower-severity one just because it carries a smaller numeric score.
const RISK_RANK = { Critical: 4, High: 3, Medium: 2, Low: 1 };

function formatCurrency(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(value) {
  if (!value) return 'Unknown';
  const timestamp = Number(value);
  if (Number.isNaN(timestamp)) return String(value);
  return new Date(timestamp * 1000).toLocaleString();
}

function formatTimelineDate(value) {
  if (!value) return 'Time unavailable';
  const timestamp = Number(value);
  if (Number.isNaN(timestamp)) return String(value);
  const date = new Date(timestamp * 1000);
  return `${date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} ${date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}`;
}

function truncateMiddle(value, maxLength) {
  if (!value || value.length <= maxLength) return value;
  const half = Math.floor((maxLength - 3) / 2);
  return `${value.slice(0, half)}...${value.slice(-half)}`;
}

function parseWalletRoute(location) {
  const path = location.pathname || '';
  const match = path.match(/^\/wallet\/(.+)$/);
  if (!match) return null;
  return decodeURIComponent(match[1]);
}

export default function WalletScanner() {
  const location = useLocation();
  const navigate = useNavigate();
  const initialAddress = useMemo(() => parseWalletRoute(location), [location]);
  const [addressInput, setAddressInput] = useState(initialAddress || '');
  const [status, setStatus] = useState(initialAddress ? 'loading' : 'idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [tokenSearch, setTokenSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [progressIndex, setProgressIndex] = useState(0);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (status !== 'loading') return undefined;
    const interval = setInterval(() => {
      setProgressIndex((prev) => (prev + 1) % WORKFLOW_STEPS.length);
    }, 700);
    return () => clearInterval(interval);
  }, [status]);

  useEffect(() => {
    if (status !== 'loading' && status !== 'error') return undefined;
    const timeout = setTimeout(() => {
      if (status === 'loading') {
        setProgressIndex(WORKFLOW_STEPS.length - 1);
      }
    }, 4500);
    return () => clearTimeout(timeout);
  }, [status]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(''), 4200);
    return () => clearTimeout(timer);
  }, [notice]);

  function normalizeAnalysisResponse(response) {
    if (response == null) {
      return { ok: false, state: 'EMPTY', error: 'No portfolio data returned.' };
    }

    if (typeof response === 'string') {
      const trimmed = response.trim();
      return { ok: false, state: 'ERROR', error: trimmed || 'No portfolio data returned.' };
    }

    if (typeof response !== 'object') {
      return { ok: false, state: 'EMPTY', error: 'No portfolio data returned.' };
    }

    if (response.status === 'error' || response.error || response.detail) {
      const message = response.summary || response.detail || response.error?.message || response.error || 'The wallet analysis failed.';
      return { ok: false, state: 'ERROR', error: message };
    }

    const hasPortfolio = Boolean(
      response.summary ||
      response.portfolio_score != null ||
      response.risk_score != null ||
      (Array.isArray(response.assets) && response.assets.length) ||
      (Array.isArray(response.risk_breakdown) && response.risk_breakdown.length) ||
      response.detail_metrics
    );

    if (!hasPortfolio) {
      return { ok: false, state: 'EMPTY', error: 'No portfolio data returned.' };
    }

    return { ok: true, state: 'SUCCESS', data: response };
  }

  const runAnalysis = useCallback(async (address) => {
    const trimmed = (address || '').trim();
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    setProgressIndex(0);
    if (!trimmed) {
      setStatus('idle');
      setError('Paste a wallet address to begin a live analysis.');
      return;
    }

    setStatus('loading');
    setError('');
    setNotice('');
    setResult(null);

    try {
      const response = await analyzeWallet(trimmed, inputChainType);

      if (requestId !== requestIdRef.current) {
        return;
      }

      const normalized = normalizeAnalysisResponse(response);

      if (!normalized.ok) {
        setStatus('error');
        setError(normalized.error);
        return;
      }

      setResult(normalized.data);
      setStatus('success');
      setNotice('Live analysis completed from the wallet analysis workflow.');
    } catch (err) {
      if (requestId !== requestIdRef.current) {
        return;
      }
      console.error('Wallet analysis failed:', err?.message || err);
      setStatus('error');
      setError(err?.message || 'Unable to analyze this wallet right now.');
    }
  }, []);

  useEffect(() => {
    if (!initialAddress) return;
    void runAnalysis(initialAddress);
  }, [initialAddress, runAnalysis]);

  async function handleSubmit(e) {
    e.preventDefault();

    const trimmed = addressInput.trim();
    if (!trimmed) return;

    if (location.pathname === `/wallet/${trimmed}`) {
      await runAnalysis(trimmed);
      return;
    }

    navigate(`/wallet/${trimmed}`);
  }

  async function handleRescan() {
    const trimmed = addressInput.trim();
    if (!trimmed) return;

    setError('');
    setNotice('');

    await runAnalysis(trimmed);
  }

  async function handleRetry() {
    const trimmed = addressInput.trim();
    if (!trimmed) return;

    setResult(null);
    setError('');
    setNotice('');

    await runAnalysis(trimmed);
  }

  function handleShareAuditLink() {
    const address = addressInput.trim();
    if (!address) {
      setNotice('Paste an address before copying the audit link.');
      return;
    }

    const url = `${window.location.origin}/wallet/${encodeURIComponent(address)}`;
    navigator.clipboard.writeText(url).then(() => {
      setNotice('Audit link copied to clipboard.');
    }).catch(() => {
      setNotice('Unable to copy the audit link.');
    });
  }

  function handleExportJson() {
    if (!result) return;
    exportJsonReport(result);
    setNotice('JSON report exported.');
  }

  function handleExportPdf() {
    if (!result) return;
    exportPdfReport(result);
    setNotice('PDF report exported.');
  }

  const assetCount = result?.assets?.length ?? 0;
  const transactionCount = result?.transactions?.length ?? 0;
  const nftCount = result?.nft_count ?? 0;
  const chainTypeLabel = result?.chain_type === 'solana' ? 'Solana' : result?.chain_type === 'xlayer' ? 'X Layer' : result?.chain_type === 'evm' ? 'EVM' : null;
  const summaryText = typeof result?.summary === 'string' ? result.summary : '';
  const walletAddress = result?.address || addressInput.trim();
  const walletAddressShort = walletAddress
    ? `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`
    : 'Unknown wallet';
  const totalUsdValue = (result?.assets || []).reduce((sum, asset) => {
    const usdValue = typeof asset.usdValue === 'number' ? asset.usdValue : typeof asset.usdValue === 'string' ? Number(asset.usdValue) : NaN;
    if (!Number.isFinite(usdValue)) {
      const price = typeof asset.pricePerToken === 'number' ? asset.pricePerToken : typeof asset.pricePerToken === 'string' ? Number(asset.pricePerToken) : NaN;
      const balance = typeof asset.balance === 'number' ? asset.balance : typeof asset.balance === 'string' ? Number(asset.balance) : NaN;
      return sum + (Number.isFinite(price) && Number.isFinite(balance) ? price * balance : 0);
    }
    return sum + usdValue;
  }, 0);
  const portfolioValueText = totalUsdValue > 0 ? formatCurrency(totalUsdValue) : 'Value unavailable';
  const inputNetworkBadge = useMemo(() => {
    const trimmed = addressInput.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith('0x')) return 'EVM';
    if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed)) return 'Solana';
    return null;
  }, [addressInput]);
  const hasValidWalletAddress = useMemo(() => {
    const trimmed = addressInput.trim();
    return /^0x[a-fA-F0-9]{40}$/.test(trimmed) || /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed);
  }, [addressInput]);
  const inputChainType = useMemo(() => {
    if (inputNetworkBadge === 'Solana') return 'solana';
    if (inputNetworkBadge === 'EVM') return 'evm';
    return undefined;
  }, [inputNetworkBadge]);

  const assetRows = (result?.assets || []).map((asset) => {
    const symbol = asset.symbol || '';
    const name = asset.name || asset.address || 'Unknown asset';
    // Native status comes from the backend's explicit is_native flag, never
    // inferred from the name/symbol — inferring it flagged any ERC-20 whose
    // name merely contained "eth"/"sol" (e.g. Tether/USDT) as a native asset.
    const isNative = asset.is_native === true;
    const analyzed = asset.analysis_status === 'analyzed';
    // Only treat the score as numeric when the backend actually analyzed the
    // asset — missing != zero. An unavailable/native asset has no score.
    const rawScore = analyzed && asset.risk_score != null && asset.risk_score !== ''
      ? Number(asset.risk_score)
      : NaN;
    const hasNumericScore = Number.isFinite(rawScore);
    // Trust the backend's risk_level as the source of truth for severity — do
    // not recompute a band from the numeric score. Native/unavailable assets
    // arrive as "Unscored"; analyzed ones as Low/Medium/High/Critical.
    const bucket = isNative
      ? 'Unscored'
      : ['Low', 'Medium', 'High', 'Critical'].includes(asset.risk_level) ? asset.risk_level : 'Unscored';
    const score = isNative ? 'N/A' : hasNumericScore ? `${rawScore}/100` : '--';
    const risk = isNative ? 'Native Asset' : bucket;
    const reason = isNative
      ? 'Native asset — contract analysis not applicable'
      : asset.analysis_status === 'unavailable'
      ? 'Contract analysis unavailable from the current provider.'
      : asset.reasons?.length
      ? asset.reasons.slice(0, 2).join(' ')
      : 'No material risk signals were returned.';
    const address = asset.address ? `${asset.address.slice(0, 6)}...${asset.address.slice(-4)}` : '—';
    return {
      key: asset.address || name,
      name,
      symbol: symbol.toUpperCase() || 'N/A',
      risk,
      score,
      reason,
      isNative,
      address,
      bucket,
      numericScore: hasNumericScore ? rawScore : null,
    };
  });

  const eligibleAssetRows = assetRows.filter((asset) => !asset.isNative);
  const scoredAssetCount = eligibleAssetRows.filter((asset) => asset.bucket !== 'Unscored').length;
  const nativeAssetCount = assetRows.filter((asset) => asset.isNative).length;
  const unavailableAssetCount = eligibleAssetRows.filter((asset) => asset.bucket === 'Unscored').length;
  const coverageText = `${scoredAssetCount} / ${eligibleAssetRows.length} eligible assets`;
  const contractAssets = eligibleAssetRows.filter((asset) => asset.bucket !== 'Unscored');
  const contractAverageRisk = contractAssets.length
    ? contractAssets.reduce((sum, asset) => sum + (asset.numericScore ?? 0), 0) / contractAssets.length
    : null;
  const contractScore = contractAverageRisk != null ? Math.round(100 - contractAverageRisk) : null;
  const backendScoreValue = Number.isFinite(Number(result?.portfolio_score ?? result?.risk_score))
    ? Number(result?.portfolio_score ?? result?.risk_score)
    : null;
  const contractScoreDisplay = contractScore != null ? `${contractScore}/100` : 'N/A';
  const backendScoreDisplay = backendScoreValue != null ? `${backendScoreValue}/100` : null;
  const portfolioScoreDisplay = backendScoreDisplay ?? contractScoreDisplay;
  const scoreBreakdownScore = portfolioScoreDisplay;
  const scoreBreakdownLabel = backendScoreValue != null ? 'Safety score' : 'Average token safety';
  // Trust the backend's risk_level verbatim — it is the source of truth and is
  // already severity-floored (a single dangerous holding cannot be averaged away
  // by clean ones). Do NOT re-derive the band from the numeric score: that both
  // duplicated the backend's own thresholds and turned an empty/errored score of
  // 0 into a false "Critical". The numeric score above is kept for display only.
  const backendRiskLevel = ['Low', 'Medium', 'High', 'Critical'].includes(result?.risk_level)
    ? result.risk_level
    : null;
  const contractRiskLevel = contractScore != null
    ? contractScore >= 80 ? 'Low' : contractScore >= 60 ? 'Medium' : contractScore >= 40 ? 'High' : 'Critical'
    : 'Insufficient data';
  const riskLevelStatus = backendRiskLevel ?? contractRiskLevel;
  const riskLevelAccent = riskLevelStatus === 'Low' ? 'green' : riskLevelStatus === 'Medium' ? 'amber' : riskLevelStatus === 'High' ? 'red' : riskLevelStatus === 'Critical' ? 'red' : 'muted';
  const aiAssessment = summaryText
    ? summaryText.split('. ').slice(0, 2).join('. ') + (summaryText.endsWith('.') ? '' : '.')
    : 'Review the available token exposure and transaction history for details.';

  const riskCounts = assetRows.reduce(
    (counts, asset) => {
      if (asset.bucket === 'Low') counts.low += 1;
      else if (asset.bucket === 'Medium') counts.medium += 1;
      else if (asset.bucket === 'High') counts.high += 1;
      else if (asset.bucket === 'Critical') counts.critical += 1;
      else counts.unscored += 1;
      return counts;
    },
    { low: 0, medium: 0, high: 0, critical: 0, unscored: 0 }
  );
  const riskDistributionData = [
    { name: 'Low', value: riskCounts.low, fill: '#22C55E' },
    { name: 'Medium', value: riskCounts.medium, fill: '#F59E0B' },
    { name: 'High', value: riskCounts.high, fill: '#EF4444' },
    { name: 'Critical', value: riskCounts.critical, fill: '#B91C3C' },
    { name: 'Unscored', value: riskCounts.unscored, fill: '#9CA3AF' },
  ].filter((entry) => entry.value > 0);
  const riskLegend = riskDistributionData.map((item) => ({
    label: item.name,
    value: item.value,
    color: item.fill,
  }));

  const filteredAssetRows = assetRows.filter((asset) => {
    const query = tokenSearch.trim().toLowerCase();
    const matchesQuery = !query || asset.name.toLowerCase().includes(query) || asset.symbol.toLowerCase().includes(query);
    const matchesFilter = riskFilter === 'All' || asset.bucket === riskFilter;
    return matchesQuery && matchesFilter;
  });

  const transactionTimeline = (result?.transactions || [])
    .filter((tx) => tx.timestamp != null || tx.blockTime != null || tx.block_timestamp != null)
    .slice()
    .sort((a, b) => {
      const aTime = Number(a.timestamp ?? a.blockTime ?? a.block_timestamp ?? 0);
      const bTime = Number(b.timestamp ?? b.blockTime ?? b.block_timestamp ?? 0);
      return bTime - aTime;
    })
    .slice(0, 6)
    .map((tx, index) => {
      const signature = tx.signature || tx.hash || tx.transactionHash || tx.txHash || tx.tx_hash || 'Unknown';
      const statusText = tx.error === null || tx.error === false || tx.error === undefined ? 'Success' : 'Failed';
      const feeValue = tx.fee != null ? `${tx.fee} lamports` : tx.transactionFee != null ? `${tx.transactionFee}` : null;
      const balanceChanges = Array.isArray(tx.balanceChanges)
        ? tx.balanceChanges
            .map((change) => {
              const owner = change.owner || change.account || change.address;
              if (!owner) return null;
              const delta = change.delta ?? change.amount;
              return delta != null ? `${owner} ${delta}` : `${owner}`;
            })
            .filter((entry) => entry && !entry.startsWith('Unknown'))
            .join('; ')
        : '';
      return {
        key: `${signature}-${index}`,
        signature,
        date: formatTimelineDate(tx.timestamp ?? tx.blockTime ?? tx.block_timestamp),
        status: statusText,
        fee: feeValue,
        details: balanceChanges || (tx.slot != null ? `slot ${tx.slot}` : null),
      };
    });
  const hasTimelineFee = transactionTimeline.some((entry) => entry.fee);
  const hasTimelineDetails = transactionTimeline.some((entry) => entry.details);
  const transactionRows = (result?.transactions || []).slice(0, 10).map((tx) => {
    const signature = tx.signature || tx.hash || tx.transactionHash || tx.txHash || tx.tx_hash || 'Unknown';
    const balanceChanges = Array.isArray(tx.balanceChanges) ? tx.balanceChanges.map((change) => {
      const owner = change.owner || change.account || change.address;
      const delta = change.delta ?? change.amount;
      return owner ? (delta != null ? `${owner} ${delta}` : owner) : null;
    }).filter(Boolean).join('; ') : '';
    return { signature, date: formatDate(tx.timestamp || tx.blockTime || tx.block_timestamp), status: tx.error === null || tx.error === false || tx.error === undefined ? 'Success' : 'Failed', fee: tx.fee != null ? `${tx.fee} lamports` : tx.transactionFee != null ? `${tx.transactionFee}` : null, details: balanceChanges || (tx.slot != null ? `Slot ${tx.slot}` : null) };
  });
  const hasTransactionFee = transactionRows.some((entry) => entry.fee);
  const hasTransactionDetails = transactionRows.some((entry) => entry.details);

  const highestRiskAsset = assetRows
    .filter((asset) => asset.numericScore != null)
    // Severity-first: rank by the backend risk level (Critical > High > ...),
    // and only use the numeric score to break ties within the same level. A
    // Critical holding must never sort below a High one that happens to carry a
    // larger numeric score.
    .sort((a, b) => {
      const rankDiff = (RISK_RANK[b.bucket] ?? 0) - (RISK_RANK[a.bucket] ?? 0);
      return rankDiff !== 0 ? rankDiff : b.numericScore - a.numericScore;
    })[0];
  const highestRiskAssetName = highestRiskAsset ? truncateMiddle(highestRiskAsset.name, 30) : 'No scored asset available';
  const highestRiskAssetScore = highestRiskAsset ? `${highestRiskAsset.numericScore}/100` : null;

  const isEmpty = status === 'idle' || (status === 'success' && !result);
  const workflowProgress = status === 'loading' ? progressIndex : status === 'success' ? WORKFLOW_STEPS.length - 1 : -1;

  return (
    <div className="wallet-scanner-page">
      <section className="wallet-scanner-top">
        <Card className="wallet-intro-card">
          <div className="wallet-intro-header">
            <div>
              <div className="wallet-intro-tag">Live on-chain analysis</div>
              <h1>Wallet Scanner</h1>
              <p>Analyze wallet addresses using live blockchain risk intelligence.</p>
            </div>
            <div className="wallet-intro-icon"><ShieldCheck size={24} /></div>
          </div>

          <form className="wallet-search-form" onSubmit={handleSubmit}>
            <label className="wallet-search-label">Wallet Address</label>
            <div className="wallet-search-field-wrap">
              <input
                value={addressInput}
                onChange={(e) => setAddressInput(e.target.value)}
                type="text"
                placeholder="Paste a wallet address to begin analysis"
                aria-label="Wallet address"
              />
            </div>
            {(inputNetworkBadge || hasValidWalletAddress) && <div className="wallet-address-field-meta">
              {inputNetworkBadge && <span className="wallet-chain-chip">{inputNetworkBadge}</span>}
              {hasValidWalletAddress && <button type="button" className="wallet-address-copy" onClick={() => { navigator.clipboard.writeText(addressInput.trim()); setNotice('Wallet address copied to clipboard.'); }}><Copy size={14} /> Copy</button>}
            </div>}
            <div className="wallet-actions">
              <Button type="submit" variant="primary" className="btn-lg">Analyze Wallet</Button>
              <Button type="button" variant="secondary" className="btn-lg" onClick={() => { setAddressInput(''); setResult(null); setStatus('idle'); setError(''); }} disabled={status === 'loading' || !addressInput.trim()}>Clear</Button>
            </div>
          </form>

          <div className="wallet-scan-highlights">
            <div className="wallet-scan-feature"><CheckCircle2 size={15} /><div><strong>Address validation</strong><small>Detects the address format and compatible network.</small></div></div>
            <div className="wallet-scan-feature"><TrendingUp size={15} /><div><strong>Live risk intelligence</strong><small>Retrieves available wallet assets and on-chain activity.</small></div></div>
            <div className="wallet-scan-feature"><Sparkles size={15} /><div><strong>Actionable insights</strong><small>Summarizes exposure and portfolio risk signals.</small></div></div>
          </div>
        </Card>

        <Card className="wallet-progress-card">
          <div className="wallet-progress-header">
            <div>
              <span className="wallet-progress-eyebrow">Analysis progress</span>
              <h2>{status === 'success' ? 'Analysis completed' : status === 'loading' ? 'Live scan in progress' : 'Ready to analyze'}</h2>
            </div>
            <p className="wallet-progress-meta">
              {status === 'success'
                ? `${chainTypeLabel ? `${chainTypeLabel} • ` : ''}${assetCount} assets • ${transactionCount} transactions`
                : 'Ready to validate the address, detect the chain and fetch live asset risk data.'}
            </p>
          </div>

          <div className="wallet-progress-steps">
            {WORKFLOW_STEPS.map((step, index) => {
              const isCompleted = status === 'success' ? index <= workflowProgress : index < workflowProgress;
              const isActive = index === workflowProgress && status === 'loading';
              return (
                <div key={step} className={`wallet-progress-step ${isCompleted ? 'is-complete' : ''} ${isActive ? 'is-active' : ''}`}>
                  <div className="wallet-progress-marker">
                    {isCompleted ? <CheckCircle2 size={14} /> : isActive ? <LoaderCircle size={14} className="spin" /> : <span>{index + 1}</span>}
                  </div>
                  <span>{step}</span>
                </div>
              );
            })}
          </div>
        </Card>
      </section>


      {status === 'error' && (
        <Card className="wallet-panel-card wallet-error-card">
          <div className="wallet-panel-tag">Analysis blocked</div>
          <h3>Wallet analysis could not be completed</h3>
          <p>{error}</p>
          <div className="wallet-panel-notice"><AlertTriangle size={16} /> The scan stopped without fabricating any portfolio content.</div>
          <Button variant="primary" onClick={handleRetry} className="wallet-error-action">Retry analysis</Button>
        </Card>
      )}

      {status === 'success' && result && (
        <section className="wallet-report">
          <div className="wallet-report-header">
            <div className="wallet-report-heading">
              <span>Live results</span>
              <h2>Portfolio intelligence</h2>
            </div>
            <div className="wallet-actions-inline">
              <Button variant="secondary" onClick={handleShareAuditLink}>Share audit link</Button>
              <Button variant="secondary" onClick={handleRescan}><RefreshCw size={14} /> Refresh scan</Button>
              <Button variant="secondary" onClick={handleExportJson}><Download size={14} /> Export JSON</Button>
              <Button variant="secondary" onClick={handleExportPdf}><Download size={14} /> Export PDF</Button>
            </div>
          </div>

          <Card className="wallet-overview-card">
            <div className="wallet-overview-header">
              <div>
                <span className="wallet-summary-label">Wallet overview</span>
                <div className="wallet-profile-caption">
                  <strong>{walletAddressShort}</strong>
                  <div className="wallet-profile-actions">
                    {chainTypeLabel && <span className="wallet-profile-badge">{chainTypeLabel}</span>}
                    <button type="button" className="wallet-copy-button" onClick={() => { navigator.clipboard.writeText(walletAddress); setNotice('Wallet address copied to clipboard.'); }}>
                      <Copy size={14} /> Copy
                    </button>
                  </div>
                </div>
              </div>
              <div className="wallet-overview-score">
                <span className="wallet-summary-label">Safety Score</span>
                <strong>{portfolioScoreDisplay}</strong>
                <div className={`wallet-summary-pill risk-${riskLevelStatus.toLowerCase().replace(/\s+/g, '-')}`}>{riskLevelStatus}</div>
              </div>
            </div>
            <div className="wallet-overview-metrics">
              <div className="wallet-overview-metric">
                <span>Portfolio value</span>
                <strong>{portfolioValueText}</strong>
              </div>
              <div className="wallet-overview-metric">
                <span>Assets</span>
                <strong>{assetCount}</strong>
              </div>
              <div className="wallet-overview-metric">
                <span>Transactions</span>
                <strong>{transactionCount}</strong>
              </div>
              <div className="wallet-overview-metric">
                <span>Contract coverage</span>
                <strong>{coverageText}</strong>
                {nativeAssetCount > 0 && <small>{nativeAssetCount} native asset not applicable</small>}
              </div>
              <div className="wallet-overview-metric">
                <span>NFTs</span>
                <strong>{nftCount}</strong>
              </div>
            </div>
          </Card>
          <div className="wallet-section-heading">
            <span>Security overview</span>
            <p>AI risk summary and portfolio score breakdown from the live analysis.</p>
          </div>
          <div className="wallet-security-grid">
            <Card className="wallet-security-card">
              <div className="wallet-ai-summary-header">
                <div>
                  <span className="wallet-summary-label">AI risk summary</span>
                  <h3>Wallet risk snapshot</h3>
                </div>
                <ShieldCheck size={20} className="wallet-ai-summary-icon" />
              </div>
              <div className="wallet-ai-summary-grid wallet-security-grid-inner">
                <div className="wallet-ai-summary-item">
                  <span>Overall Risk</span>
                  <strong className={`wallet-ai-risk ${riskLevelAccent}`}>{riskLevelStatus}</strong>
                </div>
                <div className="wallet-ai-summary-item">
                  <span>Highest Risk Asset</span>
                  <strong className="wallet-risk-asset" title={highestRiskAsset?.name || 'No scored asset available'}>
                    <span className="wallet-risk-asset-name">{highestRiskAssetName}</span>
                    {highestRiskAssetScore ? <span className="wallet-risk-asset-score">{highestRiskAssetScore}</span> : null}
                  </strong>
                </div>
                <div className="wallet-ai-summary-item">
                  <span>Activity</span>
                  <strong>{transactionCount} transactions • {nftCount} NFTs</strong>
                </div>
                <div className="wallet-ai-summary-item">
                  <span>Contract coverage</span>
                  <strong>{coverageText}</strong>
                </div>
              </div>
              <p className="wallet-ai-summary-note">{aiAssessment || 'Review the available token exposure and transaction history for details.'}</p>
            </Card>
            <Card className="wallet-security-card wallet-score-breakdown-card">
              <div className="wallet-score-breakdown-header">
                <span className="wallet-summary-label">Score breakdown</span>
              </div>
              <div className="wallet-score-breakdown-grid">
                <div className="wallet-score-breakdown-item">
                  <strong>{scoreBreakdownScore}</strong>
                  <span>{scoreBreakdownLabel}</span>
                </div>
                <div className="wallet-score-breakdown-item">
                  <strong>{result.detail_metrics?.diversification || 'Unknown'}</strong>
                  <span>Diversification</span>
                </div>
                <div className="wallet-score-breakdown-item">
                  <strong>{result.detail_metrics?.liquidity_quality || 'Unknown'}</strong>
                  <span>Liquidity quality</span>
                </div>
                <div className="wallet-score-breakdown-item">
                  <strong>{coverageText}</strong>
                  <span>Contract coverage</span>
                </div>
              </div>
            </Card>
          </div>

          <div className="wallet-detail-grid wallet-detail-grid--compact">
            <Card className="wallet-metric-card wallet-assessment-card">
              <div className="wallet-asset-card-header">
                <span>AI security assessment</span>
                <p>Key findings from the live wallet analysis.</p>
              </div>
              <ul className="wallet-assessment-list">
                <li className="wallet-assessment-row">
                  <div className="wallet-assessment-icon"><CheckCircle2 size={16} /></div>
                  <span>{assetCount} asset{assetCount === 1 ? '' : 's'} detected in this wallet.</span>
                </li>
                <li className="wallet-assessment-row">
                  <div className="wallet-assessment-icon"><TrendingUp size={16} /></div>
                  <span>{transactionCount} historical transaction{transactionCount === 1 ? '' : 's'} observed on-chain.</span>
                </li>
                {nativeAssetCount > 0 && (
                  <li className="wallet-assessment-row">
                    <div className="wallet-assessment-icon"><AlertTriangle size={16} /></div>
                    <span>{nativeAssetCount} native asset{nativeAssetCount === 1 ? '' : 's'} is not eligible for contract analysis.</span>
                  </li>
                )}
                {unavailableAssetCount > 0 && <li className="wallet-assessment-row"><div className="wallet-assessment-icon"><AlertTriangle size={16} /></div><span>{unavailableAssetCount} eligible asset{unavailableAssetCount === 1 ? '' : 's'} could not be analyzed by the current provider and remains unscored.</span></li>}
                <li className="wallet-assessment-row">
                  <div className="wallet-assessment-icon"><Sparkles size={16} /></div>
                  <span>{coverageText} received contract-level analysis.</span>
                </li>
                <li className="wallet-assessment-row">
                  <div className="wallet-assessment-icon"><ShieldCheck size={16} /></div>
                  <span>
                    {backendScoreValue != null
                      ? `Backend safety score is ${portfolioScoreDisplay}.`
                      : contractScore != null
                      ? `Contract-derived safety score is ${contractScoreDisplay}.`
                      : 'Safety scoring is unavailable because no scored assets were returned.'}
                  </span>
                </li>
              </ul>
            </Card>
            <Card className="wallet-metric-card wallet-timeline-card">
              <div className="wallet-asset-card-header">
                <span>Wallet activity timeline</span>
                <p>Most recent wallet transactions from the live provider.</p>
              </div>
              <div className="wallet-timeline-list">
                {transactionTimeline.length > 0 ? (
                  transactionTimeline.slice(0, 5).map((entry) => (
                    <div key={entry.key} className="wallet-timeline-row" style={{ gridTemplateColumns: `132px minmax(180px, 1fr) 75px${hasTimelineFee ? ' minmax(105px, auto)' : ''}${hasTimelineDetails ? ' minmax(110px, auto)' : ''}` }}>
                      <span className="wallet-timeline-time">{entry.date}</span>
                      <span className="wallet-timeline-hash" title={entry.signature}><strong>{entry.signature.slice(0, 8)}...{entry.signature.slice(-8)}</strong></span>
                      <span className={`wallet-status-badge wallet-status-${entry.status.toLowerCase()}`}>{entry.status}</span>
                      {hasTimelineFee && <span className="wallet-timeline-detail">{entry.fee || 'Not provided'}</span>}
                      {hasTimelineDetails && <span className="wallet-timeline-detail">{entry.details || 'Not provided'}</span>}
                    </div>
                  ))
                ) : (
                  <p>No wallet transaction history is available to populate this timeline.</p>
                )}
              </div>
              {transactionTimeline.length > 5 && (
                <p className="wallet-timeline-footer">Showing latest 5 transactions. View more in the detailed table below.</p>
              )}
            </Card>
          </div>

          <div className="wallet-analysis-grid">
            <Card className="wallet-asset-card wallet-asset-analysis-card">
              <div className="wallet-asset-card-header">
                <span>Asset risk analysis</span>
                <p>Token exposure, risk score and findings from live wallet data.</p>
              </div>
              <div className="wallet-asset-toolbar">
                <div className="wallet-asset-search">
                  <input
                    type="text"
                    value={tokenSearch}
                    onChange={(e) => setTokenSearch(e.target.value)}
                    placeholder="Search tokens by name or symbol"
                    aria-label="Search tokens"
                  />
                </div>
                <div className="wallet-risk-tabs">
                  {['All', 'Critical', 'High', 'Medium', 'Low', 'Unscored'].map((tab) => {
                    const tabCount = tab === 'All'
                      ? assetRows.length
                      : tab === 'Critical' ? riskCounts.critical
                      : tab === 'High' ? riskCounts.high
                      : tab === 'Medium' ? riskCounts.medium
                      : tab === 'Low' ? riskCounts.low
                      : riskCounts.unscored;
                    return (
                      <button
                        key={tab}
                        type="button"
                        className={`wallet-risk-tab ${riskFilter === tab ? 'is-active' : ''}`}
                        onClick={() => setRiskFilter(tab)}
                      >
                        {tab} ({tabCount})
                      </button>
                    );
                  })}
                </div>
              </div>
              {filteredAssetRows.length > 0 ? (
                <div className="wallet-asset-table-wrapper">
                  <table className="wallet-asset-table">
                    <thead>
                      <tr>
                        <th>Asset</th>
                        <th>Risk</th>
                        <th>Risk Score</th>
                        <th>Finding</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAssetRows.map((asset) => (
                        <tr key={asset.key}>
                          <td>
                            <div className="wallet-asset-title">{asset.name}</div>
                            <div className="wallet-asset-symbol">{asset.symbol}</div>
                          </td>
                          <td><span className={`wallet-risk-badge risk-${asset.isNative ? 'native' : asset.risk.toLowerCase()}`}>{asset.isNative ? 'Native Asset' : asset.risk}</span></td>
                          <td>{asset.score}</td>
                          <td>{asset.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>No asset-level findings were returned.</p>
              )}
            </Card>

            <div className="wallet-chart-column wallet-chart-panel-column">
              <Card className="wallet-chart-card">
                <span className="wallet-summary-label">Risk allocation</span>
                <div className="wallet-chart-wrapper wallet-chart-wrapper-donut">
                  {riskDistributionData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={120}>
                      <PieChart>
                        <Pie data={riskDistributionData} dataKey="value" nameKey="name" innerRadius={38} outerRadius={56} paddingAngle={4}>
                          {riskDistributionData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="wallet-chart-empty">Risk categories are not available for this wallet.</p>
                  )}
                </div>
                {riskLegend.length > 0 && (
                  <div className="wallet-chart-legend">
                    {riskLegend.map((entry) => (
                      <div key={entry.label} className="wallet-legend-item">
                        <span className="wallet-legend-swatch" style={{ background: entry.color }} />
                        <span>{entry.label}</span>
                        <strong>{entry.value}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              <Card className="wallet-chart-card">
                <span className="wallet-summary-label">Risk distribution</span>
                <div className="wallet-chart-wrapper">
                  {riskDistributionData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={riskDistributionData} margin={{ top: 8, right: 0, left: -10, bottom: 0 }}>
                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#AFC9FF', fontSize: 12 }} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#AFC9FF', fontSize: 12 }} />
                        <Tooltip />
                        <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                          {riskDistributionData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="wallet-chart-empty">No risk distribution data is available.</p>
                  )}
                </div>
              </Card>
            </div>
          </div>

          <Card className="wallet-transaction-card">
            <div className="wallet-asset-card-header">
              <span>Recent transactions</span>
              <p>Transaction history scraped from the live provider response.</p>
            </div>
            {transactionCount > 0 ? (
              <div className="wallet-asset-table-wrapper">
                <table className="wallet-asset-table wallet-tx-table">
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Date</th>
                      <th>Status</th>
                      {hasTransactionFee && <th>Fee</th>}
                      {hasTransactionDetails && <th>Details</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {transactionRows.map((tx) => {
                      const { signature } = tx;
                      const shortSignature = signature.length > 16 ? `${signature.slice(0, 8)}...${signature.slice(-8)}` : signature;
                      return (
                        <tr key={signature}>
                          <td>
                            <div className="wallet-tx-signature-row">
                              <span>{shortSignature}</span>
                              <button type="button" className="wallet-tx-copy" onClick={() => { navigator.clipboard.writeText(signature); setNotice('Transaction signature copied.'); }}>
                                Copy
                              </button>
                            </div>
                          </td>
                          <td>{tx.date}</td>
                          <td><span className={`wallet-status-badge wallet-status-${tx.status.toLowerCase()}`}>{tx.status}</span></td>
                          {hasTransactionFee && <td>{tx.fee || 'Not provided'}</td>}
                          {hasTransactionDetails && <td>{tx.details || 'Not provided'}</td>}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No transaction history was returned by the current provider.</p>
            )}
          </Card>
        </section>      )}

      {isEmpty && (
        <Card className="wallet-panel-card wallet-empty-card">
          <div className="wallet-panel-tag">Ready</div>
          <h3>Start with a public wallet address</h3>
          <p>Paste a wallet address to trigger a live scan. The page will show a real result if the address is valid and live data is available.</p>
          <div className="wallet-panel-notice"><Search size={16} /> No mock portfolio values are displayed in this experience.</div>
        </Card>
      )}

      {notice && <div className="wallet-notice">{notice}</div>}
    </div>
  );
}
