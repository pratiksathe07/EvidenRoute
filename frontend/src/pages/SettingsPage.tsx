import React from 'react';
import { Settings, CheckCircle2 } from 'lucide-react';
import './PagePlaceholder.css';

export const SettingsPage: React.FC = () => {
  return (
    <div className="page-placeholder-container">
      <div className="page-placeholder-card">
        <div className="page-placeholder-header">
          <div className="page-placeholder-icon">
            <Settings size={24} />
          </div>
          <div>
            <h2 className="page-placeholder-title">Settings</h2>
            <p className="page-placeholder-description">
              Configure engine thresholds, vector indices, model routing parameters, and API credentials.
            </p>
          </div>
        </div>

        <div className="page-status-badge">
          <CheckCircle2 size={14} />
          <span>Step 1 Layout Ready • Ready for Feature Implementation</span>
        </div>
      </div>
    </div>
  );
};
