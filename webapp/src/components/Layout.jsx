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
      </div>
    </div>
  );
}
