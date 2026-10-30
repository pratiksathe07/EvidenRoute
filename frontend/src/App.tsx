import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { QueryWorkspacePage } from './pages/QueryWorkspacePage';
import { SourceSelectionPage } from './pages/SourceSelectionPage';
import { EvidenceExplorerPage } from './pages/EvidenceExplorerPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          {/* Default redirect to Dashboard */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          
          {/* Primary Navigation Routes */}
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="query-workspace" element={<QueryWorkspacePage />} />
          <Route path="source-selection" element={<SourceSelectionPage />} />
          <Route path="evidence-explorer" element={<EvidenceExplorerPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="settings" element={<SettingsPage />} />

          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
