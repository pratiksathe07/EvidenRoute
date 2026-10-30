import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  XCircle,
  MinusCircle,
  ChevronDown,
  ChevronUp,
  Activity,
} from 'lucide-react';
import { PipelineStageInfo, StageStatus } from '../../types/queryWorkspace';
import './PipelineStageTracker.css';

interface PipelineStageTrackerProps {
  stages: PipelineStageInfo[];
  isLoading: boolean;
}

export const PipelineStageTracker: React.FC<PipelineStageTrackerProps> = ({
  stages,
  isLoading,
}) => {
  const [expandedStageId, setExpandedStageId] = useState<string | null>(null);

  const toggleStage = (id: string) => {
    setExpandedStageId((prev) => (prev === id ? null : id));
  };

  const getStatusIcon = (status: StageStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={16} className="stage-icon-completed" />;
      case 'running':
        return <span className="stage-running-dot" />;
      case 'skipped':
        return <MinusCircle size={16} className="stage-icon-skipped" />;
      case 'failed':
        return <XCircle size={16} className="stage-icon-failed" />;
      case 'pending':
      default:
        return <Clock size={16} className="stage-icon-pending" />;
    }
  };

  const getStatusBadge = (status: StageStatus) => {
    switch (status) {
      case 'completed':
        return <span className="stage-badge badge-completed">Completed</span>;
      case 'running':
        return <span className="stage-badge badge-running">Executing</span>;
      case 'skipped':
        return <span className="stage-badge badge-skipped">Skipped (Unconfigured)</span>;
      case 'failed':
        return <span className="stage-badge badge-failed">Failed</span>;
      case 'pending':
      default:
        return <span className="stage-badge badge-pending">Pending</span>;
    }
  };

  return (
    <div className="pipeline-tracker-card">
      <div className="pipeline-tracker-header">
        <div className="pipeline-header-title">
          <Activity size={18} />
          <h3>Execution Pipeline Visualization</h3>
          {isLoading && <span className="pipeline-running-pill">Pipeline Active</span>}
          <span className="pipeline-stage-count">
            {stages.filter((s) => s.status === 'completed').length} / {stages.length} Completed
          </span>
        </div>
        <p className="pipeline-header-subtitle">
          Real-time deterministic execution trace through query understanding, source selection, 4D scoring, conflict checking, and context pruning.
        </p>
      </div>

      <div className="pipeline-stages-flow">
        {stages.map((stage, index) => {
          const isExpanded = expandedStageId === stage.id;

          return (
            <div
              key={stage.id}
              className={`pipeline-stage-item status-${stage.status} ${isExpanded ? 'is-expanded' : ''}`}
            >
              <div
                className="stage-summary-row"
                onClick={() => toggleStage(stage.id)}
                role="button"
                tabIndex={0}
              >
                <div className="stage-number-col">
                  <div className="stage-indicator-circle">
                    {getStatusIcon(stage.status)}
                  </div>
                  {index < stages.length - 1 && <div className="stage-connector-line" />}
                </div>

                <div className="stage-content-col">
                  <div className="stage-title-row">
                    <div className="stage-index-tag">Stage {index + 1}</div>
                    <h4 className="stage-name">{stage.name}</h4>
                    {getStatusBadge(stage.status)}
                    {stage.durationMs !== undefined && stage.durationMs > 0 && (
                      <span className="stage-duration">{stage.durationMs.toFixed(1)} ms</span>
                    )}
                  </div>

                  <p className="stage-description">{stage.description}</p>

                  {stage.summary && (
                    <div className="stage-runtime-summary">
                      <span className="summary-label">Trace:</span> {stage.summary}
                    </div>
                  )}
                </div>

                <div className="stage-toggle-col">
                  {stage.details && (
                    <button
                      type="button"
                      className="stage-chevron-btn"
                      aria-label={isExpanded ? 'Collapse technical details' : 'Expand technical details'}
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  )}
                </div>
              </div>

              {/* Technical Details Accordion */}
              {isExpanded && stage.details && (
                <div className="stage-details-dropdown">
                  <div className="details-header">
                    <span>Technical Stage Metadata</span>
                  </div>
                  <pre className="details-json">
                    {JSON.stringify(stage.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
