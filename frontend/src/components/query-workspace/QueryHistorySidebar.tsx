import React from 'react';
import {
  History,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Database,
  ArrowUpRight,
  Coins,
} from 'lucide-react';
import { QueryHistoryRecord } from '../../types/queryWorkspace';
import './QueryHistorySidebar.css';

interface QueryHistorySidebarProps {
  history: QueryHistoryRecord[];
  isLoading: boolean;
  onSelectQuery: (question: string) => void;
  onRefresh: () => void;
  activeQuestion?: string;
}

export const QueryHistorySidebar: React.FC<QueryHistorySidebarProps> = ({
  history,
  isLoading,
  onSelectQuery,
  onRefresh,
  activeQuestion,
}) => {
  const getOutcomeIcon = (outcome: string) => {
    switch (outcome.toUpperCase()) {
      case 'ANSWER':
        return <CheckCircle2 size={13} className="hist-icon-success" />;
      case 'CLARIFY':
        return <HelpCircle size={13} className="hist-icon-warning" />;
      case 'RETRIEVE_MORE':
        return <AlertTriangle size={13} className="hist-icon-warning" />;
      case 'ABSTAIN':
      default:
        return <XCircle size={13} className="hist-icon-error" />;
    }
  };

  const formatTimestamp = (isoStr: string) => {
    try {
      const date = new Date(isoStr);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="query-history-sidebar">
      <div className="history-sidebar-header">
        <div className="history-header-title">
          <History size={16} />
          <span>Execution History</span>
        </div>

        <div className="history-header-actions">
          <button
            type="button"
            className="history-refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh history from database (GET /api/query)"
          >
            <RotateCcw size={12} className={isLoading ? 'spin-icon' : ''} />
          </button>
        </div>
      </div>

      <div className="history-db-badge">
        <Database size={11} />
        <span>Database Persisted (GET /api/query)</span>
      </div>

      <div className="history-items-list">
        {isLoading && history.length === 0 ? (
          <div className="history-loading-state">
            <span className="history-spinner" />
            <span>Loading history...</span>
          </div>
        ) : history.length === 0 ? (
          <div className="history-empty-state">
            <p>No queries executed yet.</p>
            <span>Run a question to log execution to database.</span>
          </div>
        ) : (
          history.map((record) => {
            const isCurrent = activeQuestion?.trim() === record.question.trim();

            return (
              <div
                key={record.query_id}
                className={`history-item-card ${isCurrent ? 'item-active' : ''}`}
                onClick={() => onSelectQuery(record.question)}
                role="button"
                tabIndex={0}
                title="Click to load this query"
              >
                <div className="history-item-top">
                  <div className="history-outcome-wrap">
                    {getOutcomeIcon(record.outcome)}
                    <span className="history-outcome-label">{record.outcome}</span>
                  </div>
                  <span className="history-time">{formatTimestamp(record.created_at)}</span>
                </div>

                <p className="history-item-question">"{record.question}"</p>

                <div className="history-item-meta">
                  <span className="meta-calls">
                    <Coins size={11} />
                    {record.budget_calls_consumed} calls
                  </span>
                  <span className="meta-load-icon">
                    <ArrowUpRight size={12} />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
