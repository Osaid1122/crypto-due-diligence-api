import './ActionPriorityBadge.css';

const PRIORITY_COLORS = {
  Critical: '#B91C3C',
  High: 'var(--danger)',
  Medium: 'var(--warning)',
  Low: 'var(--info)',
  Informational: 'var(--text-muted)',
};

export default function ActionPriorityBadge({ priority }) {
  if (!priority) return null;
  const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Medium;
  return (
    <span className="action-priority-badge" style={{ color, background: `${color}1A`, borderColor: `${color}55` }}>
      {priority}
    </span>
  );
}
