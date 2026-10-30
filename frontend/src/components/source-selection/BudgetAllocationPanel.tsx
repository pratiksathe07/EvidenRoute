import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Database,
  ArrowRight,
  Info,
} from 'lucide-react';
import './BudgetAllocationPanel.css';

interface BudgetAllocationPanelProps {
  selectedCount: number;
  skippedCount: number;
  evaluatedCount: number;
  hasExecuted: boolean;
}

export const BudgetAllocationPanel: React.FC<BudgetAllocationPanelProps> = ({
  selectedCount,
  skippedCount,
  evaluatedCount,
  hasExecuted,
}) => {
  const pruningPercentage =
    evaluatedCount > 0 ? Math.round((skippedCount / evaluatedCount) * 100) : 0;

  return (
    <div className="budget-allocation-card">
      <div className="budget-header">
        <div className="budget-title-wrap">
          <div className="budget-icon-container">
            <ShieldCheck size={18} />
          </div>
          <div>
            <h3 className="budget-title">Retrieval Budget Preservation</h3>
            <p className="budget-subtitle">
              Pre-retrieval source filtering to protect LLM context windows and vector quota.
            </p>
          </div>
        </div>

        {hasExecuted && evaluatedCount > 0 && (
          <div className="budget-efficiency-pill">
            <span>{pruningPercentage}% Budget Preserved</span>
          </div>
        )}
      </div>

      <div className="budget-content">
        {hasExecuted && evaluatedCount > 0 ? (
          <div className="budget-active-display">
            {/* 3 Backend Counts Metrics */}
            <div className="budget-metrics-row">
              <div className="budget-metric-cell">
                <span className="budget-cell-label">Selected Sources</span>
                <div className="budget-cell-val-wrap text-emerald">
                  <CheckCircle2 size={16} />
                  <span className="budget-cell-val font-mono">{selectedCount}</span>
                </div>
                <span className="budget-cell-sub">Dispatched for retrieval</span>
              </div>

              <div className="budget-metric-cell">
                <span className="budget-cell-label">Skipped Sources</span>
                <div className="budget-cell-val-wrap text-muted">
                  <XCircle size={16} />
                  <span className="budget-cell-val font-mono">{skippedCount}</span>
                </div>
                <span className="budget-cell-sub">Pruned before retrieval</span>
              </div>

              <div className="budget-metric-cell">
                <span className="budget-cell-label">Evaluated Candidates</span>
                <div className="budget-cell-val-wrap text-primary">
                  <Database size={16} />
                  <span className="budget-cell-val font-mono">{evaluatedCount}</span>
                </div>
                <span className="budget-cell-sub">Total scored by engine</span>
              </div>
            </div>

            {/* Visual Pruning Efficiency Ratio Bar */}
            <div className="budget-ratio-section">
              <div className="budget-ratio-bar">
                <div
                  className="ratio-segment selected"
                  style={{ width: `${100 - pruningPercentage}%` }}
                  title={`${selectedCount} Selected (${100 - pruningPercentage}%)`}
                />
                <div
                  className="ratio-segment skipped"
                  style={{ width: `${pruningPercentage}%` }}
                  title={`${skippedCount} Skipped (${pruningPercentage}%)`}
                />
              </div>

              <div className="budget-ratio-legend">
                <div className="legend-item">
                  <span className="legend-dot emerald" />
                  <span className="legend-label">Selected Context Sources ({100 - pruningPercentage}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot gray" />
                  <span className="legend-label">Pruned Sources ({pruningPercentage}%)</span>
                </div>
              </div>
            </div>

            {/* Why Skipping Preserves Budget Explanation */}
            <div className="budget-preservation-note">
              <span className="preservation-note-title">How Skipping Preserves Budget:</span>
              <p className="preservation-note-body">
                By excluding unaligned or low-confidence sources before executing vector and semantic searches, EvidenRoute directly reduces database I/O, prevents token exhaustion in downstream LLM prompts, and eliminates hallucination vectors.
              </p>
            </div>

            {/* Preparation for /api/intelligence/retrieve */}
            <div className="retrieval-stage-preview">
              <Info size={14} className="preview-icon" />
              <div className="preview-text">
                <strong>Operational Token Budget Stage:</strong> Specific chunk budgets, token counts, and candidate limits are enforced during execution via the central BudgetManager in <code>POST /api/query</code>.
              </div>
            </div>
          </div>
        ) : (
          /* Empty / Awaiting State */
          <div className="budget-empty-state">
            <div className="budget-empty-icon-wrap">
              <ShieldCheck size={22} />
            </div>
            <h4 className="budget-empty-title">Awaiting Source Selection Evaluation</h4>
            <p className="budget-empty-text">
              Run a query analysis above to inspect how many sources are selected versus pruned to preserve context retrieval budget.
            </p>
            <div className="budget-empty-note">
              <ArrowRight size={13} />
              <span>Token quotas and chunk retrieval limits take effect in the retrieval phase.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
