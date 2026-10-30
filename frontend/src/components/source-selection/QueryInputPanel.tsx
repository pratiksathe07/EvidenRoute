import React from 'react';
import { Sparkles, Trash2, Search, AlertCircle, CornerDownLeft } from 'lucide-react';
import './QueryInputPanel.css';

interface QueryInputPanelProps {
  query: string;
  setQuery: (q: string) => void;
  onAnalyze: () => void;
  onClear: () => void;
  isLoading: boolean;
  validationError: string | null;
  backendError: string | null;
}

const EXAMPLE_QUERIES = [
  'Why did the payment API fail during the latest deployment?',
  'What is the refund and chargeback policy for EU enterprise accounts?',
  'Summarize recent customer escalation tickets regarding latency spikes.',
];

export const QueryInputPanel: React.FC<QueryInputPanelProps> = ({
  query,
  setQuery,
  onAnalyze,
  onClear,
  isLoading,
  validationError,
  backendError,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onAnalyze();
    }
  };

  return (
    <div className="query-input-card">
      <div className="query-input-header">
        <div className="query-header-left">
          <div className="query-icon-pill">
            <Sparkles size={16} />
          </div>
          <div>
            <h3 className="query-input-title">Context Query Formulation</h3>
            <p className="query-input-subtitle">
              Input a scenario or question to inspect pre-retrieval routing and source pruning.
            </p>
          </div>
        </div>
      </div>

      <div className="query-textarea-container">
        <textarea
          className={`query-textarea ${validationError ? 'has-error' : ''}`}
          rows={3}
          placeholder="Why did the payment API fail during the latest deployment?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <div className="query-textarea-hint">
          <span>Press</span>
          <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
          <span>to analyze</span>
        </div>
      </div>

      {/* Validation or Backend Error */}
      {validationError && (
        <div className="query-feedback-msg error">
          <AlertCircle size={14} />
          <span>{validationError}</span>
        </div>
      )}

      {backendError && (
        <div className="query-feedback-msg warning">
          <AlertCircle size={14} />
          <span>{backendError}</span>
        </div>
      )}

      {/* Example Prompt Chips */}
      <div className="query-examples-row">
        <span className="examples-label">Try example:</span>
        <div className="examples-chips">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              type="button"
              className="example-chip-btn"
              onClick={() => setQuery(example)}
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Action Controls */}
      <div className="query-actions-footer">
        <button
          type="button"
          className="btn-clear"
          onClick={onClear}
          disabled={isLoading || (!query && !backendError && !validationError)}
        >
          <Trash2 size={15} />
          <span>Clear</span>
        </button>

        <button
          type="button"
          className="btn-analyze"
          onClick={onAnalyze}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="btn-spinner" />
              <span>Analyzing Sources...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Analyze Sources</span>
              <CornerDownLeft size={14} className="enter-icon" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
