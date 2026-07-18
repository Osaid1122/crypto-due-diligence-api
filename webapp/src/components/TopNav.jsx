import { Menu, Search, Bell, Code2, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './TopNav.css';

export default function TopNav({ title, onMenuClick }) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  function handleSearch(e) {
    e.preventDefault();
    const trimmed = query.trim();
    if (/^0x[a-fA-F0-9]{40}$/.test(trimmed)) {
      navigate(`/dashboard?address=${trimmed}`);
    }
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
        <button className="topnav-icon-btn" aria-label="Notifications">
          <Bell size={18} />
        </button>
        <a
          className="topnav-icon-btn"
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub repository"
        >
          <Code2 size={18} />
        </a>
        <button className="topnav-icon-btn topnav-profile" aria-label="Profile menu">
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
