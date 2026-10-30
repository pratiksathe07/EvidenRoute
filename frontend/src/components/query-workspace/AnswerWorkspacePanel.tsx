import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  Copy,
  Check,
  Sparkles,
  Info,
  ShieldCheck,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { WorkspaceExecutionResult } from '../../types/queryWorkspace';
import './AnswerWorkspacePanel.css';

interface AnswerWorkspacePanelProps {
  execution: WorkspaceExecutionResult;
}

export const AnswerWorkspacePanel: React.FC<AnswerWorkspacePanelProps> = ({ execution }) => {
  const [hasCopied, setHasCopied] = useState(false);

  const {
    outcome,
    finalAnswer,
    abstentionReason,
    readinessVerdict,
    confidenceScore,
    primaryJustification,
    geminiStatus,
    retrievedEvidence,
  } = execution;

  const handleCopy = () => {
    const textToCopy = finalAnswer || abstentionReason || primaryJustification || '';
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setHasCopied(true);
      setTimeout(() => setHasCopied(false), 2000);
    }
  };

  const getOutcomeBadge = () => {
    switch (outcome.toUpperCase()) {
      case 'ANSWER':
      case 'READY_TO_ANSWER':
        return (
          <span className="outcome-pill pill-success">
            <CheckCircle2 size={14} />
            <span>Sufficient Evidence Grounded</span>
          </span>
        );
      case 'CLARIFY':
        return (
          <span className="outcome-pill pill-warning">
            <HelpCircle size={14} />
            <span>Clarification Required</span>
          </span>
        );
      case 'RETRIEVE_MORE':
        return (
          <span className="outcome-pill pill-warning">
            <AlertTriangle size={14} />
            <span>Additional Context Needed</span>
          </span>
        );
      case 'ABSTAIN':
      default:
        return (
          <span className="outcome-pill pill-abstain">
            <XCircle size={14} />
            <span>Abstained (Insufficient Evidence)</span>
          </span>
        );
    }
  };

  // Collect unique citation references
  const citations = retrievedEvidence
    .map((e) => e.citation || e.record_id || e.chunk_id)
    .filter(Boolean);
  const uniqueCitations = Array.from(new Set(citations));

  return (
    <div className="answer-workspace-panel">
      {/* Header bar */}
      <div className="answer-panel-header">
        <div className="answer-title-group">
          <div className="answer-icon-wrap">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h3 className="answer-title">Answer Workspace & Synthesis</h3>
            <span className="answer-subtitle">
              Grounding Verdict: <strong>{readinessVerdict}</strong>
            </span>
          </div>
        </div>

        <div className="answer-header-meta">
          {getOutcomeBadge()}

          {finalAnswer && (
            <button
              type="button"
              className="answer-copy-btn"
              onClick={handleCopy}
              title="Copy answer text"
            >
              {hasCopied ? (
                <>
                  <Check size={14} />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Gemini LLM Status Banner */}
      <div className="gemini-status-banner">
        <div className="gemini-status-left">
          <Sparkles size={16} className="gemini-sparkle-icon" />
          <div className="gemini-status-text">
            <strong>LLM Generation: {geminiStatus.provider}</strong>
            <p>{geminiStatus.message}</p>
          </div>
        </div>
        <span className="gemini-offline-tag">Offline Deterministic</span>
      </div>

      {/* Main Answer Card */}
      <div className="answer-content-card">
        {outcome === 'ABSTAIN' ? (
          <div className="answer-abstention-box">
            <div className="abstention-title">
              <AlertCircle size={16} />
              <h4>Abstention Notice</h4>
            </div>
            <p className="abstention-text">
              {abstentionReason || primaryJustification || 'The engine refrained from generating an answer because evidence did not meet the sufficiency threshold.'}
            </p>
          </div>
        ) : (
          <div className="answer-text-area">
            {finalAnswer ? (
              <div className="answer-text-formatted">
                {finalAnswer.split('\n').map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
            ) : (
              <div className="answer-empty-state">
                <Info size={16} />
                <span>
                  Evidence retrieved and verified, but Gemini LLM generation is unconfigured. Inspect supporting passages in the Evidence Explorer below.
                </span>
              </div>
            )}
          </div>
        )}

        {/* Confidence & Sufficiency Gauge */}
        <div className="answer-confidence-strip">
          <div className="confidence-label-group">
            <span className="confidence-title">Readiness Confidence:</span>
            <span className="confidence-pct">{(confidenceScore * 100).toFixed(0)}%</span>
          </div>
          <div className="confidence-bar-track">
            <div
              className={`confidence-bar-fill ${confidenceScore >= 0.7 ? 'fill-high' : confidenceScore >= 0.4 ? 'fill-mid' : 'fill-low'}`}
              style={{ width: `${Math.min(confidenceScore * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Primary Justification */}
        <div className="answer-justification-box">
          <span className="justification-heading">Engine Decision Rationale:</span>
          <p className="justification-text">{primaryJustification}</p>
        </div>

        {/* Cited Evidence References */}
        {uniqueCitations.length > 0 && (
          <div className="answer-citations-tray">
            <span className="citations-label">
              <FileText size={13} />
              Cited Evidence Grounding:
            </span>
            <div className="citation-pills">
              {uniqueCitations.map((cite, i) => (
                <span key={i} className="citation-pill" title={`Source Reference: ${cite}`}>
                  [{cite}]
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
