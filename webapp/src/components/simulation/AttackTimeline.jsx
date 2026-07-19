import './AttackTimeline.css';

export default function AttackTimeline({ steps }) {
  return (
    <ol className="attack-timeline">
      {steps.map((step, i) => (
        <li key={i} className="attack-timeline-step">
          <span className="attack-timeline-dot" />
          <span className="attack-timeline-text">{step}</span>
        </li>
      ))}
    </ol>
  );
}
