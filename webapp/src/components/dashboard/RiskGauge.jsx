import { useEffect, useState } from 'react';
import './RiskGauge.css';

const RISK_COLORS = {
  Low: 'var(--success)',
  Medium: 'var(--warning)',
  High: 'var(--danger)',
  Critical: '#B91C3C',
};

const RADIUS = 84;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function RiskGauge({ score = 0, riskLevel = 'Low' }) {
  const [animatedOffset, setAnimatedOffset] = useState(CIRCUMFERENCE);
  const [displayScore, setDisplayScore] = useState(0);
  const color = RISK_COLORS[riskLevel] || RISK_COLORS.Medium;

  useEffect(() => {
    const target = CIRCUMFERENCE - (Math.min(100, Math.max(0, score)) / 100) * CIRCUMFERENCE;
    const frame = requestAnimationFrame(() => setAnimatedOffset(target));
    return () => cancelAnimationFrame(frame);
  }, [score]);

  useEffect(() => {
    const target = Math.min(100, Math.max(0, Number(score) || 0));
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplayScore(target);
      return undefined;
    }
    const startedAt = performance.now();
    let frame;
    const animate = now => {
      const progress = Math.min(1, (now - startedAt) / 900);
      setDisplayScore(Math.round(target * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div className="risk-gauge">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <circle className="risk-gauge-track" cx="100" cy="100" r={RADIUS} />
        <circle
          className="risk-gauge-fill"
          cx="100" cy="100" r={RADIUS}
          style={{ stroke: color, strokeDasharray: CIRCUMFERENCE, strokeDashoffset: animatedOffset }}
          transform="rotate(-90 100 100)"
        />
      </svg>
      <div className="risk-gauge-center">
        <div className="risk-gauge-score" style={{ color }}>{displayScore}</div>
        <div className="risk-gauge-max">/ 100</div>
      </div>
    </div>
  );
}

export { RISK_COLORS };
