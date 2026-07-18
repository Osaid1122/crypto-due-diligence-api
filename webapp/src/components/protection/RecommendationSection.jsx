import Card from '../Card';
import RecommendationCard from './RecommendationCard';
import './RecommendationSection.css';

export default function RecommendationSection({ title, items }) {
  return (
    <Card>
      <h3 className="recommendation-section-title">{title}</h3>
      {items.length ? (
        <ul className="recommendation-section-list">
          {items.map((item, i) => (
            <RecommendationCard key={i} text={item.text} priority={item.priority} />
          ))}
        </ul>
      ) : (
        <p className="recommendation-section-empty">Nothing flagged in this category.</p>
      )}
    </Card>
  );
}
