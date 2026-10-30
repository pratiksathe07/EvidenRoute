import React, { useEffect, useRef } from 'react';
import { Send, RotateCcw, Sparkles, Terminal, CornerDownLeft, AlertCircle } from 'lucide-react';
import './WorkspaceQueryInput.css';

interface WorkspaceQueryInputProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (question: string) => void;
  onClear: () => void;
  isLoading: boolean;
  validationError?: string | null;
  backendError?: string | null;
}

const EXAMPLE_QUERIES = [
  {
    label: 'Payment API Failure',
    query: 'Why did the payment API fail after deployment?',
    category: 'Ticket & Incident',
  },
  {
    label: 'Product Planning Decision',
    query: 'What was decided during the last product planning meeting?',
    category: 'Conversation',
  },
  {
    label: 'DB Connection Timeout',
    query: 'What caused the database connection timeout?',
    category: 'PostgreSQL Alert',
  },
  {
    label: 'Employee Leave Policy',
    query: 'What is the employee leave policy?',
    category: 'HR Document',
  },
];

export const WorkspaceQueryInput: React.FC<WorkspaceQueryInputProps> = ({
  query,
  setQuery,
  onSubmit,
  onClear,
  isLoading,
  validationError,
  backendError,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (!isLoading && query.trim()) {
        onSubmit(query.trim());
      }
    }
  };

  const handleSelectExample = (exampleQuery: string) => {
    setQuery(exampleQuery);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="workspace-input-card">
      <div className="workspace-input-header">
        <div className="workspace-input-badge">
          <Terminal size={14} />
          <span>Natural Language Query</span>
        </div>
        <span className="workspace-input-shortcut-hint">
          Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to run
        </span>
      </div>

      <div className={`workspace-textarea-wrapper ${validationError ? 'has-error' : ''}`}>
        <textarea
          ref={textareaRef}
          className="workspace-textarea"
          placeholder="Ask any question grounded across documents, conversations, and incident tickets..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={2}
          id="workspace-query-textarea"
        />

        <div className="workspace-input-actions">
          {query.trim().length > 0 && (
            <button
              type="button"
              className="workspace-btn-clear"
              onClick={onClear}
              disabled={isLoading}
              title="Clear input"
              id="workspace-clear-btn"
            >
              <RotateCcw size={14} />
              <span>Clear</span>
            </button>
          )}

          <button
            type="button"
            className="workspace-btn-submit"
            onClick={() => onSubmit(query.trim())}
            disabled={isLoading || !query.trim()}
            id="workspace-submit-btn"
          >
            {isLoading ? (
              <>
                <span className="workspace-spinner" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Send size={14} />
                <span>Run Query</span>
                <CornerDownLeft size={12} className="btn-shortcut-icon" />
              </>
            )}
          </button>
        </div>
      </div>

      {validationError && (
        <div className="workspace-input-error">
          <AlertCircle size={14} />
          <span>{validationError}</span>
        </div>
      )}

      {backendError && (
        <div className="workspace-backend-error">
          <AlertCircle size={14} />
          <span>{backendError}</span>
        </div>
      )}

      {/* Example Suggestions */}
      <div className="workspace-examples-container">
        <div className="workspace-examples-label">
          <Sparkles size={13} />
          <span>Try verified dataset scenarios:</span>
        </div>
        <div className="workspace-examples-pills">
          {EXAMPLE_QUERIES.map((item, idx) => (
            <button
              key={idx}
              type="button"
              className="workspace-example-pill"
              onClick={() => handleSelectExample(item.query)}
              disabled={isLoading}
              title={item.query}
            >
              <span className="example-pill-category">{item.category}:</span>
              <span className="example-pill-title">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
