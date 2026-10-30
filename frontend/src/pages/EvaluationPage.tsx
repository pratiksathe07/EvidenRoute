import React, { useEffect, useState, useCallback } from 'react';
import {
  Award,
  CheckCircle2,
  Clock,
  ShieldCheck,
  FileSearch,
  TrendingUp,
  Zap,
  BarChart2,
  Info,
  Scale,
} from 'lucide-react';
import {
  fetchEvaluationReport,
  EvaluationReport,
} from '../services/evaluationService';
import './EvaluationPage.css';

export const EvaluationPage: React.FC = () => {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  

  const loadReport = useCallback(async () => {
    
    const res = await fetchEvaluationReport();
    if (res.data) {
      setReport(res.data);
    }
    
  }, []);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const getFactorIcon = (id: string) => {
    switch (id) {
      case 'relevance':
        return <FileSearch size={18} className="text-blue" />;
      case 'freshness':
        return <Clock size={18} className="text-orange" />;
      case 'correctness':
        return <CheckCircle2 size={18} className="text-emerald" />;
      case 'authority':
      default:
        return <ShieldCheck size={18} className="text-purple" />;
    }
  };

  return (
    <div className="eval-container">
      {/* 1. Header Banner */}
      <header className="eval-header">
        <div className="eval-header-content">
          <div className="eval-badge-row">
            <span className="eval-badge">
              <Award size={13} />
              <span>Evidence Quality & Benchmark Evaluation</span>
            </span>
          </div>
          <h1 className="eval-title">Evidence Evaluation</h1>
          <p className="eval-subtitle">
            Understand how good and trustworthy the retrieved evidence is across four foundational factors:
            Relevance, Freshness, Correctness, and Authority.
          </p>
        </div>
      </header>

      {/* 2. Overall Quality & Summary Card */}
      {report && (
        <section className="eval-hero-card">
          <div className="eval-hero-score-box">
            <span className="eval-hero-score-label">Overall Evidence Quality</span>
            <div className="eval-hero-score-val">{report.overallQualityScore}%</div>
            <div className="eval-hero-verdict-pill">
              <CheckCircle2 size={13} />
              <span>{report.overallVerdict}</span>
            </div>
          </div>

          <div className="eval-hero-summary-box">
            <h2 className="eval-summary-title">Dataset Evaluation Summary</h2>
            <p className="eval-summary-text">{report.summaryText}</p>
            <div className="eval-summary-stats">
              <div className="eval-stat-chip">
                <span className="stat-label">Evaluated Benchmarks</span>
                <span className="stat-val">{report.comparison.total_queries_evaluated} Benchmark Questions</span>
              </div>
              <div className="eval-stat-chip">
                <span className="stat-label">Irrelevant Noise Pruned</span>
                <span className="stat-val text-emerald">{report.comparison.noise_reduction_pct}% Noise Reduction</span>
              </div>
              <div className="eval-stat-chip">
                <span className="stat-label">Precision Gain</span>
                <span className="stat-val text-blue">+{report.comparison.precision.gain_pct}% over Baseline</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 3. The Four Main Evaluation Factors */}
      <section className="eval-factors-section">
        <div className="eval-section-title-wrap">
          <Scale size={18} className="text-accent" />
          <h2 className="eval-section-title">The Four Evidence Factors</h2>
        </div>

        {report && (
          <div className="eval-factors-grid">
            {report.factors.map((factor) => (
              <div key={factor.id} className="eval-factor-card">
                <div className="eval-factor-header">
                  <div className="eval-factor-title-group">
                    <div className="eval-factor-icon-wrap">{getFactorIcon(factor.id)}</div>
                    <div>
                      <h3 className="eval-factor-name">{factor.name}</h3>
                      <span className="eval-factor-q">{factor.question}</span>
                    </div>
                  </div>
                  <div className="eval-factor-score-pill">
                    <span className="eval-factor-score-num">{factor.score}%</span>
                  </div>
                </div>

                <div className="eval-factor-meter-wrap">
                  <div className="eval-factor-meter">
                    <div
                      className={`eval-factor-fill ${factor.id}`}
                      style={{ width: `${factor.score}%` }}
                    />
                  </div>
                </div>

                <p className="eval-factor-explanation">{factor.explanation}</p>

                <div className="eval-factor-basis">
                  <Info size={12} />
                  <span>{factor.measurementBasis}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 4. Benchmark Performance: Baseline vs EvidenRoute */}
      {report && (
        <section className="eval-comparison-section">
          <div className="eval-section-title-wrap">
            <BarChart2 size={18} className="text-accent" />
            <h2 className="eval-section-title">Benchmark Comparison: Naive Baseline vs EvidenRoute</h2>
          </div>

          <div className="eval-table-wrap">
            <table className="eval-table">
              <thead>
                <tr>
                  <th>Performance Factor</th>
                  <th>Naive Baseline (All Sources Polled)</th>
                  <th>EvidenRoute Engine (Intelligent Selection)</th>
                  <th>Observed Improvement</th>
                </tr>
              </thead>
              <tbody>
                {report.metricsTable.map((row, idx) => (
                  <tr key={idx}>
                    <td>
                      <div className="eval-metric-name">{row.label}</div>
                      <div className="eval-metric-desc">{row.description}</div>
                    </td>
                    <td className="text-muted font-mono">{row.baseline}</td>
                    <td className="text-primary font-mono font-semibold">{row.evidenroute}</td>
                    <td>
                      <span className="eval-improvement-badge positive">
                        <TrendingUp size={13} />
                        <span>{row.improvement}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 5. Performance Across Test Queries */}
      {report && report.testQueries.length > 0 && (
        <section className="eval-queries-section">
          <div className="eval-section-title-wrap">
            <Zap size={18} className="text-accent" />
            <h2 className="eval-section-title">Performance Across Test Queries</h2>
          </div>

          <div className="eval-queries-grid">
            {report.testQueries.map((tq) => (
              <div key={tq.id} className="eval-tq-card">
                <div className="eval-tq-top">
                  <h4 className="eval-tq-question">&ldquo;{tq.question}&rdquo;</h4>
                  <span className="eval-tq-status-badge">
                    <CheckCircle2 size={12} />
                    <span>{tq.correctnessStatus}</span>
                  </span>
                </div>

                <div className="eval-tq-scores-row">
                  <div className="eval-tq-score-item">
                    <span className="tq-score-label">Relevance</span>
                    <span className="tq-score-val">{tq.relevanceScore}%</span>
                  </div>
                  <div className="eval-tq-score-item">
                    <span className="tq-score-label">Freshness</span>
                    <span className="tq-score-val">{tq.freshnessScore}%</span>
                  </div>
                  <div className="eval-tq-score-item">
                    <span className="tq-score-label">Correctness</span>
                    <span className="tq-score-val text-emerald font-semibold">{tq.correctnessScore}%</span>
                  </div>
                  <div className="eval-tq-score-item">
                    <span className="tq-score-label">Authority</span>
                    <span className="tq-score-val">{tq.authorityScore}%</span>
                  </div>
                </div>

                <p className="eval-tq-explanation">{tq.explanation}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default EvaluationPage;
