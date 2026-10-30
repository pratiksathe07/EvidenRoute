import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import './MainLayout.css';

// Route path to user-friendly page title mapping
const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/query-workspace': 'Query Workspace',
  '/source-selection': 'Source Selection',
  '/evidence-explorer': 'Evidence Explorer',
  '/evaluation': 'Evaluation',
  '/settings': 'Settings',
};

export const MainLayout: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false);
  const location = useLocation();

  const currentTitle = PAGE_TITLES[location.pathname] || 'EvidenRoute Engine';

  return (
    <div className="main-layout-container">
      {/* Sidebar Navigation */}
      <Sidebar
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        isMobileOpen={isMobileOpen}
        closeMobileMenu={() => setIsMobileOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-content-wrapper">
        <Header
          pageTitle={currentTitle}
          onToggleMobileMenu={() => setIsMobileOpen((prev) => !prev)}
        />

        <main className="page-content-scrollable">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
