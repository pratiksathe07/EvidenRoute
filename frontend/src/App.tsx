import React, { useState, useEffect } from 'react';
import './App.css';
import type {
  PipelineDecisionTrace,
  HealthResponse,
  SelectionConfig,
  RetrieveResponse,
} from './types';

const API_BASE = 'http://localhost:8000/api/intelligence';

const BENCHMARK_QUERIES = [
  {
    id: 1,
    title: '1. Payment API Deployment Failure',
    query: 'Why did the payment API fail after deployment?',
    expected: 'Technical Docs, Tickets, War Room chat',
  },
  {
    id: 2,
    title: '2. Product Planning Decision',
    query: 'What was decided during the last product planning meeting?',
    expected: 'Conversations / Meeting transcripts',
  },
  {
    id: 3,
    title: '3. Employee Leave Policy',
    query: 'What is the employee leave policy?',
    expected: 'Policy documents / HR Handbook',
  },
  {
    id: 4,
    title: '4. Database Connection Timeout',
    query: 'How do I resolve a database connection timeout?',
    expected: 'Database architecture manual & bug tickets',
  },
  {
    id: 5,
    title: '5. Unrelated Topic',
    query: 'Tell me about an unrelated topic not covered by the available sources.',
    expected: 'Zero sources selected (budget preserved)',
  },
];

const DEFAULT_CONFIG: SelectionConfig = {
  relevance_weight: 0.35,
  suitability_weight: 0.25,
  authority_weight: 0.20,
  historical_weight: 0.10,
  availability_weight: 0.10,
  selection_threshold: 0.40,
  min_relevance_threshold: 0.15,
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'retrieval' | 'selection'>('retrieval');
  const [question, setQuestion] = useState<string>(BENCHMARK_QUERIES[0].query);
  const [topK, setTopK] = useState<number>(5);
  const [loading, setLoading] = useState<boolean>(false);
  const [ingesting, setIngesting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [decisionTrace, setDecisionTrace] = useState<PipelineDecisionTrace | null>(null);
  const [retrievalResult, setRetrievalResult] = useState<RetrieveResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [indexedChunksCount, setIndexedChunksCount] = useState<number>(0);
  const [showConfig, setShowConfig] = useState<boolean>(false);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  const [config, setConfig] = useState<SelectionConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    fetchHealth();
    fetchIngestionStatus();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      // Backend offline
    }
  };

  const fetchIngestionStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/ingestion-status`);
      if (res.ok) {
        const data = await res.json();
        setIndexedChunksCount(data.total_chunks_indexed);
      }
    } catch {
      // Ignore
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/ingest`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setIndexedChunksCount(data.total_chunks);
      }
    } catch (err: any) {
      setError(err.message || 'Ingestion failed');
    } finally {
      setIngesting(false);
    }
  };

  const executeAction = async (queryToRun?: string) => {
    const q = (queryToRun !== undefined ? queryToRun : question).trim();
    if (!q) {
      setError('Please enter a question to evaluate.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'retrieval') {
        // Phase 2: Integrated Context Selection & Evidence Retrieval
        const res = await fetch(`${API_BASE}/retrieve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: q,
            top_k: topK,
            selection_config: config,
          }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || `Server responded with ${res.status}`);
        }

        const data: RetrieveResponse = await res.json();
        setRetrievalResult(data);
      } else {
        // Phase 1: Source Selection Plan Only
        const res = await fetch(`${API_BASE}/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, config }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || `Server responded with ${res.status}`);
        }

        const data = await res.json();
        setDecisionTrace(data.decision_trace);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend intelligence service.');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (q: string) => {
    setQuestion(q);
    executeAction(q);
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo-glow">
            <span className="logo-symbol">⬡</span>
          </div>
          <div>
            <div className="brand-title-row">
              <h1 className="brand-title">EvidenRoute</h1>
              <span className="phase-badge">Phase 2: Hybrid Retrieval</span>
            </div>
            <p className="brand-subtitle">
              Intelligent Context Selection & Multi-Dimensional Evidence Scoring Engine
            </p>
          </div>
        </div>

        {/* Health status indicator */}
        <div className="header-actions">
          <button
            type="button"
            className="ingest-btn"
            onClick={handleIngest}
            disabled={ingesting}
            title="Scan local data/ directories and re-index all chunks"
          >
            {ingesting ? 'Indexing...' : `⟳ Index (${indexedChunksCount} Chunks)`}
          </button>

          <div className="health-badge">
            <span className={`status-dot ${health?.status === 'operational' ? 'online' : 'checking'}`} />
            <div className="health-details">
              <span className="health-main">
                {health?.status === 'operational' ? 'Engine Ready (Local)' : 'Backend Offline'}
              </span>
              <span className="health-sub">
                BM25 Active | LLM: {health?.external_llm_integration || 'Local-First'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Mode Tabs */}
      <div className="mode-tabs">
        <button
          type="button"
          className={`mode-tab ${activeTab === 'retrieval' ? 'active' : ''}`}
          onClick={() => setActiveTab('retrieval')}
        >
          🔍 Phase 2: Evidence Passage Retrieval & Scoring
        </button>
        <button
          type="button"
          className={`mode-tab ${activeTab === 'selection' ? 'active' : ''}`}
          onClick={() => setActiveTab('selection')}
        >
          🧭 Phase 1: Source Selection Routing Plan
        </button>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {/* Preset Query Chips */}
        <section className="presets-section">
          <div className="presets-label">
            <span>Benchmark Scenarios (Development Progress Review):</span>
          </div>
          <div className="presets-grid">
            {BENCHMARK_QUERIES.map((preset) => (
              <button
                key={preset.id}
                className={`preset-chip ${question === preset.query ? 'active' : ''}`}
                onClick={() => handlePresetSelect(preset.query)}
              >
                <div className="preset-chip-title">{preset.title}</div>
                <div className="preset-chip-expected">Target: {preset.expected}</div>
              </button>
            ))}
          </div>
        </section>

        {/* Query Input Box */}
        <section className="search-section">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              executeAction();
            }}
            className="search-form"
          >
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="Ask a question to select sources and retrieve scored evidence passages..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
              {activeTab === 'retrieval' && (
                <div className="top-k-wrapper">
                  <label>Top K:</label>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                    className="top-k-select"
                  >
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                  </select>
                </div>
              )}
              <button
                type="button"
                className={`config-toggle-btn ${showConfig ? 'active' : ''}`}
                onClick={() => setShowConfig(!showConfig)}
                title="Configure Scoring Weights & Thresholds"
              >
                ⚙ Weights
              </button>
              <button
                type="submit"
                className="execute-btn"
                disabled={loading}
              >
                {loading
                  ? 'Evaluating...'
                  : activeTab === 'retrieval'
                  ? 'Retrieve & Score Evidence'
                  : 'Plan Context Selection'}
              </button>
            </div>
          </form>

          {/* Config Drawer */}
          {showConfig && (
            <div className="config-drawer">
              <div className="config-header">
                <h3>Configurable Scoring Weights & Selection Threshold</h3>
                <button
                  type="button"
                  className="reset-config-btn"
                  onClick={() => setConfig(DEFAULT_CONFIG)}
                >
                  Reset Defaults
                </button>
              </div>
              <div className="config-grid">
                <div className="config-item">
                  <label>
                    Relevance Weight: <strong>{config.relevance_weight.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.relevance_weight}
                    onChange={(e) =>
                      setConfig({ ...config, relevance_weight: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="config-item">
                  <label>
                    Suitability Weight: <strong>{config.suitability_weight.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.suitability_weight}
                    onChange={(e) =>
                      setConfig({ ...config, suitability_weight: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="config-item">
                  <label>
                    Authority Weight: <strong>{config.authority_weight.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.authority_weight}
                    onChange={(e) =>
                      setConfig({ ...config, authority_weight: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="config-item">
                  <label>
                    Historical Weight: <strong>{config.historical_weight.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.historical_weight}
                    onChange={(e) =>
                      setConfig({ ...config, historical_weight: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="config-item">
                  <label>
                    Availability Weight: <strong>{config.availability_weight.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.availability_weight}
                    onChange={(e) =>
                      setConfig({ ...config, availability_weight: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div className="config-item highlight">
                  <label>
                    Selection Threshold: <strong>{config.selection_threshold.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="0.9"
                    step="0.05"
                    value={config.selection_threshold}
                    onChange={(e) =>
                      setConfig({ ...config, selection_threshold: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>
            </div>
          )}

          {error && <div className="error-banner">⚠️ {error}</div>}
        </section>

        {/* ============================================================== */}
        {/* PHASE 2 RESULTS VIEW: RETRIEVAL & EVIDENCE SCORING            */}
        {/* ============================================================== */}
        {activeTab === 'retrieval' && retrievalResult && (
          <div className="results-container">
            {/* Query Understanding Card */}
            <section className="glass-card analysis-card">
              <div className="card-header">
                <div>
                  <span className="card-tag">Phase 1 Query Understanding</span>
                  <h2 className="card-title">Intent & Selected Search Scope</h2>
                </div>
                <div className="confidence-pill">
                  Mode: <strong>{retrievalResult.retrieval_mode}</strong>
                </div>
              </div>

              <div className="analysis-grid">
                <div className="analysis-box">
                  <span className="box-label">Detected Intent</span>
                  <span className="intent-badge">{retrievalResult.query_analysis.intent}</span>
                </div>
                <div className="analysis-box">
                  <span className="box-label">Category</span>
                  <span className="category-badge">
                    {retrievalResult.query_analysis.information_category}
                  </span>
                </div>
                <div className="analysis-box">
                  <span className="box-label">Selected Sources ({retrievalResult.selected_sources.length})</span>
                  <div className="pill-row">
                    {retrievalResult.selected_sources.length > 0 ? (
                      retrievalResult.selected_sources.map((st, i) => (
                        <span key={i} className="source-type-pill selected">
                          ✓ {st}
                        </span>
                      ))
                    ) : (
                      <span className="empty-text">Zero sources selected (Budget preserved)</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="entities-keywords-row">
                <div className="token-column">
                  <span className="box-label">Keywords</span>
                  <div className="pill-row">
                    {retrievalResult.query_analysis.keywords.map((kw, i) => (
                      <span key={i} className="token-pill keyword">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="token-column">
                  <span className="box-label">Entities</span>
                  <div className="pill-row">
                    {retrievalResult.query_analysis.entities.length > 0 ? (
                      retrievalResult.query_analysis.entities.map((ent, i) => (
                        <span key={i} className="token-pill entity">
                          {ent}
                        </span>
                      ))
                    ) : (
                      <span className="empty-text">None</span>
                    )}
                  </div>
                </div>
              </div>
            </section>

            {/* Metrics Ribbon */}
            <div className="metrics-ribbon">
              <div className="metric-cell">
                <span className="metric-val">
                  {retrievalResult.decision_trace.total_candidate_chunks_evaluated}
                </span>
                <span className="metric-label">Passages Evaluated</span>
              </div>
              <div className="metric-cell highlight-selected">
                <span className="metric-val">{retrievalResult.retrieved_evidence.length}</span>
                <span className="metric-label">Evidence Passages Returned</span>
              </div>
              <div className="metric-cell highlight-skipped">
                <span className="metric-val">{retrievalResult.skipped_sources.length}</span>
                <span className="metric-label">Sources Skipped (Budget Saved)</span>
              </div>
              <div className="metric-cell">
                <span className="metric-val">
                  {retrievalResult.decision_trace.execution_time_ms.toFixed(1)} ms
                </span>
                <span className="metric-label">Pipeline Latency</span>
              </div>
            </div>

            {/* Evidence Passages Section */}
            <section className="sources-section">
              <div className="sources-header">
                <div>
                  <span className="card-tag">Phase 2 Task 4 & 5</span>
                  <h2 className="card-title">Ranked Evidence Passages & Citations</h2>
                </div>
                <div className="threshold-indicator">
                  Formula: <strong>0.35R + 0.25A + 0.20F + 0.20D</strong>
                </div>
              </div>

              {retrievalResult.retrieved_evidence.length === 0 ? (
                <div className="empty-evidence-box">
                  <h3>No Evidence Passages Retrieved</h3>
                  <p>
                    Because Phase 1 context routing determined that available sources lacked
                    relevance to this question, zero sources were searched, completely preserving
                    the retrieval budget.
                  </p>
                </div>
              ) : (
                <div className="sources-list">
                  {retrievalResult.retrieved_evidence.map((ev) => (
                    <div key={ev.chunk_id} className="source-card selected evidence-card">
                      <div className="source-card-main">
                        <div className="source-card-top">
                          <div className="source-badge-group">
                            <span className="rank-badge">#{ev.ranking_position}</span>
                            <span className="citation-badge">{ev.citation}</span>
                            <span className="source-type-tag">{ev.source_type}</span>
                          </div>
                          <div className="final-score-box">
                            <span className="score-label">Evidence Score</span>
                            <span className="score-value selected">
                              {(ev.evidence_score.final_evidence_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <h3 className="source-name">{ev.title}</h3>
                        <p className="source-id-label">Chunk ID: {ev.chunk_id}</p>

                        {/* Passage Content Box */}
                        <div className="passage-content-box">
                          <pre className="passage-text">{ev.content}</pre>
                        </div>

                        {/* 4-Dimension Factors Grid */}
                        <div className="factors-grid evidence-factors">
                          <div className="factor-item">
                            <div className="factor-header">
                              <span>Relevance (35%)</span>
                              <strong>
                                {(ev.evidence_score.relevance_score * 100).toFixed(0)}%
                              </strong>
                            </div>
                            <div className="bar-track">
                              <div
                                className="bar-fill relevance"
                                style={{
                                  width: `${ev.evidence_score.relevance_score * 100}%`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="factor-item">
                            <div className="factor-header">
                              <span>Authority (25%)</span>
                              <strong>
                                {(ev.evidence_score.authority_score * 100).toFixed(0)}%
                              </strong>
                            </div>
                            <div className="bar-track">
                              <div
                                className="bar-fill authority"
                                style={{
                                  width: `${ev.evidence_score.authority_score * 100}%`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="factor-item">
                            <div className="factor-header">
                              <span>
                                Freshness (20%){' '}
                                <em>({ev.evidence_score.freshness_status})</em>
                              </span>
                              <strong>
                                {ev.evidence_score.freshness_score !== null
                                  ? `${(ev.evidence_score.freshness_score * 100).toFixed(0)}%`
                                  : 'N/A'}
                              </strong>
                            </div>
                            <div className="bar-track">
                              <div
                                className="bar-fill historical"
                                style={{
                                  width: `${
                                    (ev.evidence_score.freshness_score ?? 0.5) * 100
                                  }%`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="factor-item">
                            <div className="factor-header">
                              <span>
                                Directness (20%){' '}
                                <em>({ev.evidence_score.directness_label})</em>
                              </span>
                              <strong>
                                {(ev.evidence_score.directness_score * 100).toFixed(0)}%
                              </strong>
                            </div>
                            <div className="bar-track">
                              <div
                                className="bar-fill suitability"
                                style={{
                                  width: `${ev.evidence_score.directness_score * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Explainability Statement */}
                        <div className="explanation-box">
                          <span className="explanation-label">Scoring Explanation:</span>
                          <p className="explanation-text">
                            {ev.evidence_score.scoring_explanation}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Trace Stages */}
            <div className="audit-footer">
              <button
                type="button"
                className="toggle-json-btn"
                onClick={() => setShowRawJson(!showRawJson)}
              >
                {showRawJson ? 'Hide Raw Audit JSON ▴' : 'View Raw Retrieval Decision Trace JSON ▾'}
              </button>

              {showRawJson && (
                <pre className="json-block">
                  {JSON.stringify(retrievalResult.decision_trace, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* PHASE 1 RESULTS VIEW: SOURCE SELECTION PLAN ONLY              */}
        {/* ============================================================== */}
        {activeTab === 'selection' && decisionTrace && (
          <div className="results-container">
            {/* Query Understanding Card */}
            <section className="glass-card analysis-card">
              <div className="card-header">
                <div>
                  <span className="card-tag">Step 1A</span>
                  <h2 className="card-title">Deterministic Query Understanding</h2>
                </div>
                <div className="confidence-pill">
                  Confidence: <strong>{(decisionTrace.analysis.confidence * 100).toFixed(0)}%</strong>
                </div>
              </div>

              <div className="analysis-grid">
                <div className="analysis-box">
                  <span className="box-label">Detected Intent</span>
                  <span className="intent-badge">{decisionTrace.analysis.intent}</span>
                </div>
                <div className="analysis-box">
                  <span className="box-label">Information Category</span>
                  <span className="category-badge">{decisionTrace.analysis.information_category}</span>
                </div>
                <div className="analysis-box">
                  <span className="box-label">Likely Source Categories</span>
                  <div className="pill-row">
                    {decisionTrace.analysis.likely_source_types.map((st, i) => (
                      <span key={i} className="source-type-pill">
                        {st}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* Metrics Ribbon */}
            <div className="metrics-ribbon">
              <div className="metric-cell">
                <span className="metric-val">{decisionTrace.available_sources_count}</span>
                <span className="metric-label">Available Sources</span>
              </div>
              <div className="metric-cell highlight-selected">
                <span className="metric-val">{decisionTrace.selected_sources_count}</span>
                <span className="metric-label">Selected to Search</span>
              </div>
              <div className="metric-cell highlight-skipped">
                <span className="metric-val">{decisionTrace.skipped_sources_count}</span>
                <span className="metric-label">Skipped (Budget Saved)</span>
              </div>
              <div className="metric-cell">
                <span className="metric-val">{decisionTrace.execution_time_ms.toFixed(1)} ms</span>
                <span className="metric-label">Decision Latency</span>
              </div>
            </div>

            {/* Ranked Sources Decision Cards */}
            <section className="sources-section">
              <div className="sources-header">
                <div>
                  <span className="card-tag">Step 1C & 1D</span>
                  <h2 className="card-title">Source Ranking & Decision Verdicts</h2>
                </div>
                <div className="threshold-indicator">
                  Selection Threshold: <strong>{config.selection_threshold.toFixed(2)}</strong>
                </div>
              </div>

              <div className="sources-list">
                {decisionTrace.ranked_sources.map((src) => {
                  const isSelected = src.selection_status === 'selected';
                  return (
                    <div
                      key={src.source_id}
                      className={`source-card ${isSelected ? 'selected' : 'skipped'}`}
                    >
                      <div className="source-card-main">
                        <div className="source-card-top">
                          <div className="source-badge-group">
                            <span className="rank-badge">#{src.ranking_position}</span>
                            <span className={`status-badge ${isSelected ? 'selected' : 'skipped'}`}>
                              {isSelected ? '✓ SELECTED' : '✕ SKIPPED'}
                            </span>
                            <span className="source-type-tag">{src.source_type}</span>
                          </div>
                          <div className="final-score-box">
                            <span className="score-label">Final Score</span>
                            <span className={`score-value ${isSelected ? 'selected' : 'skipped'}`}>
                              {(src.final_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <h3 className="source-name">{src.source_name}</h3>
                        <p className="source-id-label">ID: {src.source_id}</p>

                        {/* Explainability Statement */}
                        <div className="explanation-box">
                          <span className="explanation-label">Decision Explanation:</span>
                          <p className="explanation-text">{src.selection_reason}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
