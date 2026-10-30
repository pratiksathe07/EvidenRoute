import React, { useState, useEffect, useCallback } from 'react';
import {
  Terminal,
  CheckCircle2,
  AlertCircle,
  Activity,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { WorkspaceQueryInput } from '../components/query-workspace/WorkspaceQueryInput';
import { ExecutionSummaryBar } from '../components/query-workspace/ExecutionSummaryBar';
import { PipelineStageTracker } from '../components/query-workspace/PipelineStageTracker';
import { AnswerWorkspacePanel } from '../components/query-workspace/AnswerWorkspacePanel';
import { EvidenceExplorerPanel } from '../components/query-workspace/EvidenceExplorerPanel';
import { ConflictSufficiencyPanel } from '../components/query-workspace/ConflictSufficiencyPanel';
import { QueryHistorySidebar } from '../components/query-workspace/QueryHistorySidebar';
import {
  executeWorkspaceQuery,
  getQueryHistory,
} from '../services/queryWorkspaceService';
import { getSystemHealth } from '../services/dashboardService';
import {
  WorkspaceExecutionResult,
  QueryHistoryRecord,
} from '../types/queryWorkspace';
import './QueryWorkspacePage.css';

type ActiveTab = 'answer' | 'conflicts' | 'trace';

export const QueryWorkspacePage: React.FC = () => {
  // Query & Execution State
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<WorkspaceExecutionResult | null>(null);

  // Active view tab
  const [activeTab, setActiveTab] = useState<ActiveTab>('answer');

  // History State
  const [history, setHistory] = useState<QueryHistoryRecord[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);

  // Engine Connection Probe
  const [isEngineConnected, setIsEngineConnected] = useState<boolean>(false);

  // 1. Probe health on mount
  const checkHealth = useCallback(async () => {
    const healthRes = await getSystemHealth();
    setIsEngineConnected(
      healthRes.isAvailable &&
        (healthRes.data?.status === 'healthy' || healthRes.data?.status === 'ok')
    );
  }, []);

  // 2. Load query history from GET /api/query
  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    const histRes = await getQueryHistory(20);
    if (histRes.isAvailable && histRes.data) {
      setHistory(histRes.data);
    }
    setIsLoadingHistory(false);
  }, []);

  useEffect(() => {
    checkHealth();
    loadHistory();
  }, [checkHealth, loadHistory]);

  // 3. Handle Query Execution
  const handleRunQuery = async (questionToRun: string) => {
    const trimmed = questionToRun.trim();
    if (!trimmed) {
      setValidationError('Please enter a natural-language question to query the intelligence engine.');
      return;
    }

    setValidationError(null);
    setBackendError(null);
    setIsLoading(true);

    const result = await executeWorkspaceQuery(trimmed, 5, true);

    if (result.isAvailable && result.data) {
      setExecutionResult(result.data);
      // Auto-switch to answer tab on new execution
      setActiveTab('answer');
      // Refresh persistent history in background
      loadHistory();
    } else {
      setBackendError(
        result.error ||
          'Failed to execute query workspace pipeline. Ensure backend is running on port 8000.'
      );
    }

    setIsLoading(false);
  };

  // 4. Handle Clear Action
  const handleClear = () => {
    setQuery('');
    setValidationError(null);
    setBackendError(null);
    setExecutionResult(null);
  };

  // 5. Handle Query Selection from History
  const handleSelectHistoryQuery = (selectedQuestion: string) => {
    setQuery(selectedQuestion);
    handleRunQuery(selectedQuestion);
  };

  return (
    <div className="query-workspace-page">
      {/* ====================================================================
          A. Page Header
          ==================================================================== */}
      <section className="workspace-header-section">
        <div className="header-info-wrap">
          <div className="header-title-line">
            <h2 className="workspace-page-title">Query Workspace</h2>
            <div className="workspace-pipeline-badge">
              <Terminal size={13} />
              <span>Full Intelligence Pipeline</span>
            </div>
          </div>
          <p className="workspace-page-subtitle">
            Execute bounded hybrid retrieval, multi-dimensional evidence evaluation, conflict detection, and grounded synthesis.
          </p>
        </div>

        {/* Dynamic Engine Probed Status */}
        <div
          className={`workspace-status-chip ${
            isEngineConnected ? 'status-online' : 'status-standby'
          }`}
          title={
            isEngineConnected
              ? 'Backend intelligence orchestrator online at http://127.0.0.1:8000'
              : 'Backend unreachable. Running in client standby mode'
          }
        >
          <span className={`status-dot ${isEngineConnected ? 'dot-online' : 'dot-standby'}`} />
          {isEngineConnected ? (
            <>
              <CheckCircle2 size={13} />
              <span>Pipeline Engine Online</span>
            </>
          ) : (
            <>
              <AlertCircle size={13} />
              <span>Engine Standby (Port 8000)</span>
            </>
          )}
        </div>
      </section>

      {/* ====================================================================
          B. Main Layout: Workspace Stream + History Drawer
          ==================================================================== */}
      <div className="workspace-main-layout">
        <div className="workspace-center-column">
          {/* Query Input Box */}
          <section className="workspace-input-section">
            <WorkspaceQueryInput
              query={query}
              setQuery={(q) => {
                setQuery(q);
                if (validationError) setValidationError(null);
              }}
              onSubmit={handleRunQuery}
              onClear={handleClear}
              isLoading={isLoading}
              validationError={validationError}
              backendError={backendError}
            />
          </section>

          {/* Execution Summary Bar (Appears when execution data exists) */}
          {executionResult && (
            <section className="workspace-summary-section">
              <ExecutionSummaryBar execution={executionResult} />
            </section>
          )}

          {/* Results Navigation Tabs (Appears when execution data exists) */}
          {executionResult && (
            <section className="workspace-tabs-section">
              <div className="workspace-tabs-bar">
                <button
                  type="button"
                  className={`workspace-tab-btn ${activeTab === 'answer' ? 'tab-active' : ''}`}
                  onClick={() => setActiveTab('answer')}
                >
                  <Sparkles size={14} />
                  <span>Answer & Supporting Evidence</span>
                  <span className="tab-count-tag">
                    {executionResult.retrievedEvidence.length}
                  </span>
                </button>

                <button
                  type="button"
                  className={`workspace-tab-btn ${activeTab === 'conflicts' ? 'tab-active' : ''}`}
                  onClick={() => setActiveTab('conflicts')}
                >
                  <ShieldAlert size={14} />
                  <span>Conflicts & Sufficiency</span>
                  {executionResult.conflicts.length > 0 && (
                    <span className="tab-count-tag count-alert">
                      {executionResult.conflicts.length}
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  className={`workspace-tab-btn ${activeTab === 'trace' ? 'tab-active' : ''}`}
                  onClick={() => setActiveTab('trace')}
                >
                  <Activity size={14} />
                  <span>Execution Pipeline Trace</span>
                  <span className="tab-count-tag">9 Stages</span>
                </button>
              </div>

              {/* Tab Contents */}
              <div className="workspace-tab-viewport">
                {activeTab === 'answer' && (
                  <div className="tab-panel-answer-view">
                    <AnswerWorkspacePanel execution={executionResult} />
                    <EvidenceExplorerPanel
                      evidenceList={executionResult.retrievedEvidence}
                    />
                  </div>
                )}

                {activeTab === 'conflicts' && (
                  <div className="tab-panel-conflicts-view">
                    <ConflictSufficiencyPanel
                      conflicts={executionResult.conflicts}
                      sufficiency={executionResult.sufficiency}
                      counterEvidence={executionResult.counterEvidence}
                      evidenceReliability={executionResult.evidenceReliability}
                    />
                  </div>
                )}

                {activeTab === 'trace' && (
                  <div className="tab-panel-trace-view">
                    <PipelineStageTracker
                      stages={executionResult.stages}
                      isLoading={isLoading}
                    />
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Empty State before any query is run */}
          {!executionResult && !isLoading && (
            <section className="workspace-empty-hero">
              <div className="hero-icon-container">
                <Terminal size={32} />
              </div>
              <h3>Ready to Orchestrate Context</h3>
              <p>
                Enter a question above or choose a verified scenario to trigger the 9-stage intelligence pipeline: query analysis, source selection, budget enforcement, bounded retrieval, 4D scoring, conflict detection, and context pruning.
              </p>
              <div className="hero-features-list">
                <span className="hero-feature-item">
                  <CheckCircle2 size={13} />
                  Multi-Factor 4D Scoring
                </span>
                <span className="hero-feature-item">
                  <CheckCircle2 size={13} />
                  Contradiction Resolution
                </span>
                <span className="hero-feature-item">
                  <CheckCircle2 size={13} />
                  Budget Quota Protection
                </span>
                <span className="hero-feature-item">
                  <CheckCircle2 size={13} />
                  Persisted Database History
                </span>
              </div>
            </section>
          )}
        </div>

        {/* Right Sidebar: Query History */}
        <aside className="workspace-history-column">
          <QueryHistorySidebar
            history={history}
            isLoading={isLoadingHistory}
            onSelectQuery={handleSelectHistoryQuery}
            onRefresh={loadHistory}
            activeQuestion={executionResult?.question || query}
          />
        </aside>
      </div>
    </div>
  );
};

export default QueryWorkspacePage;
