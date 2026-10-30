import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  FileSearch,
  Zap,
  Info,
  Scale,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { SourceRankResult } from '../../types/sourceSelection';
import './SourceRankingPanel.css';

interface SourceRankingPanelProps {
  rankedSources: SourceRankResult[];
  hasExecuted: boolean;
  isLoading: boolean;
}

export const SourceRankingPanel: React.FC<SourceRankingPanelProps> = ({
  rankedSources,
  hasExecuted,
  isLoading,
}) => {
  const [expandedScoreSourceId, setExpandedScoreSourceId] = useState<string | null>(null);

  const selectedSources = rankedSources.filter((s) => s.selection_status === 'selected');
  const skippedSources = rankedSources.filter((s) => s.selection_status === 'skipped');

  const toggleScoreBreakdown = (sourceId: string) => {
    setExpandedScoreSourceId((prev) => (prev === sourceId ? null : sourceId));
  };

  return (
    <div className="source-ranking-card">
      <div className="ranking-header">
        <div className="ranking-title-group">
          <div className="ranking-icon-box">
            <Zap size={18} />
          </div>
          <div>
            <h3 className="ranking-title">Pre-Retrieval Source Ranking & Selection</h3>
            <p className="ranking-subtitle">
              Calculated by <code>POST /api/query</code> using multi-criteria suitability scoring.
            </p>
          </div>
        </div>

        {hasExecuted && rankedSources.length > 0 && (
          <div className="ranking-stats-badge">
            <span className="stats-dot" />
            <span>
              {selectedSources.length} Selected • {skippedSources.length} Skipped
            </span>
          </div>
        )}
      </div>

      <div className="ranking-content">
        {isLoading ? (
          <div className="ranking-loading-state">
            <span className="ranking-spinner" />
            <p>Evaluating contextual suitability and ranking sources...</p>
          </div>
        ) : !hasExecuted || rankedSources.length === 0 ? (
          /* Instructional Empty State */
          <div className="ranking-empty-state">
            <div className="ranking-empty-icon">
              <FileSearch size={26} />
            </div>
            <h4 className="ranking-empty-title">Awaiting Query Analysis</h4>
            <p className="ranking-empty-text">
              Enter a question above and click <strong>&ldquo;Analyze Sources&rdquo;</strong> to inspect how EvidenRoute evaluates relevance, type suitability, authority, and availability before dispatching document queries.
            </p>
            <div className="ranking-empty-features">
              <div className="feature-pill">
                <span className="pill-dot emerald" />
                <span>Multi-criteria Suitability Algorithm</span>
              </div>
              <div className="feature-pill">
                <span className="pill-dot blue" />
                <span>Dynamic Weight Normalization</span>
              </div>
              <div className="feature-pill">
                <span className="pill-dot orange" />
                <span>Zero-Noise Source Skipping</span>
              </div>
            </div>
          </div>
        ) : (
          /* Results Table with Visual Distinction */
          <div className="ranking-results-container">
            {/* 1. Selected Sources Section */}
            {selectedSources.length > 0 && (
              <div className="ranking-section">
                <div className="section-label-row selected-label">
                  <CheckCircle2 size={16} />
                  <span>Selected Context Sources (Prioritized for Retrieval)</span>
                  <span className="section-count-tag">{selectedSources.length}</span>
                </div>

                <div className="ranking-cards-list">
                  {selectedSources.map((source) => {
                    const isScoreExpanded = expandedScoreSourceId === source.source_id;
                    const hasNormalizedWeights = source.historical_usefulness_score === null;

                    return (
                      <div key={source.source_id} className="decision-card selected-card">
                        <div className="decision-main-row">
                          <div className="decision-left">
                            <div className="rank-badge rank-selected">
                              #{source.ranking_position}
                            </div>
                            <div className="decision-info">
                              <div className="source-title-row">
                                <h4 className="decision-source-name">{source.source_name}</h4>
                                <span className="source-type-label">{source.source_type}</span>
                                {hasNormalizedWeights && (
                                  <span
                                    className="norm-weight-pill"
                                    title="Historical usefulness was null; historical weight was dynamically redistributed to remaining criteria"
                                  >
                                    <Scale size={11} />
                                    <span>Historical Weight Normalized</span>
                                  </span>
                                )}
                              </div>
                              <p className="decision-reason">
                                <span className="reason-label">Selection Reason:</span> {source.selection_reason}
                              </p>
                            </div>
                          </div>

                          <div className="decision-right">
                            <div className="score-box" title="Final Computed Engine Score">
                              <span className="score-number">{source.final_score.toFixed(3)}</span>
                              <span className="score-caption">Final Score</span>
                            </div>

                            <span className="status-pill-decision selected">
                              <CheckCircle2 size={12} />
                              <span>Selected</span>
                            </span>
                          </div>
                        </div>

                        {/* Sub-Criteria Scores Matrix */}
                        <div className="subscores-bar">
                          <div className="subscore-item">
                            <span className="subscore-label">Relevance</span>
                            <span className="subscore-val font-mono">{source.relevance_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Type Suitability</span>
                            <span className="subscore-val font-mono">{source.type_suitability_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Authority</span>
                            <span className="subscore-val font-mono">{source.authority_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Historical Usefulness</span>
                            <span className={`subscore-val font-mono ${source.historical_usefulness_score === null ? 'null-val' : ''}`}>
                              {source.historical_usefulness_score !== null
                                ? source.historical_usefulness_score.toFixed(2)
                                : 'N/A'}
                            </span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Availability</span>
                            <span className="subscore-val font-mono">{source.availability_score.toFixed(2)}</span>
                          </div>

                          {source.score_breakdown && (
                            <button
                              type="button"
                              className="btn-toggle-score-details"
                              onClick={() => toggleScoreBreakdown(source.source_id)}
                            >
                              <SlidersHorizontal size={12} />
                              <span>{isScoreExpanded ? 'Hide Weights' : 'View Weights'}</span>
                              {isScoreExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                            </button>
                          )}
                        </div>

                        {/* Extended Score Breakdown if available */}
                        {isScoreExpanded && source.score_breakdown && (
                          <div className="score-breakdown-details">
                            <span className="breakdown-title">Engine Weight Breakdown & Formula:</span>
                            <pre className="breakdown-json">
                              {JSON.stringify(source.score_breakdown, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 2. Skipped Sources Section */}
            {skippedSources.length > 0 && (
              <div className="ranking-section">
                <div className="section-label-row skipped-label">
                  <XCircle size={16} />
                  <span>Skipped Context Sources (Pruned to Preserve Budget & Reduce Noise)</span>
                  <span className="section-count-tag">{skippedSources.length}</span>
                </div>

                <div className="ranking-cards-list">
                  {skippedSources.map((source) => {
                    const isScoreExpanded = expandedScoreSourceId === source.source_id;
                    const hasNormalizedWeights = source.historical_usefulness_score === null;

                    return (
                      <div key={source.source_id} className="decision-card skipped-card">
                        <div className="decision-main-row">
                          <div className="decision-left">
                            <div className="rank-badge rank-skipped">
                              #{source.ranking_position}
                            </div>
                            <div className="decision-info">
                              <div className="source-title-row">
                                <h4 className="decision-source-name">{source.source_name}</h4>
                                <span className="source-type-label">{source.source_type}</span>
                                {hasNormalizedWeights && (
                                  <span className="norm-weight-pill skipped">
                                    <Scale size={11} />
                                    <span>Historical Weight Normalized</span>
                                  </span>
                                )}
                              </div>
                              <p className="decision-reason skipped-reason-text">
                                <span className="reason-label">Skipping Reason:</span> {source.selection_reason}
                              </p>
                            </div>
                          </div>

                          <div className="decision-right">
                            <div className="score-box skipped-score" title="Final Computed Engine Score">
                              <span className="score-number">{source.final_score.toFixed(3)}</span>
                              <span className="score-caption">Final Score</span>
                            </div>

                            <span className="status-pill-decision skipped">
                              <XCircle size={12} />
                              <span>Skipped</span>
                            </span>
                          </div>
                        </div>

                        {/* Sub-Criteria Scores Matrix */}
                        <div className="subscores-bar skipped-subscores">
                          <div className="subscore-item">
                            <span className="subscore-label">Relevance</span>
                            <span className="subscore-val font-mono">{source.relevance_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Type Suitability</span>
                            <span className="subscore-val font-mono">{source.type_suitability_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Authority</span>
                            <span className="subscore-val font-mono">{source.authority_score.toFixed(2)}</span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Historical Usefulness</span>
                            <span className={`subscore-val font-mono ${source.historical_usefulness_score === null ? 'null-val' : ''}`}>
                              {source.historical_usefulness_score !== null
                                ? source.historical_usefulness_score.toFixed(2)
                                : 'N/A'}
                            </span>
                          </div>
                          <div className="subscore-item">
                            <span className="subscore-label">Availability</span>
                            <span className="subscore-val font-mono">{source.availability_score.toFixed(2)}</span>
                          </div>

                          {source.score_breakdown && (
                            <button
                              type="button"
                              className="btn-toggle-score-details"
                              onClick={() => toggleScoreBreakdown(source.source_id)}
                            >
                              <SlidersHorizontal size={12} />
                              <span>{isScoreExpanded ? 'Hide Weights' : 'View Weights'}</span>
                              {isScoreExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                            </button>
                          )}
                        </div>

                        {/* Extended Score Breakdown if available */}
                        {isScoreExpanded && source.score_breakdown && (
                          <div className="score-breakdown-details">
                            <span className="breakdown-title">Engine Weight Breakdown:</span>
                            <pre className="breakdown-json">
                              {JSON.stringify(source.score_breakdown, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="ranking-footer-note">
              <Info size={14} />
              <span>
                Selection status (&ldquo;selected&rdquo; vs. &ldquo;skipped&rdquo;) and final score are computed dynamically by <code>POST /api/query</code>.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
