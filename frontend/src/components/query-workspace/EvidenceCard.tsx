import React, { useState } from 'react';
import {
  FileText,
  MessageSquare,
  Ticket,
  Database,
  Shield,
  Clock,
  Target,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Tag,
  Copy,
  Check,
} from 'lucide-react';
import { EvidencePassage } from '../../types/retrieval';
import './EvidenceCard.css';

interface EvidenceCardProps {
  passage: EvidencePassage;
  index: number;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ passage, index }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [showWeights, setShowWeights] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const {
    title,
    content,
    source_name,
    source_type,
    citation,
    evidence_score,
    created_at,
    original_file_path,
  } = passage;

  const score = evidence_score;
  const isContentLong = content.length > 280;

  const getSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'document':
        return <FileText size={14} />;
      case 'conversations':
      case 'conversation':
        return <MessageSquare size={14} />;
      case 'tickets':
      case 'ticket':
        return <Ticket size={14} />;
      default:
        return <Database size={14} />;
    }
  };

  const getSourceTypeClass = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'document':
        return 'type-blue';
      case 'conversations':
      case 'conversation':
        return 'type-purple';
      case 'tickets':
      case 'ticket':
        return 'type-orange';
      default:
        return 'type-neutral';
    }
  };

  const handleCopyCitation = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="qw-evidence-card">
      {/* Top Header */}
      <div className="qw-card-header">
        <div className="qw-card-title-group">
          <div className="qw-rank-indicator">#{index + 1}</div>
          <div>
            <div className="qw-source-tag-row">
              <span className={`qw-source-pill ${getSourceTypeClass(source_type)}`}>
                {getSourceIcon(source_type)}
                <span>{source_type}</span>
              </span>
              <span className="qw-source-name-label">{source_name}</span>
            </div>
            <h4 className="qw-evidence-title">{title}</h4>
          </div>
        </div>

        {/* Composite Score Box */}
        <div className="qw-score-box" title="Composite 4D Evidence Score">
          <span className="qw-score-num font-mono">
            {score.final_evidence_score.toFixed(3)}
          </span>
          <span className="qw-score-caption">Composite Score</span>
        </div>
      </div>

      {/* Content Passage */}
      <div className="qw-passage-box">
        <div className={`qw-passage-text ${isExpanded || !isContentLong ? 'expanded' : 'collapsed'}`}>
          {content}
        </div>

        {isContentLong && (
          <button
            type="button"
            className="btn-expand-passage"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                <span>Show less</span>
                <ChevronUp size={13} />
              </>
            ) : (
              <>
                <span>Show full passage</span>
                <ChevronDown size={13} />
              </>
            )}
          </button>
        )}
      </div>

      {/* 4D Multi-Criteria Scores Grid */}
      <div className="qw-subscores-grid">
        {/* Relevance */}
        <div className="qw-subscore-cell" title="Topical & Lexical Relevance to Query">
          <span className="qw-sub-label">
            <Target size={12} className="text-emerald" />
            <span>Relevance</span>
          </span>
          <span className="qw-sub-val font-mono">{score.relevance_score.toFixed(2)}</span>
        </div>

        {/* Authority */}
        <div className="qw-subscore-cell" title="Source Authority & Credibility">
          <span className="qw-sub-label">
            <Shield size={12} className="text-emerald" />
            <span>Authority</span>
          </span>
          <span className="qw-sub-val font-mono">{score.authority_score.toFixed(2)}</span>
        </div>

        {/* Freshness */}
        <div className="qw-subscore-cell" title="Temporal Currency & Recency Decay">
          <span className="qw-sub-label">
            <Clock size={12} className="text-emerald" />
            <span>Freshness</span>
          </span>
          <span className="qw-sub-val font-mono">
            {score.freshness_score !== null ? score.freshness_score.toFixed(2) : 'N/A'}
            <span className={`qw-status-tag ${score.freshness_status}`}>
              {score.freshness_status}
            </span>
          </span>
        </div>

        {/* Directness */}
        <div className="qw-subscore-cell" title="Direct vs Tangential Answer Alignment">
          <span className="qw-sub-label">
            <Sparkles size={12} className="text-emerald" />
            <span>Directness</span>
          </span>
          <span className="qw-sub-val font-mono">
            {score.directness_score.toFixed(2)}
            <span className="qw-status-tag directness">{score.directness_label}</span>
          </span>
        </div>
      </div>

      {/* Citation & Metadata Footer */}
      <div className="qw-card-footer">
        <div className="qw-citation-row">
          <Tag size={12} className="text-muted" />
          <span className="qw-citation-text" title={citation}>
            {citation}
          </span>
          <button
            type="button"
            className="btn-copy-citation"
            onClick={handleCopyCitation}
            title="Copy formal citation to clipboard"
          >
            {copied ? <Check size={12} className="text-emerald" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Cite'}</span>
          </button>
        </div>

        <div className="qw-footer-actions">
          {score.weights_applied && (
            <button
              type="button"
              className="btn-toggle-weights"
              onClick={() => setShowWeights(!showWeights)}
            >
              <span>{showWeights ? 'Hide Weights' : 'Scoring Weights'}</span>
              {showWeights ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          )}

          {created_at && (
            <span className="qw-file-stamp">
              Recorded: {created_at}
            </span>
          )}
        </div>
      </div>

      {/* Expandable Scoring Explanation & Weights */}
      {showWeights && (
        <div className="qw-scoring-breakdown-tray">
          <p className="qw-scoring-explanation-text">
            <strong>Engine Rationale:</strong> {score.scoring_explanation}
          </p>
          {score.weights_applied && (
            <div className="qw-weights-chips">
              <span className="qw-weights-title">Applied Formula:</span>
              {Object.entries(score.weights_applied).map(([k, v]) => (
                <span key={k} className="qw-weight-pill">
                  {k}: <strong>{v}</strong>
                </span>
              ))}
              {original_file_path && (
                <span className="qw-file-path-pill" title={original_file_path}>
                  File: {original_file_path}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
