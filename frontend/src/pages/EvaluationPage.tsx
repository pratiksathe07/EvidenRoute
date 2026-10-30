import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Zap,
  RotateCw,
  Layers,
  Filter,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import {
  getBaselineComparison,
  BaselineComparisonReport,
} from '../services/evaluationService';
import './EvaluationPage.css';

export const EvaluationPage: React.FC = () => {
  const [report, setReport] = useState<BaselineComparisonReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchBenchmark = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await getBaselineComparison();
      if (res.data) {
        setReport(res.data);
      } else {
        setErrorMsg(res.error || 'No evaluation results available from backend.');
        setReport(null);
      }
    } catch {
      setErrorMsg('Unable to retrieve baseline metrics from backend.');
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBenchmark();
  }, [fetchBenchmark]);

  const b = report?.baseline_metrics;
  const e = report?.evidenroute_metrics;
  const imp = report?.improvements;

  // Real token savings percentage computed strictly from actual values
  const tokenSavingsPct =
    b && e && b.budget_tokens_consumed > 0
      ? (((b.budget_tokens_consumed - e.budget_tokens_consumed) / b.budget_tokens_consumed) * 100).toFixed(1)
      : null;

  return (
    <div className="eval-page-container">
      {/* 1. Header */}
      <header className="eval-page-header">
        <div className="eval-header-title-group">
          <div className="eval-badge-row">
            <span className="eval-badge">
              <CheckCircle2 size={13} />
              Evaluation Benchmark Suite
            </span>
            {b && <span className="eval-badge">{b.total_queries} Benchmark Scenarios</span>}
          </div>
          <h1 className="eval-page-title">Evaluation & Baseline Comparison</h1>
          <p className="eval-page-subtitle">
            Measuring context precision, call quota efficiency, and contradiction detection
            comparing a naive all-source broadcast baseline against EvidenRoute&apos;s intelligent routing.
          </p>
        </div>

        <button
          type="button"
          className="eval-refresh-btn"
          onClick={fetchBenchmark}
          disabled={isLoading}
          title="Re-run evaluation benchmark against live backend"
        >
          <RotateCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>{isLoading ? 'Evaluating...' : 'Run Benchmark'}</span>
        </button>
      </header>

      {/* Loading State */}
      {isLoading ? (
        <div className="eval-table-card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
          <span className="qw-evidence-spinner" />
          <h3 style={{ margin: '1rem 0 0.5rem', color: 'var(--text-primary)' }}>
            Executing Baseline Benchmark Comparison...
          </h3>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            Evaluating naive all-sources retrieval against EvidenRoute intelligent pipeline across test queries.
          </p>
        </div>
      ) : errorMsg || !report || !b || !e || !imp ? (
        /* Empty / Unavailable State */
        <div className="eval-table-card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', padding: '0.75rem', borderRadius: '50%', backgroundColor: '#FEF2F2', color: '#EF4444', marginBottom: '0.75rem' }}>
            <AlertCircle size={32} />
          </div>
          <h3 style={{ margin: '0 0 0.5rem', color: 'var(--text-primary)' }}>
            No evaluation results available
          </h3>
          <p style={{ margin: '0 0 1.25rem', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            {errorMsg || 'Could not load benchmark evaluation from backend (GET /api/intelligence/benchmark/baseline-comparison).'}
          </p>
          <button
            type="button"
            className="eval-refresh-btn"
            onClick={fetchBenchmark}
            style={{ margin: '0 auto' }}
          >
            <RotateCw size={14} />
            <span>Retry Benchmark</span>
          </button>
        </div>
      ) : (
        <>
          {/* 2. Top KPI Cards — All Values Strictly Derived from Backend Report */}
          <section className="eval-kpi-grid" aria-label="Key Performance Indicators">
            <div className="eval-kpi-card">
              <div className="eval-kpi-header">
                <span>Call Quota Reduction</span>
                <Zap size={16} />
              </div>
              <div className="eval-kpi-value green">
                {imp.call_budget_reduction_pct.toFixed(1)}%
              </div>
              <p className="eval-kpi-subtext">
                Calls reduced from {b.budget_calls_consumed} to {e.budget_calls_consumed} across {b.total_queries} test queries
              </p>
            </div>

            <div className="eval-kpi-card">
              <div className="eval-kpi-header">
                <span>Noise Reduction</span>
                <Filter size={16} />
              </div>
              <div className="eval-kpi-value green">
                {imp.irrelevant_passages_filtered_pct.toFixed(1)}%
              </div>
              <p className="eval-kpi-subtext">
                Average {e.average_passages_retrieved} targeted passage vs {b.average_passages_retrieved} unfiltered passages
              </p>
            </div>

            <div className="eval-kpi-card">
              <div className="eval-kpi-header">
                <span>Token Budget Saved</span>
                <Layers size={16} />
              </div>
              <div className="eval-kpi-value green">
                {tokenSavingsPct ? `${tokenSavingsPct}%` : 'N/A'}
              </div>
              <p className="eval-kpi-subtext">
                {e.budget_tokens_consumed.toLocaleString()} tokens consumed vs {b.budget_tokens_consumed.toLocaleString()} in baseline
              </p>
            </div>

            <div className="eval-kpi-card">
              <div className="eval-kpi-header">
                <span>Contradiction Detection</span>
                <ShieldCheck size={16} />
              </div>
              <div className="eval-kpi-value green">
                {(e.contradiction_accuracy * 100).toFixed(1)}%
              </div>
              <p className="eval-kpi-subtext">
                Detects version and metric discrepancies vs {(b.contradiction_accuracy * 100).toFixed(1)}% in naive baseline
              </p>
            </div>
          </section>

          {/* 3. Detailed Side-by-Side Comparison Table */}
          <section className="eval-table-card">
            <div className="eval-card-header">
              <h2 className="eval-card-title">Side-by-Side Evaluation Matrix</h2>
              <p className="eval-card-desc">
                Direct comparison across verified benchmark metrics measured over {b.total_queries} production queries.
              </p>
            </div>

            <div className="eval-table-wrapper">
              <table className="eval-comparison-table">
                <thead>
                  <tr>
                    <th style={{ width: '25%' }}>Evaluation Metric</th>
                    <th style={{ width: '35%' }}>What It Means</th>
                    <th style={{ width: '15%' }}>Naive Baseline</th>
                    <th style={{ width: '15%' }}>EvidenRoute</th>
                    <th style={{ width: '10%' }}>Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <div className="eval-metric-title">Source Calls Consumed</div>
                    </td>
                    <td>
                      <div className="eval-metric-meaning">
                        Total external API/database lookups required across {b.total_queries} benchmark questions.
                      </div>
                    </td>
                    <td>
                      <span className="eval-val-badge muted">{b.budget_calls_consumed} calls</span>
                    </td>
                    <td>
                      <span className="eval-val-badge highlight">{e.budget_calls_consumed} calls</span>
                    </td>
                    <td>
                      <span className="eval-gain-pill">-{imp.call_budget_reduction_pct.toFixed(0)}%</span>
                    </td>
                  </tr>

                  <tr>
                    <td>
                      <div className="eval-metric-title">Context Tokens Consumed</div>
                    </td>
                    <td>
                      <div className="eval-metric-meaning">
                        Total text tokens loaded into context. Fewer tokens reduce latency and LLM cost.
                      </div>
                    </td>
                    <td>
                      <span className="eval-val-badge muted">{b.budget_tokens_consumed.toLocaleString()} tokens</span>
                    </td>
                    <td>
                      <span className="eval-val-badge highlight">{e.budget_tokens_consumed.toLocaleString()} tokens</span>
                    </td>
                    <td>
                      <span className="eval-gain-pill">
                        {tokenSavingsPct ? `-${tokenSavingsPct}%` : 'N/A'}
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td>
                      <div className="eval-metric-title">Average Passages Retrieved</div>
                    </td>
                    <td>
                      <div className="eval-metric-meaning">
                        Number of candidate passages returned per query. Over-retrieval causes context dilution.
                      </div>
                    </td>
                    <td>
                      <span className="eval-val-badge muted">{b.average_passages_retrieved} passages</span>
                    </td>
                    <td>
                      <span className="eval-val-badge highlight">{e.average_passages_retrieved} passage</span>
                    </td>
                    <td>
                      <span className="eval-gain-pill">-{imp.irrelevant_passages_filtered_pct.toFixed(0)}%</span>
                    </td>
                  </tr>

                  <tr>
                    <td>
                      <div className="eval-metric-title">Contradiction Accuracy</div>
                    </td>
                    <td>
                      <div className="eval-metric-meaning">
                        Accuracy in detecting factual discrepancies, metric conflicts, and superseded versions.
                      </div>
                    </td>
                    <td>
                      <span className="eval-val-badge muted">{(b.contradiction_accuracy * 100).toFixed(1)}%</span>
                    </td>
                    <td>
                      <span className="eval-val-badge highlight">{(e.contradiction_accuracy * 100).toFixed(1)}%</span>
                    </td>
                    <td>
                      <span className="eval-gain-pill">
                        +{((e.contradiction_accuracy - b.contradiction_accuracy) * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td>
                      <div className="eval-metric-title">Average Retrieval Latency</div>
                    </td>
                    <td>
                      <div className="eval-metric-meaning">
                        Time taken in milliseconds to analyze intent, select sources, and rank evidence.
                      </div>
                    </td>
                    <td>
                      <span className="eval-val-badge muted">{b.average_latency_ms.toFixed(2)} ms</span>
                    </td>
                    <td>
                      <span className="eval-val-badge highlight">{e.average_latency_ms.toFixed(2)} ms</span>
                    </td>
                    <td>
                      <span className="eval-gain-pill">{e.average_latency_ms.toFixed(1)}ms</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* 4. Visual Comparison Cards Computed Strictly from Actual Backend Metrics */}
          <section className="eval-visual-grid" aria-label="Visual Metric Comparisons">
            <div className="eval-visual-card">
              <h3 className="eval-visual-title">API Source Calls</h3>
              <div className="eval-bar-group">
                <div className="eval-bar-item">
                  <div className="eval-bar-labels">
                    <span className="eval-bar-name">Naive Baseline (Broadcast All)</span>
                    <span className="eval-bar-value">{b.budget_calls_consumed} calls</span>
                  </div>
                  <div className="eval-bar-track">
                    <div className="eval-bar-fill baseline" style={{ width: '100%' }} />
                  </div>
                </div>

                <div className="eval-bar-item">
                  <div className="eval-bar-labels">
                    <span className="eval-bar-name">EvidenRoute (Intelligent Routing)</span>
                    <span className="eval-bar-value">{e.budget_calls_consumed} calls</span>
                  </div>
                  <div className="eval-bar-track">
                    <div
                      className="eval-bar-fill evidenroute"
                      style={{
                        width: `${Math.max(
                          (e.budget_calls_consumed / (b.budget_calls_consumed || 1)) * 100,
                          4
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="eval-visual-card">
              <h3 className="eval-visual-title">Context Tokens Consumed</h3>
              <div className="eval-bar-group">
                <div className="eval-bar-item">
                  <div className="eval-bar-labels">
                    <span className="eval-bar-name">Naive Baseline (All Passages)</span>
                    <span className="eval-bar-value">{b.budget_tokens_consumed.toLocaleString()} tokens</span>
                  </div>
                  <div className="eval-bar-track">
                    <div className="eval-bar-fill baseline" style={{ width: '100%' }} />
                  </div>
                </div>

                <div className="eval-bar-item">
                  <div className="eval-bar-labels">
                    <span className="eval-bar-name">EvidenRoute (Pruned & Ranked)</span>
                    <span className="eval-bar-value">{e.budget_tokens_consumed.toLocaleString()} tokens</span>
                  </div>
                  <div className="eval-bar-track">
                    <div
                      className="eval-bar-fill evidenroute"
                      style={{
                        width: `${Math.max(
                          (e.budget_tokens_consumed / (b.budget_tokens_consumed || 1)) * 100,
                          5
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 5. Explanatory Insights Section */}
          <section className="eval-insights-grid" aria-label="Explanation of Results">
            <div className="eval-insight-card">
              <div className="eval-insight-icon-wrap">
                <Zap size={20} />
              </div>
              <h3 className="eval-insight-heading">Why {imp.call_budget_reduction_pct.toFixed(0)}% Fewer Calls?</h3>
              <p className="eval-insight-desc">
                Standard RAG broadcasts every query to all registered enterprise stores. EvidenRoute
                evaluates semantic domain relevance before fetching, searching only the most
                authoritative sources.
              </p>
            </div>

            <div className="eval-insight-card">
              <div className="eval-insight-icon-wrap">
                <Filter size={20} />
              </div>
              <h3 className="eval-insight-heading">Why Fewer Passages Are Better</h3>
              <p className="eval-insight-desc">
                Flooding LLMs with {b.average_passages_retrieved} candidate passages introduces noise and increases hallucination.
                EvidenRoute scores evidence across 4 dimensions, keeping only the most direct and
                fresh passages ({e.average_passages_retrieved} on average).
              </p>
            </div>

            <div className="eval-insight-card">
              <div className="eval-insight-icon-wrap">
                <ShieldCheck size={20} />
              </div>
              <h3 className="eval-insight-heading">How Conflicts Are Detected</h3>
              <p className="eval-insight-desc">
                When policies evolve, EvidenRoute compares passage claims and timestamps to flag
                discrepancies with {(e.contradiction_accuracy * 100).toFixed(1)}% accuracy, shielding users from stale facts.
              </p>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default EvaluationPage;
