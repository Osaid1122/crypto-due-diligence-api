import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, RotateCw, ShieldCheck, ScanSearch, CircleAlert } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import SimulationCard from '../components/simulation/SimulationCard';
import { getAttackScenarios, selectPrimaryScenario } from '../utils/attackSimulation';
import { analyzeToken } from '../api/client';
import ChainSelector, { addressPlaceholder, isValidAddress } from '../components/ChainSelector';
import { getNetwork, isNetworkKey } from '../config/networks';
import './Simulation.css';

const LOADING_MESSAGES = [
  'Retrieving security data…',
  'Identifying risky capabilities…',
  'Building educational scenarios…',
];

export default function Simulation() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [chainType, setChainType] = useState(isNetworkKey(searchParams.get('chain_type')) ? searchParams.get('chain_type') : 'ethereum');
  const [addressInput, setAddressInput] = useState(searchParams.get('address') || '');
  const [status, setStatus] = useState('idle');
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [duration, setDuration] = useState(null);

  useEffect(() => {
    if (status !== 'loading') return;
    setLoadingMsgIndex(0);
    const interval = setInterval(() => setLoadingMsgIndex(i => (i + 1) % LOADING_MESSAGES.length), 900);
    return () => clearInterval(interval);
  }, [status]);

  const runAnalysis = useCallback(async (chain, address) => {
    if (!isValidAddress(chain, address)) {
      setStatus('error');
      setErrorMsg(chain === 'solana' ? 'Invalid Solana mint address.' : `Invalid ${getNetwork(chain).label} address.`);
      return;
    }
    setStatus('loading');
    setErrorMsg('');
    const startedAt = performance.now();
    try {
      const data = await analyzeToken(chain, address);
      setResult(data);
      setDuration(((performance.now() - startedAt) / 1000).toFixed(2));
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

  const scenarios = status === 'success' && result ? getAttackScenarios(result) : [];
  const primaryScenario = selectPrimaryScenario(scenarios);
  const relatedScenarios = primaryScenario
    ? scenarios.filter(scenario => scenario.key !== primaryScenario.key)
    : [];

  return (
    <div className="simulation-page">
      <div className="simulation-intro"><ScanSearch size={20} /><div><span>INVESTIGATION MODE</span><h2>Attack surface simulation</h2></div></div>
      <Card className="simulation-input-card">
        <p className="simulation-disclaimer">
          Educational only — this page explains what identified contract capabilities could allow if abused. It does not simulate real blockchain transactions.
        </p>
        <form onSubmit={handleSubmit} className="simulation-input-row">
          <ChainSelector value={chainType} onChange={setChainType} />
          <input
            type="text"
            className="simulation-address-input"
            placeholder={addressPlaceholder(chainType)}
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
          />
          <Button type="submit" variant="primary" loading={status === 'loading'}>Analyze</Button>
        </form>
      </Card>

      {status === 'idle' && (
        <Card className="simulation-empty"><ShieldCheck size={28} className="simulation-clean-icon" /><p>Start an investigation to map contract capabilities into potential attack paths.</p></Card>
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
          <Button variant="secondary" onClick={() => runAnalysis(chainType, addressInput.trim())}>
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
          <SimulationCard scenario={primaryScenario} chainType={result.network || chainType} confidence={result.confidence} duration={duration} />
          {relatedScenarios.length > 0 && (
            <section className="simulation-related-findings" aria-labelledby="related-findings-title">
              <div className="simulation-related-heading">
                <CircleAlert size={17} />
                <div>
                  <span>ADDITIONAL DETECTED FINDINGS</span>
                  <h3 id="related-findings-title">Related security findings</h3>
                </div>
              </div>
              <div className="simulation-related-list">
                {relatedScenarios.map(scenario => (
                  <article className="simulation-related-item" key={scenario.key}>
                    <div>
                      <h4>{scenario.title}</h4>
                      <p>{scenario.description}</p>
                    </div>
                    <span className={`simulation-related-severity severity-${scenario.impact.toLowerCase()}`}>
                      {scenario.impact}
                    </span>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
