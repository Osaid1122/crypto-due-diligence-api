import './Card.css';

/**
 * Base card — every major feature lives inside one of these per spec:
 * 16px radius, 1px border, 24px padding, soft shadow, hover elevation.
 */
export default function Card({ children, hoverable = false, className = '', ...rest }) {
  return (
    <div className={`card${hoverable ? ' card-hoverable' : ''} ${className}`} {...rest}>
      {children}
    </div>
  );
}
