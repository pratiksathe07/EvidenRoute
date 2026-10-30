import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { QueryWorkspacePage } from './pages/QueryWorkspacePage';
import { ResourceRankingPage } from './pages/ResourceRankingPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { EvidenceExplorerPage } from './pages/EvidenceExplorerPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          {/* Default redirect to Dashboard */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          
          {/* Exactly Six Primary Navigation Routes */}
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="query-workspace" element={<QueryWorkspacePage />} />
          <Route path="resource-ranking" element={<ResourceRankingPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="evidence-explorer" element={<EvidenceExplorerPage />} />
          <Route path="settings" element={<SettingsPage />} />

          {/* Legacy route alias for backwards compatibility */}
          <Route path="source-selection" element={<Navigate to="/resource-ranking" replace />} />

          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
