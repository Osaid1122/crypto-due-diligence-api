import { AlertTriangle } from 'lucide-react';
import './ActionPriorityBadge.css';

const PRIORITY_COLORS = {
  Critical: '#B91C3C',
  High: '#F97316',
  Medium: 'var(--warning)',
  Low: 'var(--info)',
  Informational: 'var(--text-muted)',
};

export default function ActionPriorityBadge({ priority }) {
  if (!priority) return null;
  const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Medium;
  return (
    <span
      className={`action-priority-badge priority-${priority?.toLowerCase()}`}
      style={{ color, background: `${color}22`, borderColor: `${color}55` }}
    >
      {priority === 'High' ? <AlertTriangle size={14} /> : null}
      {priority}
    </span>
  );
}
