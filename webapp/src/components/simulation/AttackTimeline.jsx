import { AlertTriangle, ArrowDownRight, CircleDollarSign, Eye, ShieldAlert, Target, TrendingDown, WalletCards } from 'lucide-react';
import './AttackTimeline.css';

function iconForStep(step, index) {
  const text = step.toLowerCase();
  if (text.includes('wallet') || text.includes('holder')) return WalletCards;
  if (text.includes('sell') || text.includes('fund') || text.includes('supply')) return CircleDollarSign;
  if (text.includes('liquidity') || text.includes('pressure') || text.includes('volatility')) return TrendingDown;
  if (text.includes('risk') || text.includes('detected')) return Eye;
  if (text.includes('outcome') || text.includes('locked')) return AlertTriangle;
  return index === 0 ? Eye : index === 1 ? Target : ShieldAlert;
}

export default function AttackTimeline({ steps, tone = 'medium' }) {
  return <ol className={`attack-timeline attack-timeline--${tone}`}>
    {steps.map((step, i) => { const Icon = iconForStep(step, i); return <li key={i} className="attack-timeline-step"><div className="attack-timeline-node"><Icon size={22} /><span>{String(i + 1).padStart(2, '0')}</span></div><div className="attack-timeline-content"><span>Attack event</span><strong>{step}</strong></div>{i < steps.length - 1 && <ArrowDownRight className="attack-timeline-arrow" size={21} />}</li>; })}
  </ol>;
}
