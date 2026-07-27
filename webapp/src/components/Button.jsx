import { Loader2 } from 'lucide-react';
import './Button.css';

/**
 * Reusable button — variants per Part 1B spec: primary, secondary, danger, success.
 * `loading` shows a spinner and disables interaction without changing layout width.
 */
export default function Button({
  children,
  variant = 'primary',
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  fullWidth = false,
  className = '',
  ...rest
}) {
  return (
    <button
      type={type}
      className={`btn btn-${variant}${fullWidth ? ' btn-full' : ''}${className ? ` ${className}` : ''}`}
      onClick={onClick}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Loader2 className="btn-spinner" size={16} aria-hidden="true" />}
      <span>{children}</span>
    </button>
  );
}
