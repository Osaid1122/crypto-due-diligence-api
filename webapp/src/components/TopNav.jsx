import { Menu, Search, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './TopNav.css';

export default function TopNav({ title, onMenuClick }) {
  const [query, setQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cdd-notifications')) || [
      { id: 1, title: 'Security intelligence ready', detail: 'Run a live analysis to inspect a token.', time: 'Just now', unread: true },
      { id: 2, title: 'Three networks online', detail: 'Ethereum, X Layer, and Solana analysis are available.', time: 'Today', unread: true },
    ]; } catch { return []; }
  });
  const navigate = useNavigate();
  const unread = notifications.filter(item => item.unread).length;

  function persist(next) { setNotifications(next); localStorage.setItem('cdd-notifications', JSON.stringify(next)); }

  function handleSearch(e) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    if (/^0x[a-fA-F0-9]{40}$/.test(trimmed)) {
      navigate(`/wallet/${trimmed}`);
      return;
    }
    if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed)) {
      navigate(`/wallet/${trimmed}`);
      return;
    }
    if (/^[a-zA-Z0-9.-]+\.eth$/i.test(trimmed)) {
      navigate(`/wallet/${trimmed}`);
      return;
    }
    navigate(`/dashboard?address=${trimmed}`);
  }

  return (
    <header className="topnav">
      <div className="topnav-left">
        <button className="topnav-menu-btn" onClick={onMenuClick} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <h1 className="topnav-title">{title}</h1>
      </div>

      <form className="topnav-search" onSubmit={handleSearch} role="search">
        <Search size={16} className="topnav-search-icon" aria-hidden="true" />
        <input
          type="text"
          placeholder="Search contract address…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search contract address"
        />
      </form>

      <div className="topnav-right">
        <div className="topnav-notifications">
        <button className="topnav-icon-btn topnav-bell" onClick={() => setNotificationsOpen(open => !open)} aria-label="Notifications" aria-expanded={notificationsOpen}>
          <Bell size={18} />
          {unread > 0 && <span className="topnav-unread-badge">{unread}</span>}
        </button>
        {notificationsOpen && <div className="topnav-notification-menu" role="dialog" aria-label="Notifications">
          <div className="topnav-notification-heading"><strong>Notifications</strong><span>{unread ? `${unread} unread` : 'All caught up'}</span></div>
          <div className="topnav-notification-list">{notifications.length ? notifications.map(item => <button className={`topnav-notification ${item.unread ? 'is-unread' : ''}`} key={item.id} onClick={() => persist(notifications.map(note => note.id === item.id ? { ...note, unread: false } : note))}>
            <span className="topnav-notification-dot" /><span><b>{item.title}</b><small>{item.detail}</small><time>{item.time}</time></span>
          </button>) : <p className="topnav-notification-empty">No notifications.</p>}</div>
          <div className="topnav-notification-actions"><button onClick={() => persist(notifications.map(item => ({ ...item, unread: false })))}>Mark all read</button><button onClick={() => persist([])} disabled={!notifications.length}>Clear all</button></div>
        </div>}
        </div>
      </div>
    </header>
  );
}
