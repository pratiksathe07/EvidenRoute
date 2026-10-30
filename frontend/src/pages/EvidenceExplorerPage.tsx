import React from 'react';
import { FileSearch, CheckCircle2 } from 'lucide-react';
import './PagePlaceholder.css';

export const EvidenceExplorerPage: React.FC = () => {
  return (
    <div className="page-placeholder-container">
      <div className="page-placeholder-card">
        <div className="page-placeholder-header">
          <div className="page-placeholder-icon">
            <FileSearch size={24} />
          </div>
          <div>
            <h2 className="page-placeholder-title">Evidence Explorer</h2>
            <p className="page-placeholder-description">
              Trace provenance, inspect retrieved chunk citations, relevance confidence scores, and context graphs.
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
