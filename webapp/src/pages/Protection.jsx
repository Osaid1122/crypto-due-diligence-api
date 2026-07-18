import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, RotateCw, ShieldCheck, ShieldAlert, ShieldX, ShieldQuestion } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import SignalList from '../components/dashboard/SignalList';
import RecommendationSection from '../components/protection/RecommendationSection';
import {
  getOverallRecommendation, getImmediateActions,
  getBeforeInvestingChecklist, getMonitoringChecklist, getGoodSigns,
} from '../components/protection/recommendationLogic';
import { fetchChains, analyzeToken, ADDRESS_RE } from '../api/client';
import './Protection.css';

const LOADING_MESSAGES = [
  'Retrieving security data…',
  'Calculating deterministic score…',
  'Deriving recommendations…',
];

const BANNER_ICONS = {
  proceed: ShieldCheck,
  caution: ShieldQuestion,
  'high-risk': ShieldAlert,
  avoid: ShieldX,
};

export default function Protection() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [chains, setChains] = useState([]);
  const [chainId, setChainId] = useState(searchParams.get('chain') || '1');
  const [addressInput, setAddressInput] = useState(searchParams.get('address') || '');
  const [status, setStatus] = useState('idle');
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchChains().then(d => setChains(d.chains || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (status !== 'loading') return;
    setLoadingMsgIndex(0);
    const interval = setInterval(() => setLoadingMsgIndex(i => (i + 1) % LOADING_MESSAGES.length), 900);
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
    try {
      const data = await analyzeToken(Number(chain), address);
      setResult(data);
      setStatus('success');
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Unable to analyze this contract.');
    }
  }, []);

  useEffect(() => {
    const chain = searchParams.get('chain');
    const address = searchParams.get('address');
    if (chain && address && ADDRESS_RE.test(address)) runAnalysis(chain, address);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    setSearchParams({ chain: chainId, address: addressInput.trim() });
    runAnalysis(chainId, addressInput.trim());
  }

  const groupedChains = chains.reduce((acc, c) => {
    (acc[c.ecosystem] ||= []).push(c);
    return acc;
  }, {});

  const overall = result ? getOverallRecommendation(result.risk_score) : null;
  const BannerIcon = overall ? BANNER_ICONS[overall.level] : null;

  return (
    <div className="protection-page">
      <Card className="protection-input-card">
        <form onSubmit={handleSubmit} className="protection-input-row">
          <select value={chainId} onChange={e => setChainId(e.target.value)} className="protection-select" aria-label="Blockchain">
            {Object.entries(groupedChains).map(([eco, list]) => (
              <optgroup key={eco} label={eco}>
                {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
            ))}
          </select>
          <input
            type="text"
            className="protection-address-input"
            placeholder="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
          />
          <Button type="submit" variant="primary" loading={status === 'loading'}>Get advice</Button>
        </form>
      </Card>

      {status === 'idle' && (
        <Card className="protection-empty"><p>Paste a contract address above to get protection guidance.</p></Card>
      )}

      {status === 'loading' && (
        <Card className="protection-loading">
          <div className="protection-spinner" />
          <p>{LOADING_MESSAGES[loadingMsgIndex]}</p>
        </Card>
      )}

      {status === 'error' && (
        <Card className="protection-error">
          <div className="protection-error-title"><AlertCircle size={18} /> Unable to analyze this contract</div>
          <p className="protection-error-detail">{errorMsg}</p>
          <Button variant="secondary" onClick={() => runAnalysis(chainId, addressInput.trim())}>
            <RotateCw size={14} /> Retry
          </Button>
        </Card>
      )}

      {status === 'success' && result && overall && (
        <>
          <div className={`protection-banner protection-banner-${overall.level}`}>
            <BannerIcon size={28} />
            <div>
              <div className="protection-banner-label">{overall.label}</div>
              <div className="protection-banner-desc">{overall.desc}</div>
            </div>
          </div>

          <RecommendationSection title="Immediate actions" items={getImmediateActions(result)} />
          <RecommendationSection title="Before investing" items={getBeforeInvestingChecklist(result)} />
          <RecommendationSection title="Monitoring" items={getMonitoringChecklist(result)} />

          <Card>
            <h3 className="protection-good-signs-title">Good signs</h3>
            <SignalList variant="positive" items={getGoodSigns(result)} />
          </Card>
        </>
      )}
    </div>
  );
}
