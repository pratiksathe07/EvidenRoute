import React from 'react';
import { BarChart3, CheckCircle2 } from 'lucide-react';
import './PagePlaceholder.css';

export const EvaluationPage: React.FC = () => {
  return (
    <div className="page-placeholder-container">
      <div className="page-placeholder-card">
        <div className="page-placeholder-header">
          <div className="page-placeholder-icon">
            <BarChart3 size={24} />
          </div>
          <div>
            <h2 className="page-placeholder-title">Evaluation</h2>
            <p className="page-placeholder-description">
              Measure context precision, recall, faithfulness, and latency across orchestrated LLM outputs.
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
