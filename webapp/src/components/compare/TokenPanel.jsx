import RiskGauge from '../dashboard/RiskGauge';
import RiskBadge from '../dashboard/RiskBadge';
import ConfidenceBar from '../dashboard/ConfidenceBar';
import ScoreBreakdownChart from '../dashboard/ScoreBreakdownChart';
import SignalList from '../dashboard/SignalList';
import InfoGrid from '../dashboard/InfoGrid';
import Card from '../Card';
import { AlertCircle } from 'lucide-react';
import './TokenPanel.css';

export default function TokenPanel({ label, status, result, error, chainName, address }) {
  if (status === 'idle') {
    return (
      <Card className="token-panel token-panel-empty">
        <div className="token-panel-label">{label}</div>
        <p>Enter a contract address to compare.</p>
      </Card>
    );
  }

  if (status === 'loading') {
    return (
      <Card className="token-panel token-panel-loading">
        <div className="token-panel-label">{label}</div>
        <div className="token-panel-spinner" />
      </Card>
    );
  }

  if (status === 'error') {
    return (
      <Card className="token-panel token-panel-error">
        <div className="token-panel-label">{label}</div>
        <div className="token-panel-error-msg"><AlertCircle size={16} /> {error || 'Unable to analyze this contract.'}</div>
      </Card>
    );
  }

  if (!result) return null;

  return (
    <div className="token-panel-stack">
      <Card>
        <div className="token-panel-label">{label}</div>
        <div className="token-panel-header">
          <RiskGauge score={result.risk_score} riskLevel={result.risk_level} />
          <div>
            <h3 className="token-panel-name">{result.token_name || 'Unknown token'}</h3>
            <span className="token-panel-symbol">{result.token_symbol ? `$${result.token_symbol}` : ''}</span>
            <div className="token-panel-badge"><RiskBadge riskLevel={result.risk_level} /></div>
          </div>
        </div>
        <ConfidenceBar
          confidence={result.confidence}
          known={result.confidence_known_signals}
          total={result.confidence_total_signals}
        />
      </Card>

      <Card>
        <p className="token-panel-section-title">AI summary</p>
        <p className="token-panel-verdict">{result.summary}</p>
      </Card>

      <Card>
        <p className="token-panel-section-title">Score breakdown</p>
        <ScoreBreakdownChart triggeredRules={result.triggered_rules} />
      </Card>

      <Card>
        <p className="token-panel-section-title">Warning signals</p>
        <SignalList variant="warning" items={(result.triggered_rules || []).map(r => r.reason)} />
      </Card>

      <Card>
        <p className="token-panel-section-title">Positive signals</p>
        <SignalList
          variant="positive"
          items={[
            ...(result.positive_signals || []),
            ...((result.not_triggered_rules || []).map(r => r.reason)),
          ]}
        />
      </Card>

      <Card>
        <p className="token-panel-section-title">Technical details</p>
        <InfoGrid
          normalizedSignals={result.normalized_signals}
          technicalData={result.technical_data}
          chainName={chainName}
          address={address}
        />
      </Card>
    </div>
  );
}
