import './ConfidenceBar.css';

export default function ConfidenceBar({ confidence = 0, known, total }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="confidence-block">
      <div className="confidence-row">
        <span className="confidence-label">Data confidence</span>
        <div className="confidence-track">
          <div className="confidence-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="confidence-pct">{pct}%</span>
      </div>
      <p className="confidence-note">
        {total
          ? `Based on ${known} of ${total} security signals returned by GoPlus for this token.`
          : 'Confidence reflects how complete the available on-chain security data is.'}
      </p>
    </div>
  );
}
