import React, { useState, useEffect, useCallback } from 'react';
import { Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { QueryInputPanel } from '../components/source-selection/QueryInputPanel';
import { AvailableSourcesPanel } from '../components/source-selection/AvailableSourcesPanel';
import { SourceRankingPanel } from '../components/source-selection/SourceRankingPanel';
import { BudgetAllocationPanel } from '../components/source-selection/BudgetAllocationPanel';
import { SelectionExplanationPanel } from '../components/source-selection/SelectionExplanationPanel';
import {
  getAvailableSources,
  getIntelligencePlan,
} from '../services/sourceSelectionService';
import { getSystemHealth } from '../services/dashboardService';
import {
  SourceMetadata,
  PlanResponse,
} from '../types/sourceSelection';
import './SourceSelectionPage.css';

export const SourceSelectionPage: React.FC = () => {
  // Query & Execution State
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasExecuted, setHasExecuted] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  // Data State
  const [availableSources, setAvailableSources] = useState<SourceMetadata[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState<boolean>(false);
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null);

  // Engine Probe State
  const [isEngineConnected, setIsEngineConnected] = useState<boolean>(false);

  // Probe backend on mount
  const checkHealth = useCallback(async () => {
    const healthRes = await getSystemHealth();
    setIsEngineConnected(
      healthRes.isAvailable &&
        (healthRes.data?.status === 'healthy' || healthRes.data?.status === 'ok')
    );
  }, []);

  // Fetch available sources from GET /api/sources
  const loadSources = useCallback(async () => {
    setIsLoadingSources(true);
    const result = await getAvailableSources();
    if (result.isAvailable && result.data) {
      setAvailableSources(result.data);
    } else {
      setAvailableSources([]);
    }
    setIsLoadingSources(false);
  }, []);

  useEffect(() => {
    checkHealth();
    loadSources();
  }, [checkHealth, loadSources]);

  // Handle Query Submission calling POST /api/query
  const handleAnalyzeSources = async () => {
    const trimmed = query.trim();
    if (!trimmed) {
      setValidationError('Please enter a question or operational scenario to analyze sources.');
      return;
    }

    setValidationError(null);
    setBackendError(null);
    setIsLoading(true);

    // Call query orchestration endpoint: POST /api/query
    const result = await getIntelligencePlan(
      {
        question: trimmed,
      },
      availableSources
    );

    if (result.isAvailable && result.data && result.data.decision_trace) {
      setPlanResult(result.data);
      setHasExecuted(true);
    } else {
      setPlanResult(null);
      setHasExecuted(true);
      setBackendError(
        result.error ||
          'Backend intelligence orchestrator is currently unreachable (POST /api/query). Start the backend API on port 8000 to compute live selection rankings.'
      );
    }

    setIsLoading(false);
  };

  // Handle Clear
  const handleClear = () => {
    setQuery('');
    setValidationError(null);
    setBackendError(null);
    setPlanResult(null);
    setHasExecuted(false);
  };

  const decisionTrace = planResult?.decision_trace ?? null;

  return (
    <div className="source-selection-container">
      {/* ====================================================================
          A. Page Heading
          ==================================================================== */}
      <section className="studio-heading-section">
        <div className="heading-text-wrap">
          <div className="heading-title-row">
            <h2 className="studio-title">Source Selection Studio</h2>
            <div className="engine-step-tag">
              <Database size={13} />
              <span>Pre-Retrieval Stage</span>
            </div>
          </div>
          <p className="studio-subtitle">
            Understand how EvidenRoute prioritizes context sources before retrieval.
          </p>
        </div>

        {/* Dynamic Engine Probed Status */}
        <div
          className={`studio-status-pill ${
            isEngineConnected ? 'status-online' : 'status-standby'
          }`}
          title={
            isEngineConnected
              ? 'Backend intelligence orchestrator online at /api/health'
              : 'Client mode active. Awaiting backend API on port 8000'
          }
        >
          <span className={`status-indicator-dot ${isEngineConnected ? 'dot-online' : 'dot-standby'}`} />
          {isEngineConnected ? (
            <>
              <CheckCircle2 size={13} />
              <span>Orchestrator Probed</span>
            </>
          ) : (
            <>
              <AlertCircle size={13} />
              <span>Engine Standby (Awaiting Backend)</span>
            </>
          )}
        </div>
      </section>

      {/* ====================================================================
          B. Query Input Panel
          ==================================================================== */}
      <section className="studio-input-section">
        <QueryInputPanel
          query={query}
          setQuery={(q) => {
            setQuery(q);
            if (validationError) setValidationError(null);
          }}
          onAnalyze={handleAnalyzeSources}
          onClear={handleClear}
          isLoading={isLoading}
          validationError={validationError}
          backendError={backendError}
        />
      </section>

      {/* ====================================================================
          C. Available Sources Panel
          ==================================================================== */}
      <section className="studio-available-section">
        <AvailableSourcesPanel
          sources={availableSources}
          isLoading={isLoadingSources}
        />
      </section>

      {/* ====================================================================
          D. Source Ranking and Selection Panel (Core Section)
          ==================================================================== */}
      <section className="studio-ranking-section">
        <SourceRankingPanel
          rankedSources={decisionTrace?.ranked_sources || []}
          hasExecuted={hasExecuted}
          isLoading={isLoading}
        />
      </section>

      {/* ====================================================================
          E & F. Budget Preservation & Selection Explanation
          ==================================================================== */}
      <section className="studio-budget-explanation-layout">
        <div className="layout-col-budget">
          <BudgetAllocationPanel
            selectedCount={decisionTrace?.selected_sources_count ?? 0}
            skippedCount={decisionTrace?.skipped_sources_count ?? 0}
            evaluatedCount={decisionTrace?.evaluated_sources_count ?? 0}
            hasExecuted={hasExecuted}
          />
        </div>

        <div className="layout-col-explanation">
          <SelectionExplanationPanel
            decisionTrace={decisionTrace}
            hasExecuted={hasExecuted}
          />
        </div>
      </section>
    </div>
  );
};

export default SourceSelectionPage;
