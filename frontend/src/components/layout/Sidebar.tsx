import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Terminal,
  Database,
  FileSearch,
  BarChart3,
  Settings,
  Route,
  ChevronLeft,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { NavItem } from '../../types/navigation';
import './Sidebar.css';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  isMobileOpen: boolean;
  closeMobileMenu: () => void;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { id: 'query-workspace', label: 'Query Workspace', path: '/query-workspace', icon: Terminal },
  { id: 'source-selection', label: 'Source Selection', path: '/source-selection', icon: Database },
  { id: 'evidence-explorer', label: 'Evidence Explorer', path: '/evidence-explorer', icon: FileSearch },
  { id: 'evaluation', label: 'Evaluation', path: '/evaluation', icon: BarChart3 },
  { id: 'settings', label: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  closeMobileMenu,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div className="sidebar-mobile-backdrop" onClick={closeMobileMenu} />
      )}

      <aside
        className={`app-sidebar ${isCollapsed ? 'collapsed' : ''} ${
          isMobileOpen ? 'mobile-open' : ''
        }`}
      >
        {/* Brand / Logo Area */}
        <div className="sidebar-brand">
          <div className="brand-logo-container">
            <div className="brand-logo-icon">
              <Route className="logo-svg" size={22} />
            </div>
            {!isCollapsed && (
              <div className="brand-text">
                <span className="brand-title">
                  Eviden<span className="brand-accent">Route</span>
                </span>
                <span className="brand-subtitle">Context Selection Engine</span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">
            {!isCollapsed ? 'ORCHESTRATION' : '•••'}
          </div>
          <ul className="nav-list">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.id} className="nav-item">
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `nav-link ${isActive ? 'active' : ''}`
                    }
                    onClick={closeMobileMenu}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <Icon className="nav-icon" size={20} />
                    {!isCollapsed && <span className="nav-label">{item.label}</span>}
                    {!isCollapsed && item.badge && (
                      <span className="nav-badge">{item.badge}</span>
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Engine Status Badge (Sidebar Footer) */}
        {!isCollapsed && (
          <div className="sidebar-footer-card">
            <div className="engine-status-header">
              <ShieldCheck size={16} className="engine-icon" />
              <span>EvidenRoute Core</span>
            </div>
            <p className="engine-status-text">v1.0.0-alpha • Context Active</p>
          </div>
        )}

        {/* Collapse / Expand Toggle Button */}
        <button
          type="button"
          className="sidebar-collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </aside>
    </>
  );
};
