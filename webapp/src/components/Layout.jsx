import { useState } from 'react';
import Sidebar from './Sidebar';
import TopNav from './TopNav';
import './Layout.css';

export default function Layout({ title, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="layout">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="layout-main">
        <TopNav title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="layout-content">
          <div className="layout-content-inner">{children}</div>
        </main>
        <footer className="layout-footer">
          {/* GoPlus attribution — required wherever GoPlus data is displayed,
              per their API license agreement. */}
          <span className="layout-footer-credit">
            Security data powered by{' '}
            <a
              href="https://gopluslabs.io"
              target="_blank"
              rel="noopener noreferrer"
              className="layout-footer-link"
            >
              GoPlus Security
            </a>
          </span>
        </footer>
      </div>
    </div>
  );
}
