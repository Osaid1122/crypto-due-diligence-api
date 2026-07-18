import { NavLink } from 'react-router-dom';
import {
  Shield, LayoutDashboard, Activity, ShieldCheck, GitCompare,
  Wallet, FileText, Info, Code2, Sun, Moon, X,
} from 'lucide-react';
import { useState } from 'react';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/simulation', label: 'Attack Simulation', icon: Activity },
  { to: '/protection', label: 'Protection Advisor', icon: ShieldCheck },
  { to: '/compare', label: 'Compare Tokens', icon: GitCompare },
  { to: '/wallet', label: 'Wallet Scanner', icon: Wallet },
  { to: '/docs', label: 'API Documentation', icon: FileText },
  { to: '/about', label: 'About', icon: Info },
];

export default function Sidebar({ open, onClose }) {
  const [dark, setDark] = useState(true);

  return (
    <>
      {open && <div className="sidebar-scrim" onClick={onClose} aria-hidden="true" />}
      <aside className={`sidebar${open ? ' sidebar-open' : ''}`} aria-label="Primary navigation">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Shield size={22} strokeWidth={2.2} />
            <span>Crypto Due Diligence</span>
          </div>
          <button className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              onClick={onClose}
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="sidebar-footer-link"
          >
            <Code2 size={16} />
            <span>GitHub Repository</span>
          </a>
          <button className="sidebar-footer-link" onClick={() => setDark(d => !d)}>
            {dark ? <Sun size={16} /> : <Moon size={16} />}
            <span>Theme Toggle</span>
          </button>
          <div className="sidebar-version">v1.0.0</div>
        </div>
      </aside>
    </>
  );
}
