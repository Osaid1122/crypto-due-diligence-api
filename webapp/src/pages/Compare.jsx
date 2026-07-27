import { useState } from 'react';
import { GitCompare } from 'lucide-react';
import Card from '../components/Card';
import Button from '../components/Button';
import TokenPanel from '../components/compare/TokenPanel';
import ComparisonSummary from '../components/compare/ComparisonSummary';
import { analyzeToken } from '../api/client';
import ChainSelector, { addressPlaceholder, isValidAddress } from '../components/ChainSelector';
import { getNetwork } from '../config/networks';
import './Compare.css';

const EMPTY_SIDE = { chainType: 'ethereum', address: '', status: 'idle', result: null, error: '' };

export default function Compare() {
  const [sideA, setSideA] = useState({ ...EMPTY_SIDE });
  const [sideB, setSideB] = useState({ ...EMPTY_SIDE });

  function updateSide(setSide, patch) {
    setSide(prev => ({ ...prev, ...patch }));
  }

  async function runComparison(e) {
    e.preventDefault();

    const validA = isValidAddress(sideA.chainType, sideA.address);
    const validB = isValidAddress(sideB.chainType, sideB.address);

    if (!validA) updateSide(setSideA, { status: 'error', error: 'Invalid contract address.' });
    if (!validB) updateSide(setSideB, { status: 'error', error: 'Invalid contract address.' });
    if (!validA || !validB) return;

    updateSide(setSideA, { status: 'loading', error: '' });
    updateSide(setSideB, { status: 'loading', error: '' });

    // Reuses the existing /analyze/token endpoint twice, in parallel — no
    // backend change, no duplicated analysis logic. allSettled so one side
    // failing doesn't block the other from rendering.
    const [resA, resB] = await Promise.allSettled([
      analyzeToken(sideA.chainType, sideA.address.trim()),
      analyzeToken(sideB.chainType, sideB.address.trim()),
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

  function chainName(chainType) {
    return getNetwork(chainType).label;
  }

  const bothSucceeded = sideA.status === 'success' && sideB.status === 'success';

  return (
    <div className="compare-page">
      <Card className="compare-input-card">
        <form onSubmit={runComparison} className="compare-form">
          <div className="compare-input-col">
            <div className="compare-input-label">Token A</div>
            <ChainSelector value={sideA.chainType} onChange={chainType => updateSide(setSideA, { chainType })} />
            <input
              type="text"
              className="compare-address-input"
              placeholder={addressPlaceholder(sideA.chainType)}
              value={sideA.address}
              onChange={e => updateSide(setSideA, { address: e.target.value, error: '' })}
            />
          </div>

          <div className="compare-vs"><GitCompare size={20} /></div>

          <div className="compare-input-col">
            <div className="compare-input-label">Token B</div>
            <ChainSelector value={sideB.chainType} onChange={chainType => updateSide(setSideB, { chainType })} />
            <input
              type="text"
              className="compare-address-input"
              placeholder={addressPlaceholder(sideB.chainType)}
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
            chainName={chainName(sideA.chainType)}
            address={sideA.address.trim()}
          />
          <TokenPanel
            label="Token B"
            status={sideB.status}
            result={sideB.result}
            error={sideB.error}
            chainName={chainName(sideB.chainType)}
            address={sideB.address.trim()}
          />
        </div>
      )}
    </div>
  );
}
