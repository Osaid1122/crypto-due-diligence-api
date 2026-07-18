import { CheckCircle2 } from 'lucide-react';
import ActionPriorityBadge from './ActionPriorityBadge';
import './RecommendationCard.css';

export default function RecommendationCard({ text, priority }) {
  return (
    <li className="recommendation-card">
      <CheckCircle2 size={16} className="recommendation-icon" />
      <span className="recommendation-text">{text}</span>
      <ActionPriorityBadge priority={priority} />
    </li>
  );
}
