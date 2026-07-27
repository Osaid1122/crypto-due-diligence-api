import { CheckCircle2, ExternalLink } from 'lucide-react';
import ActionPriorityBadge from './ActionPriorityBadge';
import './RecommendationCard.css';

export default function RecommendationCard({ text, priority, resources = [] }) {
  return (
    <li className="recommendation-card">
      <CheckCircle2 size={16} className="recommendation-icon" />
      <div className="recommendation-content"><span className="recommendation-text">{text}</span>{resources.length > 0 && <div className="recommendation-resources">{resources.map(resource => <a key={resource.href} href={resource.href} target="_blank" rel="noopener noreferrer">{resource.label}<ExternalLink size={11} /></a>)}</div>}</div>
      <ActionPriorityBadge priority={priority} />
    </li>
  );
}
