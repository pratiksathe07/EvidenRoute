import React from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Cpu,
} from 'lucide-react';
import { RetrieveResponse } from '../../types/retrieval';
import './QuerySummary.css';

interface QuerySummaryProps {
  response: RetrieveResponse;
}

export const QuerySummary: React.FC<QuerySummaryProps> = ({ response }) => {
  const {
    query,
    query_analysis,
    selected_sources,
    skipped_sources,
    retrieval_mode,
    retrieved_evidence,
    decision_trace,
    answer_readiness,
  } = response;

  const executionTime = decision_trace?.execution_time_ms ?? null;
  const confidence = answer_readiness?.confidence_score ?? query_analysis?.confidence ?? null;
  const verdict = answer_readiness?.readiness_verdict || 'COMPLETED';
  const isReady = answer_readiness?.is_ready_to_answer ?? true;

  const getVerdictBadge = () => {
    if (isReady && verdict === 'READY_TO_ANSWER') {
      return (
        <span className="verdict-pill ready">
          <CheckCircle2 size={13} />
          <span>Ready to Answer</span>
        </span>
      );
    }
    if (verdict.includes('ABSTAIN')) {
      return (
        <span className="verdict-pill abstain">
          <AlertTriangle size={13} />
          <span>Honest Abstention</span>
        </span>
      );
    }
    if (verdict.includes('CLARIF')) {
      return (
        <span className="verdict-pill clarify">
          <HelpCircle size={13} />
          <span>Needs Clarification</span>
        </span>
      );
    }
    return (
      <span className="verdict-pill completed">
        <CheckCircle2 size={13} />
        <span>{verdict}</span>
      </span>
    );
  };

  return (
    <div className="qw-summary-card">
      <div className="qw-summary-top-row">
        <div className="qw-summary-title-wrap">
          <div className="qw-summary-icon">
            <Activity size={18} />
          </div>
          <div>
            <h3 className="qw-summary-title">Query Execution Summary</h3>
            <p className="qw-summary-query">&ldquo;{query}&rdquo;</p>
          </div>
        </div>

        <div className="qw-summary-badges">
          {getVerdictBadge()}
          <span className="retrieval-mode-pill">
            <Cpu size={12} />
            <span>Mode: {retrieval_mode}</span>
          </span>
        </div>
      </div>

      <div className="qw-summary-grid">
        {/* Metric 1: Intent & Category */}
        <div className="qw-metric-tile">
          <div className="qw-tile-label">
            <Sparkles size={14} className="text-emerald" />
            <span>Identified Intent</span>
          </div>
          <div className="qw-tile-val">{query_analysis?.intent || 'General Inquiry'}</div>
          <div className="qw-tile-sub">
            Category: {query_analysis?.information_category || 'General'}
          </div>
        </div>

        {/* Metric 2: Confidence */}
        <div className="qw-metric-tile">
          <div className="qw-tile-label">
            <ShieldCheck size={14} className="text-emerald" />
            <span>Decision Confidence</span>
          </div>
          <div className="qw-tile-val font-mono">
            {confidence !== null ? `${Math.round(confidence * 100)}%` : '--'}
          </div>
          <div className="qw-tile-sub">
            {answer_readiness?.recommended_action
              ? `Action: ${answer_readiness.recommended_action.toUpperCase()}`
              : 'Multi-criteria score'}
          </div>
        </div>

        {/* Metric 3: Source Routing */}
        <div className="qw-metric-tile">
          <div className="qw-tile-label">
            <Layers size={14} className="text-emerald" />
            <span>Context Sources</span>
          </div>
          <div className="qw-tile-val font-mono">
            <span className="text-emerald">{selected_sources.length}</span>
            <span className="text-muted"> / </span>
            <span className="text-secondary">{selected_sources.length + skipped_sources.length}</span>
          </div>
          <div className="qw-tile-sub">
            {selected_sources.length} selected, {skipped_sources.length} skipped
          </div>
        </div>

        {/* Metric 4: Retrieved Chunks & Timing */}
        <div className="qw-metric-tile">
          <div className="qw-tile-label">
            <Clock size={14} className="text-emerald" />
            <span>Retrieved Evidence</span>
          </div>
          <div className="qw-tile-val font-mono">
            {retrieved_evidence.length} <span className="qw-tile-unit">passages</span>
          </div>
          <div className="qw-tile-sub font-mono">
            {executionTime !== null ? `${executionTime.toFixed(1)} ms latency` : 'Pipeline complete'}
          </div>
        </div>
      </div>
    </div>
  );
};
