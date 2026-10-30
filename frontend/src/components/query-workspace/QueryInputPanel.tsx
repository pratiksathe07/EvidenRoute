import React from 'react';
import { Sparkles, Trash2, Search, AlertCircle, CornerDownLeft } from 'lucide-react';
import './QueryInputPanel.css';

interface QueryInputPanelProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: () => void;
  onClear: () => void;
  isLoading: boolean;
  validationError: string | null;
  apiError: string | null;
}

const EXAMPLE_QUERIES = [
  'Why did the payment API fail after deployment?',
  'What is the database connection timeout limit?',
  'What is the annual leave rollover policy?',
  'How do quantum teleportation warp drives operate on Mars?',
];

export const QueryInputPanel: React.FC<QueryInputPanelProps> = ({
  query,
  setQuery,
  onSubmit,
  onClear,
  isLoading,
  validationError,
  apiError,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!isLoading && query.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="qw-input-card">
      <div className="qw-input-header">
        <div className="qw-header-left">
          <div className="qw-icon-pill">
            <Sparkles size={16} />
          </div>
          <div>
            <h3 className="qw-input-title">Contextual Query Orchestration</h3>
            <p className="qw-input-subtitle">
              Dispatch natural language inquiries to initiate pre-retrieval source selection, bounded retrieval, and 4D evidence evaluation.
            </p>
          </div>
        </div>
      </div>

      <div className="qw-textarea-container">
        <textarea
          className={`qw-textarea ${validationError ? 'has-error' : ''}`}
          rows={3}
          placeholder="e.g. Why did the payment API fail after deployment?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <div className="qw-textarea-hint">
          <span>Press</span>
          <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
          <span>to retrieve</span>
        </div>
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="qw-feedback-msg error">
          <AlertCircle size={15} />
          <span>{validationError}</span>
        </div>
      )}

      {/* API / Backend Connection Error */}
      {apiError && (
        <div className="qw-feedback-msg warning">
          <AlertCircle size={15} />
          <span>{apiError}</span>
        </div>
      )}

      {/* Example Prompt Chips */}
      <div className="qw-examples-row">
        <span className="qw-examples-label">Try benchmark questions:</span>
        <div className="qw-examples-chips">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              type="button"
              className="qw-example-chip"
              onClick={() => setQuery(example)}
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Action Footer */}
      <div className="qw-actions-footer">
        <button
          type="button"
          className="btn-qw-clear"
          onClick={onClear}
          disabled={isLoading || (!query && !apiError && !validationError)}
        >
          <Trash2 size={15} />
          <span>Clear</span>
        </button>

        <button
          type="button"
          className="btn-qw-submit"
          onClick={onSubmit}
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <>
              <span className="qw-spinner" />
              <span>Retrieving & Scoring Evidence...</span>
            </>
          ) : (
            <>
              <Search size={16} />
              <span>Run Query & Retrieve Evidence</span>
              <CornerDownLeft size={14} className="qw-enter-icon" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
