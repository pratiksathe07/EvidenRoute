import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  RotateCw,
  AlertCircle,
  X,
  FileSearch,
} from 'lucide-react';
import { RetrieveResponse, RetrievalHealthResponse } from '../types/retrieval';
import { SourceMetadata } from '../types/sourceSelection';
import { retrieveEvidence, getRetrievalHealth } from '../services/retrievalService';
import { getAvailableSources } from '../services/sourceSelectionService';

import { QueryInputPanel } from '../components/query-workspace/QueryInputPanel';
import { QuerySummary } from '../components/query-workspace/QuerySummary';
import { SourceResultsPanel } from '../components/query-workspace/SourceResultsPanel';
import { EvidenceList } from '../components/query-workspace/EvidenceList';
import { DecisionTracePanel } from '../components/query-workspace/DecisionTracePanel';
import { InsufficientEvidenceNotice } from '../components/query-workspace/InsufficientEvidenceNotice';
import { ConflictInspector } from '../components/query-workspace/ConflictInspector';

import './QueryWorkspacePage.css';

const DEFAULT_QUERY = 'Why did the payment API fail after deployment?';

export const QueryWorkspacePage: React.FC = () => {
  // Query state
  const [query, setQuery] = useState<string>(DEFAULT_QUERY);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // Response state
  const [retrievalResult, setRetrievalResult] = useState<RetrieveResponse | null>(null);
  const [lastExecutedQuery, setLastExecutedQuery] = useState<string | null>(null);

  // Auxiliary backend state
  const [availableSources, setAvailableSources] = useState<SourceMetadata[]>([]);
  const [healthStatus, setHealthStatus] = useState<RetrievalHealthResponse | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);

  // Prevent duplicate concurrent submissions
  const isExecutingRef = useRef<boolean>(false);

  // Initial load: Fetch sources metadata and probe retrieval subsystem health
  const loadDiagnostics = useCallback(async () => {
    try {
      const [sourcesRes, healthRes] = await Promise.all([
        getAvailableSources(),
        getRetrievalHealth(),
      ]);

      if (sourcesRes.data) {
        setAvailableSources(sourcesRes.data);
      }

      if (healthRes.data) {
        setHealthStatus(healthRes.data);
        setIsBackendHealthy(healthRes.data.status === 'healthy' || healthRes.isAvailable);
      } else {
        setIsBackendHealthy(sourcesRes.isAvailable);
      }
    } catch {
      setIsBackendHealthy(false);
    }
  }, []);

  useEffect(() => {
    loadDiagnostics();
  }, [loadDiagnostics]);

  // Main submission handler
  const handleRunQuery = async () => {
    const trimmed = query.trim();

    if (!trimmed) {
      setValidationError('Please enter a query or question before executing retrieval.');
      return;
    }

    if (isExecutingRef.current) {
      return;
    }

    setValidationError(null);
    setApiError(null);
    setIsLoading(true);
    isExecutingRef.current = true;

    try {
      const response = await retrieveEvidence({
        question: trimmed,
        top_k: 10,
        selection_config: null,
        retrieval_config: null,
      });

      if (response.data) {
        // Success: replace previous result
        setRetrievalResult(response.data);
        setLastExecutedQuery(trimmed);
        setApiError(null);
      } else {
        // Failure: preserve previous result, show error clearly
        setApiError(
          response.error ||
            'The retrieval engine failed to process your inquiry. Please ensure the backend is active.'
        );
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An unexpected network error occurred.';
      setApiError(msg);
    } finally {
      setIsLoading(false);
      isExecutingRef.current = false;
    }
  };

  const handleClearQuery = () => {
    setQuery('');
    setValidationError(null);
  };

  const handleSelectExample = (example: string) => {
    setQuery(example);
    setValidationError(null);
  };

  return (
    <div className="qw-page-container">
      {/* 1. Page Header */}
      <header className="qw-page-header">
        <div className="qw-page-title-group">
          <div className="qw-badge-row">
            <span className="qw-step-badge">Step 4 Engine</span>
            <span className={`qw-status-pill ${isBackendHealthy ? 'online' : 'offline'}`}>
              <span className={`status-indicator-dot ${isBackendHealthy ? 'pulse' : ''}`} />
              <span>
                {isBackendHealthy
                  ? healthStatus?.bm25_status === 'ready'
                    ? 'Retrieval Subsystem Online (BM25 Ready)'
                    : 'Backend Online'
                  : 'Backend Offline'}
              </span>
            </span>
          </div>

          <h1 className="qw-page-title">Query Workspace & Evidence Retrieval</h1>
          <p className="qw-page-subtitle">
            Enter a natural-language question to orchestrate context sources, retrieve grounded evidence
            passages, and inspect explainable 4D scoring traces.
          </p>
        </div>

        <div className="qw-header-actions">
          <button
            type="button"
            className="qw-reload-btn"
            onClick={loadDiagnostics}
            title="Refresh backend subsystem diagnostics"
          >
            <RotateCw size={14} />
            <span>Sync Engine</span>
          </button>
        </div>
      </header>

      {/* 2. Top API Error Banner (if error occurred, preserves previous result below) */}
      {apiError && (
        <div className="qw-alert-banner" role="alert">
          <div className="qw-alert-icon">
            <AlertCircle size={20} />
          </div>
          <div className="qw-alert-content">
            <div className="qw-alert-title">Retrieval Query Failed</div>
            <div className="qw-alert-desc">{apiError}</div>
          </div>
          <button
            type="button"
            className="qw-alert-dismiss"
            onClick={() => setApiError(null)}
            aria-label="Dismiss error"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* 3. Query Input Section */}
      <QueryInputPanel
        query={query}
        setQuery={setQuery}
        onSubmit={handleRunQuery}
        onClear={handleClearQuery}
        isLoading={isLoading}
        validationError={validationError}
        apiError={apiError}
      />

      {/* 4. Query Execution Results or Initial Empty State */}
      {retrievalResult ? (
        <main className="qw-results-container" aria-label="Query Retrieval Results">
          {/* Section F: Insufficient Evidence or Abstention Notice */}
          <InsufficientEvidenceNotice
            readiness={retrievalResult.answer_readiness}
            sufficiency={retrievalResult.sufficiency}
          />

          {/* Section F: Detected Contradictions & Divergences */}
          {retrievalResult.conflicts && retrievalResult.conflicts.length > 0 && (
            <ConflictInspector conflicts={retrievalResult.conflicts} />
          )}

          {/* 2-Column Grid: Section B (Query Summary) & Section C (Source Routing) */}
          <div className="qw-two-col-grid">
            {/* Section B: Query Execution Summary */}
            <QuerySummary response={retrievalResult} />

            {/* Section C: Selected and Skipped Sources */}
            <SourceResultsPanel
              selectedSources={retrievalResult.selected_sources}
              skippedSources={retrievalResult.skipped_sources}
              allAvailableSources={availableSources}
            />
          </div>

          {/* Section D: Retrieved Evidence Panel */}
          <EvidenceList
            evidence={retrievalResult.retrieved_evidence || []}
            hasExecuted={Boolean(lastExecutedQuery)}
            isLoading={isLoading}
          />

          {/* Section E: Decision Trace Panel */}
          {retrievalResult.decision_trace && (
            <DecisionTracePanel trace={retrievalResult.decision_trace} />
          )}
        </main>
      ) : (
        /* Initial Empty State before first run */
        <div className="qw-initial-empty">
          <div className="qw-empty-icon-wrap" aria-hidden="true">
            <FileSearch size={32} />
          </div>
          <h3 className="qw-empty-title">Ready for Inquiry Orchestration</h3>
          <p className="qw-empty-desc">
            Submit a question above to execute real-time intent classification, pre-retrieval routing across
            enterprise sources, bounded candidate retrieval, and 4D evidence evaluation.
          </p>
          <div className="qw-empty-suggestions">
            <span className="qw-empty-suggestions-label">Try an example inquiry:</span>
            <div className="qw-suggest-chips">
              <button
                type="button"
                className="qw-suggest-chip"
                onClick={() => handleSelectExample('Why did the payment API fail after deployment?')}
              >
                Why did the payment API fail after deployment?
              </button>
              <button
                type="button"
                className="qw-suggest-chip"
                onClick={() => handleSelectExample('What is the database connection timeout limit?')}
              >
                What is the database connection timeout limit?
              </button>
              <button
                type="button"
                className="qw-suggest-chip"
                onClick={() =>
                  handleSelectExample('How do quantum teleportation warp drives operate on Mars?')
                }
              >
                Quantum warp drives on Mars (Test Abstention)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryWorkspacePage;
