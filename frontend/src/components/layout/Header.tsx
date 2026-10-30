import React from 'react';
import { Search, Activity, Menu, Bell, User } from 'lucide-react';
import './Header.css';

interface HeaderProps {
  pageTitle: string;
  onToggleMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  pageTitle,
  onToggleMobileMenu,
}) => {
  return (
    <header className="app-header">
      {/* Left Section: Mobile Menu Toggle & Dynamic Page Title */}
      <div className="header-left">
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={onToggleMobileMenu}
          aria-label="Open mobile menu"
        >
          <Menu size={20} />
        </button>
        <h1 className="header-page-title">{pageTitle}</h1>
      </div>

      {/* Center Section: Visual Search Field */}
      <div className="header-search">
        <div className="search-input-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search queries, sources, evidence..."
            readOnly
          />
          <span className="search-shortcut">Ctrl K</span>
        </div>
      </div>

      {/* Right Section: System Status & Profile */}
      <div className="header-right">
        {/* System Status Indicator */}
        <div className="system-status-badge standby" title="Engine client mode initialized. Awaiting backend connection.">
          <span className="status-pulse-dot standby" />
          <Activity size={14} className="status-icon" />
          <span className="status-label">Engine Standby</span>
        </div>

        {/* Notifications (visual placeholder) */}
        <button
          type="button"
          className="header-icon-btn"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell size={18} />
          <span className="notification-dot" />
        </button>

        {/* User Profile Placeholder */}
        <div className="user-profile-badge">
          <div className="user-avatar">
            <User size={16} />
          </div>
          <div className="user-info">
            <span className="user-name">Member 3</span>
            <span className="user-role">Frontend Dev</span>
          </div>
        </div>
      </div>
    </header>
  );
};
