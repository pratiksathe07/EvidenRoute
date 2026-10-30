/**
 * EvidenRoute - Evidence Retrieval & Evaluation Type Definitions
 * Matches backend.app.intelligence.models.py (FastAPI /api/intelligence/retrieve)
 */

import { QueryAnalysis } from './sourceSelection';

/**
 * Multi-dimensional 4D evidence scoring breakdown
 */
export interface EvidenceScore {
  relevance_score: number;
  authority_score: number;
  freshness_score: number | null;
  freshness_status: 'fresh' | 'decayed' | 'stale' | 'unknown' | string;
  directness_score: number;
  directness_label: 'direct' | 'supporting' | 'indirect' | 'tangential' | string;
  final_evidence_score: number;
  scoring_explanation: string;
  weights_applied?: {
    relevance?: number;
    authority?: number;
    directness?: number;
    freshness?: number;
    [key: string]: number | undefined;
  };
}

/**
 * Ranked evidence passage retrieved from selected grounding sources
 */
export interface EvidencePassage {
  chunk_id: string;
  source_id: string;
  source_name: string;
  source_type: string;
  record_id: string;
  title: string;
  content: string;
  authority_level: number;
  created_at?: string | null;
  original_file_path: string;
  chunk_index: number;
  retrieval_score: number;
  bm25_score: number;
  semantic_score?: number | null;
  retrieval_mode: 'lexical_only' | 'hybrid' | string;
  evidence_score: EvidenceScore;
  citation: string;
  ranking_position: number;
}

/**
 * Passage reference involved in detected contradiction
 */
export interface ConflictingPassageRef {
  chunk_id: string;
  source_id: string;
  source_name: string;
  citation: string;
  statement: string;
  timestamp?: string | null;
}

/**
 * Explainable conflict report between two or more evidence passages
 */
export interface ConflictReport {
  conflict_id: string;
  conflict_type:
    | 'direct_contradiction'
    | 'temporal_supersedence'
    | 'version_divergence'
    | 'status_progression'
    | 'contextual_difference'
    | string;
  topic: string;
  is_direct_contradiction: boolean;
  severity: 'critical' | 'warning' | 'info' | string;
  conflicting_passages: ConflictingPassageRef[];
  explanation: string;
  resolution_hint?: string | null;
}

/**
 * Sufficiency evaluation result
 */
export interface EvidenceSufficiencyResult {
  is_sufficient: boolean;
  sufficiency_score: number;
  sufficiency_status: 'sufficient' | 'partially_sufficient' | 'insufficient' | 'conflicted' | string;
  supporting_evidence?: EvidencePassage[];
  missing_information: string[];
  conflicts_detected?: ConflictReport[];
  explanation: string;
  recommended_action: 'answer' | 'retrieve_more' | 'clarify' | 'abstain' | string;
  dimension_scores?: Record<string, number>;
}

/**
 * Context compression and deduplication result
 */
export interface PrunedContextResult {
  original_passages_count: number;
  retained_passages_count: number;
  original_sentence_count: number;
  retained_sentence_count: number;
  pruned_sentence_count: number;
  retained_evidence?: EvidencePassage[];
  conflict_passages_preserved_count: number;
  compression_ratio: number;
}

/**
 * Final Answer Readiness verdict synthesized across sufficiency and conflicts
 */
export interface AnswerReadinessResult {
  is_ready_to_answer: boolean;
  readiness_verdict:
    | 'READY_TO_ANSWER'
    | 'NEEDS_CLARIFICATION'
    | 'ABSTAIN_INSUFFICIENT_EVIDENCE'
    | 'ABSTAIN_UNRESOLVED_CONFLICT'
    | string;
  recommended_action: 'answer' | 'clarify' | 'abstain' | 'retrieve_more' | string;
  confidence_score: number;
  primary_justification: string;
  conflicts_summary?: {
    total_detected?: number;
    direct_contradictions?: number;
    has_unresolved?: boolean;
    [key: string]: unknown;
  };
  sufficiency_summary?: {
    is_sufficient?: boolean;
    score?: number;
    status?: string;
    missing_info_count?: number;
    [key: string]: unknown;
  };
  pruning_summary?: {
    original_sentences?: number;
    retained_sentences?: number;
    pruned_sentences?: number;
    compression_ratio?: number;
    conflicts_preserved?: number;
    [key: string]: unknown;
  };
}

/**
 * Retrieval decision trace
 */
export interface RetrievalDecisionTrace {
  query: string;
  analysis: QueryAnalysis;
  selected_source_ids: string[];
  skipped_source_ids: string[];
  retrieval_mode: string;
  total_candidate_chunks_evaluated: number;
  retrieved_evidence_count: number;
  retrieved_evidence: EvidencePassage[];
  execution_time_ms: number;
  budget_info?: Record<string, unknown>;
  trace_stages: string[];
  conflicts?: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  pruned_context?: PrunedContextResult;
  answer_readiness?: AnswerReadinessResult;
}

/**
 * Request payload for POST /api/intelligence/retrieve
 */
export interface RetrieveRequest {
  question: string;
  top_k?: number;
  selection_config?: Record<string, unknown> | null;
  retrieval_config?: Record<string, unknown> | null;
}

/**
 * Response payload from POST /api/intelligence/retrieve
 */
export interface RetrieveResponse {
  query: string;
  query_analysis: QueryAnalysis;
  selected_sources: string[];
  skipped_sources: string[];
  retrieval_mode: string;
  retrieved_evidence: EvidencePassage[];
  decision_trace: RetrievalDecisionTrace;
  conflicts: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  pruned_context?: PrunedContextResult;
  answer_readiness?: AnswerReadinessResult;
}

/**
 * Retrieval health check response (GET /api/intelligence/retrieval-health)
 */
export interface RetrievalHealthResponse {
  status: string;
  ingestion_status: {
    total_chunks_indexed: number;
    status: string;
  };
  bm25_status: string;
  semantic_model_status: Record<string, unknown>;
  active_retrieval_mode: string;
  evidence_scorer_status: string;
}
