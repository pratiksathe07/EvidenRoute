import React, { useState, useEffect, useCallback } from 'react';
import {
  Database,
  Search,
  CheckCircle2,
  XCircle,
  Shield,
  Gauge,
  Info,
  Layers,
} from 'lucide-react';
import {
  rankResourcesForQuestion,
  ResourceRankingResult,
} from '../services/resourceRankingService';
import './ResourceRankingPage.css';

const SAMPLE_QUESTIONS = [
  'Why did the payment API fail after deployment?',
  'What was decided in the product planning meeting?',
  'What is the employee leave policy for parental leave?',
  'How do I resolve database connection timeout issues?',
];

export const ResourceRankingPage: React.FC = () => {
  const [question, setQuestion] = useState<string>('Why did the payment API fail after deployment?');
  const [rankingData, setRankingData] = useState<ResourceRankingResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRank = useCallback(async (qToRank?: string) => {
    const targetQ = (qToRank || question).trim();
    if (!targetQ) return;

    setIsLoading(true);
    setErrorMessage(null);

    const res = await rankResourcesForQuestion(targetQ);
    if (res.isAvailable && res.data) {
      setRankingData(res.data);
    } else {
      setErrorMessage(res.error || 'Failed to analyze resources for this question.');
    }
    setIsLoading(false);
  }, [question]);

  // Initial ranking on mount
  useEffect(() => {
    handleRank();
  }, []);

  return (
    <div className="rr-container">
      {/* 1. Header */}
      <header className="rr-header">
        <div className="rr-header-content">
          <div className="rr-badge-row">
            <span className="rr-badge">
              <Layers size={13} />
              <span>Context Selection & Resource Allocation</span>
            </span>
          </div>
          <h1 className="rr-title">Resource Ranking</h1>
          <p className="rr-subtitle">
            See how EvidenRoute evaluates connected resources, prioritizes what to search, and distributes retrieval budget to prevent wasted context.
          </p>
        </div>
      </header>

      {/* 2. Inquiry Input Bar */}
      <section className="rr-input-section">
        <div className="rr-input-wrap">
          <Search size={18} className="rr-search-icon" />
          <input
            type="text"
            className="rr-input"
            placeholder="Type a question to evaluate resource rankings (e.g. 'Why did the payment API fail?')..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRank();
            }}
          />
          <button
            type="button"
            className="rr-analyze-btn"
            onClick={() => handleRank()}
            disabled={isLoading || !question.trim()}
          >
            {isLoading ? 'Analyzing...' : 'Rank Resources'}
          </button>
        </div>

        {/* Quick Sample Questions */}
        <div className="rr-samples-row">
          <span className="rr-samples-label">Try with:</span>
          {SAMPLE_QUESTIONS.map((sq, idx) => (
            <button
              key={idx}
              type="button"
              className="rr-sample-chip"
              onClick={() => {
                setQuestion(sq);
                handleRank(sq);
              }}
            >
              {sq}
            </button>
          ))}
        </div>
      </section>

      {/* Error Banner */}
      {errorMessage && (
        <div className="rr-error-banner">
          <Info size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* 3. Budget Overview Cards */}
      {rankingData && (
        <section className="rr-budget-grid">
          <div className="rr-budget-card highlight">
            <div className="rr-budget-header">
              <span className="rr-budget-label">Resources Selected</span>
              <CheckCircle2 size={18} className="text-emerald" />
            </div>
            <div className="rr-budget-val text-emerald">
              {rankingData.selectedCount} of {rankingData.resources.length}
            </div>
            <div className="rr-budget-desc">
              Only resources directly relevant to your question are searched.
            </div>
          </div>

          <div className="rr-budget-card">
            <div className="rr-budget-header">
              <span className="rr-budget-label">Resources Skipped</span>
              <XCircle size={18} className="text-muted" />
            </div>
            <div className="rr-budget-val text-muted">
              {rankingData.skippedCount} Skipped
            </div>
            <div className="rr-budget-desc">
              Unrelated documents filtered out to prevent noisy answers.
            </div>
          </div>

          <div className="rr-budget-card">
            <div className="rr-budget-header">
              <span className="rr-budget-label">Budget Allocated</span>
              <Gauge size={18} className="text-blue" />
            </div>
            <div className="rr-budget-val text-blue">
              {rankingData.budget.callsUsedText}
            </div>
            <div className="rr-budget-desc">
              {rankingData.budget.candidatesUsedText}
            </div>
          </div>

          <div className="rr-budget-card">
            <div className="rr-budget-header">
              <span className="rr-budget-label">Context Preserved</span>
              <Shield size={18} className="text-purple" />
            </div>
            <div className="rr-budget-val text-purple">
              {rankingData.budget.preservationPercent}% Saved
            </div>
            <div className="rr-budget-desc">
              {rankingData.budget.tokensUsedText}
            </div>
          </div>
        </section>
      )}

      {/* 4. Ranked Resources Table */}
      <section className="rr-table-section">
        <div className="rr-table-header">
          <h2 className="rr-table-title">Available Resources & Selection Explanations</h2>
          <span className="rr-table-subtitle">
            Evaluated for question: &ldquo;{rankingData?.question || question}&rdquo;
          </span>
        </div>

        {rankingData ? (
          <div className="rr-cards-list">
            {rankingData.resources.map((res) => (
              <div
                key={res.id}
                className={`rr-resource-card ${res.isSelected ? 'selected' : 'skipped'}`}
              >
                <div className="rr-card-left">
                  <div className="rr-card-status-badge">
                    {res.isSelected ? (
                      <span className="status-pill selected">
                        <CheckCircle2 size={13} />
                        <span>Selected for Search</span>
                      </span>
                    ) : (
                      <span className="status-pill skipped">
                        <XCircle size={13} />
                        <span>Skipped</span>
                      </span>
                    )}
                    <span className="rr-category-pill">{res.category}</span>
                    <span className={`rr-priority-pill ${res.priority.toLowerCase()}`}>
                      {res.priority} Priority
                    </span>
                  </div>

                  <h3 className="rr-resource-name">{res.name}</h3>
                  <p className="rr-explanation-text">{res.explanation}</p>

                  <div className="rr-card-footer-meta">
                    <span className="meta-item">
                      <Gauge size={13} />
                      <span>{res.budgetAllocatedText}</span>
                    </span>
                    <span className="meta-item">
                      <Database size={13} />
                      <span>{res.recordCount} indexed records</span>
                    </span>
                  </div>
                </div>

                <div className="rr-card-right">
                  <div className="rr-score-metric">
                    <span className="rr-score-label">Relevance to Question</span>
                    <div className="rr-score-bar-wrap">
                      <div className="rr-score-bar">
                        <div
                          className="rr-score-fill blue"
                          style={{ width: `${res.relevancePercent}%` }}
                        />
                      </div>
                      <span className="rr-score-pct">{res.relevancePercent}%</span>
                    </div>
                  </div>

                  <div className="rr-score-metric">
                    <span className="rr-score-label">Trust & Authority Level</span>
                    <div className="rr-score-bar-wrap">
                      <div className="rr-score-bar">
                        <div
                          className="rr-score-fill emerald"
                          style={{ width: `${res.trustLevelPercent}%` }}
                        />
                      </div>
                      <span className="rr-score-pct">{res.trustLevelPercent}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rr-loading-state">
            <span className="rr-spinner" />
            <span>Evaluating contextual suitability and ranking resources...</span>
          </div>
        )}
      </section>
    </div>
  );
};

export default ResourceRankingPage;
