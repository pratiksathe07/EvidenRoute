import React from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Terminal,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { QueryRunItem } from '../../types/dashboard';
import './RecentQueries.css';

interface RecentQueriesProps {
  queries: QueryRunItem[];
  isLoading?: boolean;
}

export const RecentQueries: React.FC<RecentQueriesProps> = ({
  queries,
  isLoading = false,
}) => {
  const hasQueries = queries && queries.length > 0;

  const renderStatusBadge = (status: QueryRunItem['answerStatus']) => {
    switch (status) {
      case 'verified':
        return (
          <span className="status-badge verified">
            <ShieldCheck size={12} />
            <span>Verified</span>
          </span>
        );
      case 'reliable':
        return (
          <span className="status-badge reliable">
            <CheckCircle size={12} />
            <span>Reliable</span>
          </span>
        );
      case 'partial':
        return (
          <span className="status-badge partial">
            <AlertTriangle size={12} />
            <span>Partial Context</span>
          </span>
        );
      case 'failed':
      default:
        return (
          <span className="status-badge failed">
            <XCircle size={12} />
            <span>Failed</span>
          </span>
        );
    }
  };

  return (
    <div className="recent-queries-card">
      <div className="recent-queries-header">
        <div>
          <h3 className="recent-queries-title">Recent Query Runs</h3>
          <p className="recent-queries-subtitle">
            Auditable trail of context orchestration runs, evidence counts, and answer reliability.
          </p>
        </div>
        <div className="recent-queries-counter">
          <History size={13} />
          <span>{hasQueries ? `${queries.length} Runs` : '0 Runs Recorded'}</span>
        </div>
      </div>

      <div className="recent-queries-content">
        {isLoading ? (
          <div className="queries-loading-state">
            <span className="queries-spinner" />
            <p>Loading recent orchestration runs...</p>
          </div>
        ) : hasQueries ? (
          <div className="table-responsive-container">
            <table className="queries-table">
              <thead>
                <tr>
                  <th>Query</th>
                  <th>Selected Sources</th>
                  <th>Evidence</th>
                  <th>Budget Used</th>
                  <th>Answer Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {queries.map((q) => (
                  <tr key={q.id}>
                    <td className="cell-query font-medium">{q.query}</td>
                    <td className="cell-sources">
                      <div className="source-tags-wrap">
                        {q.selectedSources.map((src, i) => (
                          <span key={i} className="source-chip">
                            {src}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="cell-evidence font-mono">{q.evidenceCount} items</td>
                    <td className="cell-budget font-mono">{q.budgetUsed}</td>
                    <td className="cell-status">{renderStatusBadge(q.answerStatus)}</td>
                    <td className="cell-timestamp font-mono">{q.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Thoughtful Empty State when no query history exists */
          <div className="queries-empty-state">
            <div className="queries-empty-icon-wrapper">
              <Terminal size={24} className="queries-empty-icon" />
            </div>
            <h4 className="queries-empty-title">No Query Runs Recorded Yet</h4>
            <p className="queries-empty-text">
              Context orchestration records, source routing decisions, and evidence verification scores will populate here as questions are processed.
            </p>
            <Link to="/query-workspace" className="queries-empty-action-btn">
              <span>Open Query Workspace</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
