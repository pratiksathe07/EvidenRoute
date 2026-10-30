import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSearch,
  Search,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  inspectEvidenceForQuestion,
  QueryEvidenceInspection,
} from '../services/evidenceExplorerService';
import './EvidenceExplorerPage.css';

const SAMPLE_QUESTIONS = [
  'Why did the payment API fail after deployment?',
  'What was decided in the product planning meeting?',
  'What is the employee leave policy for parental leave?',
  'How do I resolve database connection timeout issues?',
];

export const EvidenceExplorerPage: React.FC = () => {
  const [question, setQuestion] = useState<string>('Why did the payment API fail after deployment?');
  const [inspection, setInspection] = useState<QueryEvidenceInspection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

  const handleInspect = useCallback(async (qToInspect?: string) => {
    const target = (qToInspect || question).trim();
    if (!target) return;

    setIsLoading(true);
    setErrorMessage(null);

    const res = await inspectEvidenceForQuestion(target);
    if (res.isAvailable && res.data) {
      setInspection(res.data);
      // Auto-expand first item
      if (res.data.evidenceItems.length > 0) {
        setExpandedCardId(res.data.evidenceItems[0].id);
      }
    } else {
      setErrorMessage(res.error || 'Failed to inspect evidence for this question.');
    }
    setIsLoading(false);
  }, [question]);

  useEffect(() => {
    handleInspect();
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedCardId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="ee-container">
      {/* 1. Header Banner */}
      <header className="ee-header">
        <div className="ee-header-content">
          <div className="ee-badge-row">
            <span className="ee-badge">
              <FileSearch size={13} />
              <span>Evidence Provenance & Verification</span>
            </span>
          </div>
          <h1 className="ee-title">Evidence Explorer</h1>
          <p className="ee-subtitle">
            Trace where answers come from, inspect original documents, and understand why each passage was selected to ground your answer.
          </p>
        </div>
      </header>

      {/* 2. Question Search & Inspection Bar */}
      <section className="ee-input-section">
        <div className="ee-input-wrap">
          <Search size={18} className="ee-search-icon" />
          <input
            type="text"
            className="ee-input"
            placeholder="Search or enter a question to inspect retrieved evidence..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleInspect();
            }}
          />
          <button
            type="button"
            className="ee-inspect-btn"
            onClick={() => handleInspect()}
            disabled={isLoading || !question.trim()}
          >
            {isLoading ? 'Exploring...' : 'Inspect Evidence'}
          </button>
        </div>

        {/* Suggested Questions */}
        <div className="ee-samples-row">
          <span className="ee-samples-label">Examples:</span>
          {SAMPLE_QUESTIONS.map((sq, idx) => (
            <button
              key={idx}
              type="button"
              className="ee-sample-chip"
              onClick={() => {
                setQuestion(sq);
                handleInspect(sq);
              }}
            >
              {sq}
            </button>
          ))}
        </div>
      </section>

      {errorMessage && (
        <div className="ee-error-banner">
          <AlertTriangle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 3. Query Summary Card */}
      {inspection && (
        <section className="ee-summary-card">
          <div className="ee-summary-top">
            <span className="ee-summary-label">Active Question</span>
            <span className="ee-verdict-pill">
              <CheckCircle2 size={13} className="text-emerald" />
              <span>{inspection.verdictLabel}</span>
            </span>
          </div>
          <h2 className="ee-active-question">&ldquo;{inspection.question}&rdquo;</h2>
          <div className="ee-summary-meta">
            <span>Evaluated <strong>{inspection.totalSourcesEvaluated}</strong> sources</span>
            <span>•</span>
            <span>Found <strong>{inspection.totalPassagesRetrieved}</strong> grounded evidence passages</span>
          </div>
        </section>
      )}

      {/* 4. Evidence Passages List */}
      <section className="ee-passages-section">
        <h3 className="ee-section-heading">Retrieved Supporting Evidence</h3>

        {inspection ? (
          inspection.evidenceItems.length > 0 ? (
            <div className="ee-cards-list">
              {inspection.evidenceItems.map((item, idx) => (
                <div key={item.id} className="ee-evidence-card">
                  {/* Card Header */}
                  <div
                    className="ee-card-header"
                    onClick={() => toggleExpand(item.id)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="ee-card-header-left">
                      <span className="ee-rank-pill">#{idx + 1}</span>
                      <div>
                        <div className="ee-card-title-row">
                          <h4 className="ee-source-name">{item.sourceName}</h4>
                          <span className="ee-cat-badge">{item.sourceCategory}</span>
                          <span className="ee-doc-name">{item.originalDocument}</span>
                        </div>
                        <span className="ee-citation-code">{item.citation}</span>
                      </div>
                    </div>

                    <div className="ee-card-header-right">
                      <div className="ee-quality-pill" title="Relevance match">
                        <span>{item.relevancePercent}% Match</span>
                      </div>
                      <div className="ee-expand-icon">
                        {expandedCardId === item.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>
                  </div>

                  {/* Highlighted Passage Excerpt */}
                  <div className="ee-passage-box">
                    <div className="ee-passage-quote">&ldquo;{item.passageContent}&rdquo;</div>
                  </div>

                  {/* Why Retrieved & How It Supports */}
                  <div className="ee-explanations-grid">
                    <div className="ee-explanation-cell">
                      <span className="ee-cell-label">Why This Was Retrieved:</span>
                      <p className="ee-cell-text">{item.retrievalReason}</p>
                    </div>

                    <div className="ee-explanation-cell">
                      <span className="ee-cell-label">How It Supports The Answer:</span>
                      <p className="ee-cell-text">{item.answerSupportExplanation}</p>
                    </div>
                  </div>

                  {/* Conflicting information if present */}
                  {item.conflictingInformation && (
                    <div className="ee-conflict-note">
                      <AlertTriangle size={14} className="text-warning" />
                      <span><strong>Notice:</strong> {item.conflictingInformation}</span>
                    </div>
                  )}

                  {/* Expandable Details Drawer */}
                  {expandedCardId === item.id && (
                    <div className="ee-details-drawer">
                      <div className="ee-drawer-title">Evidence Quality Breakdown:</div>
                      <div className="ee-drawer-grid">
                        <div className="ee-drawer-item">
                          <span className="ee-drawer-label">Relevance Match:</span>
                          <span className="ee-drawer-val text-blue">{item.relevancePercent}%</span>
                        </div>
                        <div className="ee-drawer-item">
                          <span className="ee-drawer-label">Source Authority:</span>
                          <span className="ee-drawer-val text-purple">{item.authorityPercent}% (Trusted)</span>
                        </div>
                        <div className="ee-drawer-item">
                          <span className="ee-drawer-label">Freshness:</span>
                          <span className="ee-drawer-val text-orange">{item.freshnessPercent}%</span>
                        </div>
                        <div className="ee-drawer-item">
                          <span className="ee-drawer-label">Verification Status:</span>
                          <span className="ee-drawer-val text-emerald">{item.correctnessStatus}</span>
                        </div>
                      </div>
                      <div className="ee-drawer-footer">
                        <span className="ee-tech-id">System Reference: {item.technicalId}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="ee-empty-state">
              <FileSearch size={32} className="text-muted" />
              <p>No evidence passages found for this inquiry.</p>
            </div>
          )
        ) : (
          <div className="ee-loading-state">
            <span className="ee-spinner" />
            <span>Finding grounded evidence passages...</span>
          </div>
        )}
      </section>
    </div>
  );
};

export default EvidenceExplorerPage;
