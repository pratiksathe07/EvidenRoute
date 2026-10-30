import React from 'react';
import { Link } from 'react-router-dom';
import {
  Layers,
  Clock,
  Coins,
  ExternalLink,
  Sliders,
  FileSearch,
} from 'lucide-react';
import { WorkspaceExecutionResult } from '../../types/queryWorkspace';
import './ExecutionSummaryBar.css';

interface ExecutionSummaryBarProps {
  execution: WorkspaceExecutionResult;
}

export const ExecutionSummaryBar: React.FC<ExecutionSummaryBarProps> = ({ execution }) => {
  const { budgetStatus, rawRetrieveResponse } = execution;
  const selectedSourcesCount = rawRetrieveResponse?.selected_sources?.length ?? 1;
  const skippedSourcesCount = rawRetrieveResponse?.skipped_sources?.length ?? 0;
  const totalEvaluated = selectedSourcesCount + skippedSourcesCount;
  const passagesCount = execution.retrievedEvidence.length;
  const retrievalMode = rawRetrieveResponse?.retrieval_mode || 'Lexical (BM25)';

  return (
    <div className="exec-summary-bar">
      <div className="exec-summary-metric">
        <div className="exec-metric-icon icon-sources">
          <Layers size={16} />
        </div>
        <div className="exec-metric-data">
          <span className="exec-metric-label">Sources Evaluated</span>
          <span className="exec-metric-value">
            <strong>{selectedSourcesCount}</strong> / {totalEvaluated}{' '}
            <span className="exec-metric-sub">({skippedSourcesCount} skipped)</span>
          </span>
        </div>
      </div>

      <div className="exec-summary-divider" />

      <div className="exec-summary-metric">
        <div className="exec-metric-icon icon-evidence">
          <FileSearch size={16} />
        </div>
        <div className="exec-metric-data">
          <span className="exec-metric-label">Evidence Passages</span>
          <span className="exec-metric-value">
            <strong>{passagesCount}</strong> retrieved
          </span>
        </div>
      </div>

      <div className="exec-summary-divider" />

      <div className="exec-summary-metric">
        <div className="exec-metric-icon icon-latency">
          <Clock size={16} />
        </div>
        <div className="exec-metric-data">
          <span className="exec-metric-label">Pipeline Latency</span>
          <span className="exec-metric-value">
            <strong>{execution.executionTimeMs}</strong> ms
          </span>
        </div>
      </div>

      <div className="exec-summary-divider" />

      <div className="exec-summary-metric">
        <div className="exec-metric-icon icon-budget">
          <Coins size={16} />
        </div>
        <div className="exec-metric-data">
          <span className="exec-metric-label">Source Calls Quota</span>
          <span className="exec-metric-value">
            <strong>{budgetStatus.callsConsumed}</strong> / {budgetStatus.callsMax} calls
          </span>
        </div>
      </div>

      <div className="exec-summary-divider" />

      <div className="exec-summary-metric">
        <div className="exec-metric-icon icon-mode">
          <Sliders size={16} />
        </div>
        <div className="exec-metric-data">
          <span className="exec-metric-label">Retrieval Mode</span>
          <span className="exec-metric-value mode-badge">{retrievalMode}</span>
        </div>
      </div>

      <div className="exec-summary-actions">
        <Link
          to="/source-selection"
          className="exec-summary-link-btn"
          title="Inspect granular multi-factor suitability and pre-retrieval ranking on Source Selection Studio"
        >
          <span>Source Selection Studio</span>
          <ExternalLink size={13} />
        </Link>
      </div>
    </div>
  );
};
