import React, { useState } from 'react';
import {
  AlertOctagon,
  ChevronDown,
  ChevronUp,
  FileDiff,
  HelpCircle,
  Lightbulb,
} from 'lucide-react';
import { ConflictReport } from '../../types/retrieval';
import './ConflictInspector.css';

interface ConflictInspectorProps {
  conflicts: ConflictReport[];
}

export const ConflictInspector: React.FC<ConflictInspectorProps> = ({ conflicts }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (!conflicts || conflicts.length === 0) return null;

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'sev-critical';
      case 'warning':
        return 'sev-warning';
      default:
        return 'sev-info';
    }
  };

  const formatConflictType = (type: string) => {
    return type
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  return (
    <div className="qw-conflict-card">
      <div className="qw-conflict-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="qw-conflict-title-wrap">
          <div className="qw-conflict-icon-box">
            <AlertOctagon size={18} />
          </div>
          <div>
            <h4 className="qw-conflict-title">
              Evidence Conflict & Divergence Detection ({conflicts.length})
            </h4>
            <p className="qw-conflict-subtitle">
              The engine detected discrepancies across candidate passages requiring transparent resolution.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="qw-conflict-toggle"
          aria-label={isExpanded ? 'Collapse conflicts' : 'Expand conflicts'}
        >
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {isExpanded && (
        <div className="qw-conflict-body">
          {conflicts.map((conflict) => (
            <div key={conflict.conflict_id} className="qw-conflict-item">
              <div className="qw-conflict-item-top">
                <div className="qw-conflict-type-row">
                  <span className={`qw-sev-pill ${getSeverityBadgeClass(conflict.severity)}`}>
                    {conflict.severity.toUpperCase()}
                  </span>
                  <span className="qw-conflict-type-label">
                    {formatConflictType(conflict.conflict_type)}
                  </span>
                  {conflict.topic && (
                    <span className="qw-conflict-topic">Topic: {conflict.topic}</span>
                  )}
                </div>
              </div>

              <p className="qw-conflict-explanation">{conflict.explanation}</p>

              {/* Conflicting Passages Side-by-Side or List */}
              {conflict.conflicting_passages && conflict.conflicting_passages.length > 0 && (
                <div className="qw-conflicting-passages-grid">
                  {conflict.conflicting_passages.map((p, idx) => (
                    <div key={p.chunk_id || idx} className="qw-conflicting-passage-card">
                      <div className="qw-passage-ref-header">
                        <FileDiff size={13} className="text-muted" />
                        <span className="qw-passage-source-name">{p.source_name}</span>
                        {p.timestamp && (
                          <span className="qw-passage-timestamp font-mono">
                            {p.timestamp}
                          </span>
                        )}
                      </div>
                      <blockquote className="qw-passage-statement">
                        &ldquo;{p.statement}&rdquo;
                      </blockquote>
                      <span className="qw-passage-citation-tag">{p.citation}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Engine Resolution Hint */}
              {conflict.resolution_hint && (
                <div className="qw-resolution-hint-box">
                  <Lightbulb size={14} className="qw-hint-icon" />
                  <span className="qw-hint-text">
                    <strong>Resolution Guidance:</strong> {conflict.resolution_hint}
                  </span>
                </div>
              )}
            </div>
          ))}

          <div className="qw-conflict-footer-note">
            <HelpCircle size={13} />
            <span>
              Contradictions and temporal updates are highlighted to prevent synthesizing answers from outdated or conflicting policies.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
