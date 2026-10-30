import React, { useState } from 'react';
import { RetrievalDecisionTrace } from '../../types/retrieval';
import './DecisionTracePanel.css';

interface DecisionTracePanelProps {
  trace: RetrievalDecisionTrace;
}

export const DecisionTracePanel: React.FC<DecisionTracePanelProps> = ({ trace }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'analysis' | 'sources' | 'retrieval' | 'stages' | 'raw'>('analysis');

  const {
    analysis,
    selected_source_ids = [],
    skipped_source_ids = [],
    retrieval_mode,
    total_candidate_chunks_evaluated,
    retrieved_evidence_count,
    execution_time_ms,
    budget_info,
    trace_stages = [],
  } = trace;

  const togglePanel = () => {
    setIsOpen(!isOpen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      togglePanel();
    }
  };

  return (
    <section className="decision-trace-section" aria-label="Query Decision Audit Trace">
      <div
        className="trace-header-toggle"
        role="button"
        tabIndex={0}
        onClick={togglePanel}
        onKeyDown={handleKeyDown}
        aria-expanded={isOpen}
        aria-controls="decision-trace-content"
      >
        <div className="trace-header-left">
          <div className="trace-icon-badge" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <div>
            <h3 className="trace-title">Execution & Decision Audit Trace</h3>
            <p className="trace-subtitle">
              Inspect how EvidenRoute analyzed the query, routed to sources, and evaluated chunk candidates
            </p>
          </div>
        </div>

        <div className="trace-header-right">
          <span className="trace-meta-pill">
            <span className="meta-dot"></span>
            {trace_stages.length > 0 ? `${trace_stages.length} Stages` : 'Audited'}
          </span>
          <span className="trace-meta-pill">
            {execution_time_ms != null ? `${execution_time_ms.toFixed(1)} ms` : 'Completed'}
          </span>
          <span className="trace-chevron" aria-hidden="true">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={isOpen ? 'chevron-rotated' : ''}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </span>
        </div>
      </div>

      {isOpen && (
        <div id="decision-trace-content" className="trace-body">
          {/* Audit Navigation Tabs */}
          <div className="trace-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'analysis'}
              className={`trace-tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              Query Analysis
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'sources'}
              className={`trace-tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
              onClick={() => setActiveTab('sources')}
            >
              Source Routing ({selected_source_ids.length}/{selected_source_ids.length + skipped_source_ids.length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'retrieval'}
              className={`trace-tab-btn ${activeTab === 'retrieval' ? 'active' : ''}`}
              onClick={() => setActiveTab('retrieval')}
            >
              Retrieval & Budget
            </button>
            {trace_stages.length > 0 && (
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'stages'}
                className={`trace-tab-btn ${activeTab === 'stages' ? 'active' : ''}`}
                onClick={() => setActiveTab('stages')}
              >
                Pipeline Stages ({trace_stages.length})
              </button>
            )}
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'raw'}
              className={`trace-tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
              onClick={() => setActiveTab('raw')}
            >
              Raw Trace
            </button>
          </div>

          <div className="trace-tab-panel">
            {/* Tab 1: Query Analysis */}
            {activeTab === 'analysis' && (
              <div className="trace-analysis-grid">
                <div className="trace-card">
                  <h4 className="card-header">Query Intent & Category</h4>
                  <div className="trace-kv-list">
                    <div className="trace-kv-item">
                      <span className="kv-label">Intent:</span>
                      <span className="kv-value highlight">{analysis?.intent || 'general_query'}</span>
                    </div>
                    <div className="trace-kv-item">
                      <span className="kv-label">Category:</span>
                      <span className="kv-value">{analysis?.information_category || 'uncategorized'}</span>
                    </div>
                    <div className="trace-kv-item">
                      <span className="kv-label">Confidence:</span>
                      <span className="kv-value">
                        {analysis?.confidence != null ? `${(analysis.confidence * 100).toFixed(0)}%` : 'N/A'}
                      </span>
                    </div>
                    {analysis?.analyzer_type && (
                      <div className="trace-kv-item">
                        <span className="kv-label">Analyzer Engine:</span>
                        <span className="kv-value">{analysis.analyzer_type}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="trace-card">
                  <h4 className="card-header">Extracted Linguistic Entities</h4>
                  <div className="trace-tags-container">
                    <div className="tag-group">
                      <span className="tag-group-label">Keywords:</span>
                      <div className="tags-wrap">
                        {analysis?.keywords && analysis.keywords.length > 0 ? (
                          analysis.keywords.map((kw: string, i: number) => (
                            <span key={i} className="trace-badge keyword-badge">
                              {kw}
                            </span>
                          ))
                        ) : (
                          <span className="empty-subtext">None extracted</span>
                        )}
                      </div>
                    </div>

                    <div className="tag-group">
                      <span className="tag-group-label">Technical Terms:</span>
                      <div className="tags-wrap">
                        {analysis?.technical_terms && analysis.technical_terms.length > 0 ? (
                          analysis.technical_terms.map((term: string, i: number) => (
                            <span key={i} className="trace-badge tech-badge">
                              {term}
                            </span>
                          ))
                        ) : (
                          <span className="empty-subtext">None extracted</span>
                        )}
                      </div>
                    </div>

                    {analysis?.entities && analysis.entities.length > 0 && (
                      <div className="tag-group">
                        <span className="tag-group-label">Entities:</span>
                        <div className="tags-wrap">
                          {analysis.entities.map((ent: string, i: number) => (
                            <span key={i} className="trace-badge entity-badge">
                              {ent}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {analysis?.likely_source_types && analysis.likely_source_types.length > 0 && (
                  <div className="trace-card span-full">
                    <h4 className="card-header">Expected Context Source Types</h4>
                    <div className="tags-wrap">
                      {analysis.likely_source_types.map((st: string, i: number) => (
                        <span key={i} className="trace-badge source-type-badge">
                          {st}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Source Routing Decisions */}
            {activeTab === 'sources' && (
              <div className="trace-sources-view">
                <div className="trace-card">
                  <h4 className="card-header selected-header">
                    <span className="status-dot green"></span>
                    Selected Context Sources ({selected_source_ids.length})
                  </h4>
                  <p className="card-subtext">
                    Sources prioritized by EvidenRoute pre-retrieval routing before chunking
                  </p>
                  <div className="id-list">
                    {selected_source_ids.map((id, i) => (
                      <div key={i} className="id-item selected-item">
                        <span className="id-rank">#{i + 1}</span>
                        <code className="id-code">{id}</code>
                        <span className="id-tag">Grounded</span>
                      </div>
                    ))}
                    {selected_source_ids.length === 0 && (
                      <div className="empty-subtext">No sources were selected.</div>
                    )}
                  </div>
                </div>

                <div className="trace-card">
                  <h4 className="card-header skipped-header">
                    <span className="status-dot gray"></span>
                    Pruned / Skipped Sources ({skipped_source_ids.length})
                  </h4>
                  <p className="card-subtext">
                    Excluded pre-retrieval to prevent irrelevant context dilution and noise
                  </p>
                  <div className="id-list">
                    {skipped_source_ids.map((id, i) => (
                      <div key={i} className="id-item skipped-item">
                        <span className="id-rank">pruned</span>
                        <code className="id-code">{id}</code>
                        <span className="id-tag pruned-tag">Pruned</span>
                      </div>
                    ))}
                    {skipped_source_ids.length === 0 && (
                      <div className="empty-subtext">No sources were skipped.</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Retrieval & Budget Details */}
            {activeTab === 'retrieval' && (
              <div className="trace-retrieval-grid">
                <div className="metric-box">
                  <div className="metric-label">Retrieval Mode</div>
                  <div className="metric-val">{retrieval_mode || 'lexical_only'}</div>
                  <div className="metric-sub">Lexical BM25 ranking across selected corpus</div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">Evaluated Candidates</div>
                  <div className="metric-val">{total_candidate_chunks_evaluated ?? 'N/A'}</div>
                  <div className="metric-sub">Candidate chunks parsed & scored</div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">Retained Evidence</div>
                  <div className="metric-val">{retrieved_evidence_count ?? 'N/A'}</div>
                  <div className="metric-sub">Top ranked passages passing threshold</div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">Execution Latency</div>
                  <div className="metric-val">
                    {execution_time_ms != null ? `${execution_time_ms.toFixed(1)}ms` : 'N/A'}
                  </div>
                  <div className="metric-sub">End-to-end selection & retrieval latency</div>
                </div>

                {budget_info && Object.keys(budget_info).length > 0 && (
                  <div className="trace-card span-full">
                    <h4 className="card-header">Context Budget Allocations</h4>
                    <pre className="json-pre">{JSON.stringify(budget_info, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}

            {/* Tab 4: Pipeline Stages */}
            {activeTab === 'stages' && (
              <div className="trace-stages-list">
                {trace_stages.map((stage, idx) => (
                  <div key={idx} className="stage-step-item">
                    <div className="stage-step-index">{idx + 1}</div>
                    <div className="stage-step-content">
                      <span className="stage-step-title">{stage}</span>
                      <span className="stage-step-status">Executed</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 5: Raw JSON Audit */}
            {activeTab === 'raw' && (
              <div className="trace-raw-container">
                <pre className="json-pre" tabIndex={0}>
                  {JSON.stringify(trace, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
};
export default DecisionTracePanel;
