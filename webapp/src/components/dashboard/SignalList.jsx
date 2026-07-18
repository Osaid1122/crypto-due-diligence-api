import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import './SignalList.css';

export default function SignalList({ items, variant }) {
  const Icon = variant === 'warning' ? AlertTriangle : CheckCircle2;
  const iconClass = variant === 'warning' ? 'signal-icon-warn' : 'signal-icon-ok';

  if (!items.length) {
    return <p className="signal-empty">No {variant === 'warning' ? 'warning' : 'positive'} signals detected.</p>;
  }

  return (
    <ul className="signal-list">
      {items.map((text, i) => (
        <li key={i}>
          <Icon size={16} className={iconClass} />
          <span>{text}</span>
        </li>
      ))}
    </ul>
  );
}
