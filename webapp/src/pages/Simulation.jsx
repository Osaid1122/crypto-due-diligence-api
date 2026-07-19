import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, RotateCw, ShieldCheck } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import SimulationCard from '../components/simulation/SimulationCard';
import { getAttackScenarios } from '../utils/attackSimulation';
import { fetchChains, analyzeToken, ADDRESS_RE } from '../api/client';
import './Simulation.css';

const LOADING_MESSAGES = [
  'Retrieving security data…',
  'Identifying risky capabilities…',
  'Building educational scenarios…',
];

export default function Simulation() {
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

  const scenarios = status === 'success' && result ? getAttackScenarios(result) : [];

  return (
    <div className="simulation-page">
      <Card className="simulation-input-card">
        <p className="simulation-disclaimer">
          Educational only — this page explains what identified contract capabilities could allow if abused. It does not simulate real blockchain transactions.
        </p>
        <form onSubmit={handleSubmit} className="simulation-input-row">
          <select value={chainId} onChange={e => setChainId(e.target.value)} className="simulation-select" aria-label="Blockchain">
            {Object.entries(groupedChains).map(([eco, list]) => (
              <optgroup key={eco} label={eco}>
                {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
            ))}
          </select>
          <input
            type="text"
            className="simulation-address-input"
            placeholder="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
          />
          <Button type="submit" variant="primary" loading={status === 'loading'}>Analyze</Button>
        </form>
      </Card>

      {status === 'idle' && (
        <Card className="simulation-empty"><p>Paste a contract address above to see potential attack scenarios.</p></Card>
      )}

      {status === 'loading' && (
        <Card className="simulation-loading">
          <div className="simulation-spinner" />
          <p>{LOADING_MESSAGES[loadingMsgIndex]}</p>
        </Card>
      )}

      {status === 'error' && (
        <Card className="simulation-error">
          <div className="simulation-error-title"><AlertCircle size={18} /> Unable to analyze this contract</div>
          <p className="simulation-error-detail">{errorMsg}</p>
          <Button variant="secondary" onClick={() => runAnalysis(chainId, addressInput.trim())}>
            <RotateCw size={14} /> Retry
          </Button>
        </Card>
      )}

      {status === 'success' && scenarios.length === 0 && (
        <Card className="simulation-clean">
          <ShieldCheck size={28} className="simulation-clean-icon" />
          <p>No significant attack scenarios detected from current analysis.</p>
        </Card>
      )}

      {status === 'success' && scenarios.length > 0 && (
        <div className="simulation-grid">
          {scenarios.map(scenario => <SimulationCard key={scenario.key} scenario={scenario} />)}
        </div>
      )}
    </div>
  );
}
