import { useEffect, useState } from 'react';
import './RiskGauge.css';

const RISK_COLORS = {
  Low: 'var(--success)',
  Medium: 'var(--warning)',
  High: 'var(--danger)',
  Critical: '#B91C3C',
};

const RADIUS = 68;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function RiskGauge({ score = 0, riskLevel = 'Low' }) {
  const [animatedOffset, setAnimatedOffset] = useState(CIRCUMFERENCE);
  const color = RISK_COLORS[riskLevel] || RISK_COLORS.Medium;

  useEffect(() => {
    const target = CIRCUMFERENCE - (Math.min(100, Math.max(0, score)) / 100) * CIRCUMFERENCE;
    const frame = requestAnimationFrame(() => setAnimatedOffset(target));
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div className="risk-gauge">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle className="risk-gauge-track" cx="80" cy="80" r={RADIUS} />
        <circle
          className="risk-gauge-fill"
          cx="80" cy="80" r={RADIUS}
          style={{ stroke: color, strokeDasharray: CIRCUMFERENCE, strokeDashoffset: animatedOffset }}
          transform="rotate(-90 80 80)"
        />
      </svg>
      <div className="risk-gauge-center">
        <div className="risk-gauge-score" style={{ color }}>{score}</div>
        <div className="risk-gauge-max">/ 100</div>
      </div>
    </div>
  );
}

export { RISK_COLORS };
