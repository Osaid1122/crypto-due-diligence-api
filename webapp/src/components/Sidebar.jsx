import { Link, NavLink } from 'react-router-dom';
import {
  Shield, Home, LayoutDashboard, Activity, ShieldCheck, GitCompare,
  Wallet, FileText, Info, X,
} from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/dashboard', label: 'Analysis Dashboard', icon: LayoutDashboard },
  { to: '/simulation', label: 'Attack Simulation', icon: Activity },
  { to: '/protection', label: 'Protection Advisor', icon: ShieldCheck },
  { to: '/compare', label: 'Compare Tokens', icon: GitCompare },
  { to: '/wallet', label: 'Wallet Scanner', icon: Wallet },
  { to: '/docs', label: 'API Documentation', icon: FileText },
  { to: '/about', label: 'About', icon: Info },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <div className="sidebar-scrim" onClick={onClose} aria-hidden="true" />}
      <aside className={`sidebar${open ? ' sidebar-open' : ''}`} aria-label="Primary navigation">
        <div className="sidebar-header">
          <Link className="sidebar-logo" to="/" onClick={onClose} aria-label="Crypto Due Diligence home">
            <span className="sidebar-logo-mark"><Shield size={19} strokeWidth={2.4} /></span>
            <span><b>Crypto</b> Due Diligence<small>SECURITY INTELLIGENCE</small></span>
          </Link>
          <button className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              onClick={onClose}
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-version">v1.0.0</div>
        </div>
      </aside>
    </>
  );
}
