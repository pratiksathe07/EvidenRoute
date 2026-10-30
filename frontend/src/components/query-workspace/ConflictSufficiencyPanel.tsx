import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ShieldAlert,
  FileQuestion,
  Search,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  ConflictReport,
  EvidenceSufficiencyResult,
  CounterEvidenceResult,
  EvidenceReliabilityResult,
} from '../../types';
import './ConflictSufficiencyPanel.css';

interface ConflictSufficiencyPanelProps {
  conflicts: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  counterEvidence?: CounterEvidenceResult;
  evidenceReliability?: EvidenceReliabilityResult;
}

export const ConflictSufficiencyPanel: React.FC<ConflictSufficiencyPanelProps> = ({
  conflicts,
  sufficiency,
  counterEvidence,
  evidenceReliability,
}) => {
  const [expandedConflictId, setExpandedConflictId] = useState<string | null>(null);

  const toggleConflict = (id: string) => {
    setExpandedConflictId((prev) => (prev === id ? null : id));
  };

  const getSufficiencyStatusBadge = (status?: string) => {
    const s = (status || '').toLowerCase();
    if (s.includes('sufficient') && !s.includes('partially') && !s.includes('in')) {
      return (
        <span className="status-badge-chip badge-sufficient">
          <CheckCircle2 size={13} />
          <span>Sufficient Evidence</span>
        </span>
      );
    }
    if (s.includes('partially')) {
      return (
        <span className="status-badge-chip badge-partial">
          <HelpCircle size={13} />
          <span>Partially Sufficient</span>
        </span>
      );
    }
    if (s.includes('conflict')) {
      return (
        <span className="status-badge-chip badge-conflict">
          <AlertTriangle size={13} />
          <span>Contradictory Evidence</span>
        </span>
      );
    }
    return (
      <span className="status-badge-chip badge-insufficient">
        <XCircle size={13} />
        <span>Insufficient Evidence</span>
      </span>
    );
  };

  const getSeverityBadge = (severity?: string) => {
    const s = (severity || '').toLowerCase();
    if (s === 'critical' || s === 'high') {
      return <span className="severity-chip sev-critical">Critical</span>;
    }
    if (s === 'warning' || s === 'medium') {
      return <span className="severity-chip sev-warning">Warning</span>;
    }
    return <span className="severity-chip sev-info">Informational</span>;
  };

  const getActionBadge = (action?: string) => {
    const a = (action || '').toUpperCase();
    switch (a) {
      case 'ANSWER':
        return <span className="action-tag action-answer">Recommended: Answer</span>;
      case 'CLARIFY':
        return <span className="action-tag action-clarify">Recommended: Request Clarification</span>;
      case 'RETRIEVE_MORE':
        return <span className="action-tag action-retrieve">Recommended: Retrieve Additional Context</span>;
      case 'ABSTAIN':
      default:
        return <span className="action-tag action-abstain">Recommended: Abstain from Answering</span>;
    }
  };

  const sufficiencyScore = sufficiency?.sufficiency_score ?? (evidenceReliability?.reliability_score ?? 0.8);
  const missingInfo = sufficiency?.missing_information || evidenceReliability?.missing_information || [];
  const recommendedAction = sufficiency?.recommended_action || evidenceReliability?.recommended_action || 'answer';

  return (
    <div className="conflict-sufficiency-panel">
      {/* Panel Header */}
      <div className="panel-header-strip">
        <div className="header-title-block">
          <ShieldAlert size={18} className="panel-header-icon" />
          <div>
            <h3 className="panel-title">Conflict & Sufficiency Evaluation</h3>
            <span className="panel-subtitle">
              Grounding rigor, contradiction resolution, and factual completeness
            </span>
          </div>
        </div>

        <div className="header-badges-row">
          {getSufficiencyStatusBadge(sufficiency?.sufficiency_status)}
          {getActionBadge(recommendedAction)}
        </div>
      </div>

      <div className="panel-content-grid">
        {/* Left Column: Sufficiency & Missing Info */}
        <div className="sufficiency-card">
          <div className="card-subheading">
            <span>Evidence Sufficiency Score</span>
            <span className="score-percent">{(sufficiencyScore * 100).toFixed(0)}%</span>
          </div>

          <div className="progress-bar-container">
            <div
              className={`progress-fill ${sufficiencyScore >= 0.7 ? 'bar-green' : sufficiencyScore >= 0.4 ? 'bar-amber' : 'bar-red'}`}
              style={{ width: `${Math.min(sufficiencyScore * 100, 100)}%` }}
            />
          </div>

          <p className="sufficiency-explanation">
            {sufficiency?.explanation || evidenceReliability?.explanation || 'Retrieved context evaluated for factual sufficiency and claim completeness.'}
          </p>

          {/* Dimension Breakdown if present */}
          {sufficiency?.dimension_scores && (
            <div className="dimension-scores-tray">
              {Object.entries(sufficiency.dimension_scores).map(([dim, val]) => (
                <div key={dim} className="dim-chip">
                  <span className="dim-name">{dim.replace(/_/g, ' ')}:</span>
                  <span className="dim-val">{(val * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Missing Information Checklist */}
          <div className="missing-info-section">
            <div className="missing-info-title">
              <FileQuestion size={14} />
              <span>Missing Information & Coverage Gaps</span>
            </div>

            {missingInfo.length === 0 ? (
              <div className="missing-empty">
                <CheckCircle2 size={14} className="text-success" />
                <span>No critical information gaps identified for this query.</span>
              </div>
            ) : (
              <ul className="missing-list">
                {missingInfo.map((item, idx) => (
                  <li key={idx} className="missing-item">
                    <span className="bullet-missing">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right Column: Conflicts & Contradictions */}
        <div className="conflicts-card">
          <div className="card-subheading">
            <span>Contradiction & Conflict Engine</span>
            <span className={`conflict-count-tag ${conflicts.length > 0 ? 'has-conflicts' : 'no-conflicts'}`}>
              {conflicts.length} {conflicts.length === 1 ? 'Conflict' : 'Conflicts'} Detected
            </span>
          </div>

          {conflicts.length === 0 ? (
            <div className="zero-conflicts-state">
              <CheckCircle2 size={24} className="zero-conflicts-icon" />
              <div className="zero-conflicts-msg">
                <h4>No Contradictions Detected</h4>
                <p>All retrieved evidence passages are factually aligned across sources with zero metric or status disagreements.</p>
              </div>
            </div>
          ) : (
            <div className="conflicts-accordion">
              {conflicts.map((conflict, idx) => {
                const isExpanded = expandedConflictId === conflict.conflict_id || idx === 0;

                return (
                  <div
                    key={conflict.conflict_id || idx}
                    className={`conflict-item-card ${isExpanded ? 'conflict-expanded' : ''}`}
                  >
                    <div
                      className="conflict-item-header"
                      onClick={() => toggleConflict(conflict.conflict_id)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="conflict-header-left">
                        <AlertTriangle size={15} className="conflict-warn-icon" />
                        <span className="conflict-topic">Topic: {conflict.topic}</span>
                        {getSeverityBadge(conflict.severity)}
                      </div>

                      <div className="conflict-header-right">
                        <span className="conflict-type-pill">
                          {conflict.conflict_type.replace(/_/g, ' ')}
                        </span>
                        {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                      </div>
                    </div>

                    <div className="conflict-item-body">
                      <p className="conflict-explanation-text">{conflict.explanation}</p>

                      {/* Conflicting Passages Comparison */}
                      {conflict.conflicting_passages && conflict.conflicting_passages.length > 0 && (
                        <div className="conflicting-passages-tray">
                          <span className="passages-tray-title">Conflicting Claims Compared:</span>
                          <div className="passage-claims-grid">
                            {conflict.conflicting_passages.map((p, pIdx) => (
                              <div key={pIdx} className="passage-claim-box">
                                <div className="claim-source-badge">
                                  <span>{p.source_name || p.source_id}</span>
                                  {p.citation && <code>[{p.citation}]</code>}
                                </div>
                                <p className="claim-statement">"{p.statement}"</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Resolution Hint */}
                      {conflict.resolution_hint && (
                        <div className="conflict-resolution-box">
                          <Sparkles size={13} className="resolution-sparkle" />
                          <span><strong>Resolution Hint:</strong> {conflict.resolution_hint}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Counter-Evidence Stress Test Summary if available */}
          {counterEvidence && counterEvidence.executed && (
            <div className="counter-evidence-box">
              <div className="counter-evidence-header">
                <Search size={13} />
                <span>Counter-Evidence Stress Test (Step 4)</span>
              </div>
              <p className="counter-evidence-text">{counterEvidence.summary}</p>
              <div className="counter-evidence-meta">
                <span>Impact: <strong>{counterEvidence.impact_on_decision}</strong></span>
                <span>Examined: <strong>{counterEvidence.evidence_examined_count}</strong> passages</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
