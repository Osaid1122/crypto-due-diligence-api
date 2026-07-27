import Card from '../Card';
import RecommendationCard from './RecommendationCard';
import './RecommendationSection.css';

export default function RecommendationSection({ title, items, step, description, icon: Icon, className = '', resourcesForItem }) {
  return (
    <Card className={`recommendation-section ${className}`}>
      <div className="recommendation-section-heading"><div>{Icon && <Icon size={18} />}{step && <span>{step}</span>}<h3 className="recommendation-section-title">{title}</h3></div>{description && <p>{description}</p>}</div>
      {items.length ? (
        <ul className="recommendation-section-list">
          {items.map((item, i) => (
            <RecommendationCard key={i} text={item.text} priority={item.priority} resources={resourcesForItem?.(item) || []} />
          ))}
        </ul>
      ) : (
        <p className="recommendation-section-empty">Nothing flagged in this category.</p>
      )}
    </Card>
  );
}
