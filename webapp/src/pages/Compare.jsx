import { useEffect, useState } from 'react';
import { GitCompare } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import TokenPanel from '../components/compare/TokenPanel';
import ComparisonSummary from '../components/compare/ComparisonSummary';
import { fetchChains, analyzeToken, ADDRESS_RE } from '../api/client';
import './Compare.css';

const EMPTY_SIDE = { chainId: '1', address: '', status: 'idle', result: null, error: '' };

export default function Compare() {
  const [chains, setChains] = useState([]);
  const [sideA, setSideA] = useState({ ...EMPTY_SIDE });
  const [sideB, setSideB] = useState({ ...EMPTY_SIDE });

  useEffect(() => {
    fetchChains().then(d => setChains(d.chains || [])).catch(() => {});
  }, []);

  const groupedChains = chains.reduce((acc, c) => {
    (acc[c.ecosystem] ||= []).push(c);
    return acc;
  }, {});

  function updateSide(setSide, patch) {
    setSide(prev => ({ ...prev, ...patch }));
  }

  async function runComparison(e) {
    e.preventDefault();

    const validA = ADDRESS_RE.test(sideA.address.trim());
    const validB = ADDRESS_RE.test(sideB.address.trim());

    if (!validA) updateSide(setSideA, { status: 'error', error: 'Invalid contract address.' });
    if (!validB) updateSide(setSideB, { status: 'error', error: 'Invalid contract address.' });
    if (!validA || !validB) return;

    updateSide(setSideA, { status: 'loading', error: '' });
    updateSide(setSideB, { status: 'loading', error: '' });

    // Reuses the existing /analyze/token endpoint twice, in parallel — no
    // backend change, no duplicated analysis logic. allSettled so one side
    // failing doesn't block the other from rendering.
    const [resA, resB] = await Promise.allSettled([
      analyzeToken(Number(sideA.chainId), sideA.address.trim()),
      analyzeToken(Number(sideB.chainId), sideB.address.trim()),
    ]);

    if (resA.status === 'fulfilled') {
      updateSide(setSideA, { status: 'success', result: resA.value });
    } else {
      updateSide(setSideA, { status: 'error', error: resA.reason?.message || 'Analysis failed.' });
    }

    if (resB.status === 'fulfilled') {
      updateSide(setSideB, { status: 'success', result: resB.value });
    } else {
      updateSide(setSideB, { status: 'error', error: resB.reason?.message || 'Analysis failed.' });
    }
  }

  function chainName(chainId) {
    return chains.find(c => String(c.id) === String(chainId))?.name;
  }

  const bothSucceeded = sideA.status === 'success' && sideB.status === 'success';

  return (
    <div className="compare-page">
      <Card className="compare-input-card">
        <form onSubmit={runComparison} className="compare-form">
          <div className="compare-input-col">
            <div className="compare-input-label">Token A</div>
            <select
              value={sideA.chainId}
              onChange={e => updateSide(setSideA, { chainId: e.target.value })}
              className="compare-select"
              aria-label="Token A blockchain"
            >
              {Object.entries(groupedChains).map(([eco, list]) => (
                <optgroup key={eco} label={eco}>
                  {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </optgroup>
              ))}
            </select>
            <input
              type="text"
              className="compare-address-input"
              placeholder="0xA0b86991..."
              value={sideA.address}
              onChange={e => updateSide(setSideA, { address: e.target.value, error: '' })}
            />
          </div>

          <div className="compare-vs"><GitCompare size={20} /></div>

          <div className="compare-input-col">
            <div className="compare-input-label">Token B</div>
            <select
              value={sideB.chainId}
              onChange={e => updateSide(setSideB, { chainId: e.target.value })}
              className="compare-select"
              aria-label="Token B blockchain"
            >
              {Object.entries(groupedChains).map(([eco, list]) => (
                <optgroup key={eco} label={eco}>
                  {list.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </optgroup>
              ))}
            </select>
            <input
              type="text"
              className="compare-address-input"
              placeholder="0x514910771AF9Ca656af840dff83E8264EcF986CA"
              value={sideB.address}
              onChange={e => updateSide(setSideB, { address: e.target.value, error: '' })}
            />
          </div>
        </form>
        <Button
          variant="primary"
          fullWidth
          onClick={runComparison}
          loading={sideA.status === 'loading' || sideB.status === 'loading'}
        >
          Analyze comparison
        </Button>
      </Card>

      {bothSucceeded && <ComparisonSummary resultA={sideA.result} resultB={sideB.result} />}

      {(sideA.status !== 'idle' || sideB.status !== 'idle') && (
        <div className="compare-grid">
          <TokenPanel
            label="Token A"
            status={sideA.status}
            result={sideA.result}
            error={sideA.error}
            chainName={chainName(sideA.chainId)}
            address={sideA.address.trim()}
          />
          <TokenPanel
            label="Token B"
            status={sideB.status}
            result={sideB.result}
            error={sideB.error}
            chainName={chainName(sideB.chainId)}
            address={sideB.address.trim()}
          />
        </div>
      )}
    </div>
  );
}
