import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSearch,
  Search,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Shield,
  Layers,
  Sparkles,
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

  const avgAuthority = inspection && inspection.evidenceItems.length > 0
    ? Math.round(
        inspection.evidenceItems.reduce((acc, curr) => acc + curr.authorityPercent, 0) /
          inspection.evidenceItems.length
      )
    : 85;

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

      {/* 2. Prominent Question Search & Inspection Bar */}
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
          <span className="ee-samples-label">Try with:</span>
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

      {/* 3. Error Banner */}
      {errorMessage && (
        <div className="ee-error-banner">
          <AlertTriangle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 4. Inspection Results Summary Card */}
      {inspection && (
        <section className="ee-summary-card">
          <div className="ee-summary-top">
            <span className="ee-summary-label">Active Question Inspection</span>
            <span className="ee-verdict-pill">
              <CheckCircle2 size={12} />
              <span>{inspection.verdictLabel}</span>
            </span>
          </div>

          <h2 className="ee-active-question">&ldquo;{inspection.question}&rdquo;</h2>

          <div className="ee-summary-meta">
            <span className="ee-meta-pill">
              <Layers size={13} />
              <span>{inspection.totalPassagesRetrieved} Passages Selected</span>
            </span>
            <span className="ee-meta-pill">
              <Shield size={13} />
              <span>Avg Authority: {avgAuthority}%</span>
            </span>
            <span className="ee-meta-pill">
              <Sparkles size={13} />
              <span>{inspection.totalSourcesEvaluated} Connected Resources Evaluated</span>
            </span>
          </div>
        </section>
      )}

      {/* 5. Retrieved Evidence Passages List */}
      {inspection && (
        <section className="ee-passages-section">
          <div className="ee-section-heading">
            <h3 className="ee-heading-title">Retrieved Evidence Passages</h3>
            <span className="ee-heading-desc">
              Original text passages evaluated and approved by EvidenRoute
            </span>
          </div>

          <div className="ee-passages-list">
            {inspection.evidenceItems.map((item, idx) => {
              const isExpanded = expandedCardId === item.id;
              return (
                <div key={item.id} className="ee-passage-card">
                  {/* Card Header */}
                  <div
                    className="ee-card-header"
                    onClick={() => toggleExpand(item.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleExpand(item.id);
                      }
                    }}
                  >
                    <div className="ee-card-title-group">
                      <span className="ee-index-badge">#{idx + 1}</span>
                      <div>
                        <div className="ee-source-name-row">
                          <span className="ee-source-title">{item.sourceName}</span>
                          <span className="ee-category-tag">{item.sourceCategory}</span>
                        </div>
                        <span className="ee-doc-title">{item.originalDocument}</span>
                      </div>
                    </div>

                    <div className="ee-card-header-right">
                      <div className="ee-quality-pill">
                        <span className="ee-quality-label">Authority</span>
                        <span className="ee-quality-score">{item.authorityPercent}%</span>
                      </div>
                      <div className="ee-toggle-arrow">
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className={`ee-card-body ${isExpanded ? 'open' : 'collapsed'}`}>
                    {/* The Passage Content */}
                    <div className="ee-quote-block">
                      <p className="ee-passage-text">&ldquo;{item.passageContent}&rdquo;</p>
                    </div>

                    {/* Explanatory Details */}
                    <div className="ee-details-grid">
                      <div className="ee-detail-item">
                        <span className="ee-detail-label">Why This Was Selected:</span>
                        <p className="ee-detail-val">{item.retrievalReason}</p>
                      </div>

                      <div className="ee-detail-item">
                        <span className="ee-detail-label">How It Supports Answer:</span>
                        <p className="ee-detail-val">{item.answerSupportExplanation}</p>
                      </div>
                    </div>

                    {/* Score Bar Breakdown */}
                    <div className="ee-factors-row">
                      <div className="ee-factor-pill">
                        <span className="f-label">Relevance:</span>
                        <span className="f-val text-blue">{item.relevancePercent}%</span>
                      </div>
                      <div className="ee-factor-pill">
                        <span className="f-label">Freshness:</span>
                        <span className="f-val text-orange">{item.freshnessPercent}%</span>
                      </div>
                      <div className="ee-factor-pill">
                        <span className="f-label">Correctness:</span>
                        <span className="f-val text-emerald">{item.correctnessStatus}</span>
                      </div>
                      <div className="ee-factor-pill">
                        <span className="f-label">Authority:</span>
                        <span className="f-val text-purple">{item.authorityPercent}%</span>
                      </div>
                    </div>

                    {/* Footer Provenance */}
                    <div className="ee-card-footer">
                      <div className="ee-provenance">
                        <span>Original Identifier: <code>{item.technicalId}</code></span>
                        <span>•</span>
                        <span>Timestamp: {item.timestamp}</span>
                      </div>
                      <span className="ee-verified-flag">
                        <CheckCircle2 size={13} className="text-emerald" />
                        <span>Verified Grounding</span>
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
};

export default EvidenceExplorerPage;
