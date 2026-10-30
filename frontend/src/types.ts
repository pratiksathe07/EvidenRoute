export interface QueryAnalysisResult {
  intent: string;
  confidence: number;
  keywords: string[];
  entities: string[];
  technical_terms: string[];
  information_category: string;
  expected_information: string[];
  likely_source_types: string[];
  analyzer_type: string;
  limitations_note?: string;
}

export interface SourceScoreBreakdown {
  relevance_score: number;
  type_suitability_score: number;
  authority_score: number;
  historical_usefulness_score: number | null;
  availability_score: number;
  weights_applied: Record<string, number>;
  calculation_notes: string[];
}

export interface SourceRankResult {
  source_id: string;
  source_name: string;
  source_type: string;
  relevance_score: number;
  type_suitability_score: number;
  authority_score: number;
  historical_usefulness_score: number | null;
  availability_score: number;
  final_score: number;
  selection_status: 'selected' | 'skipped';
  selection_reason: string;
  ranking_position: number;
  score_breakdown?: SourceScoreBreakdown;
}

export interface SelectionConfig {
  relevance_weight: number;
  suitability_weight: number;
  authority_weight: number;
  historical_weight: number;
  availability_weight: number;
  selection_threshold: number;
  min_relevance_threshold: number;
}

export interface PipelineDecisionTrace {
  query: string;
  analysis: QueryAnalysisResult;
  available_sources_count: number;
  evaluated_sources_count: number;
  selected_sources_count: number;
  skipped_sources_count: number;
  ranked_sources: SourceRankResult[];
  execution_time_ms: number;
  config_used: SelectionConfig;
  notes: string[];
}

export interface HealthResponse {
  status: string;
  query_analyzer: string;
  source_registry: string;
  source_selector: string;
  external_llm_integration: string;
  active_sources_count: number;
  environment: string;
}

// Phase 2 Types
export interface EvidenceScore {
  relevance_score: number;
  authority_score: number;
  freshness_score: number | null;
  freshness_status: string;
  directness_score: number;
  directness_label: string;
  final_evidence_score: number;
  scoring_explanation: string;
  weights_applied: Record<string, number>;
}

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
  semantic_score: number | null;
  retrieval_mode: string;
  evidence_score: EvidenceScore;
  citation: string;
  ranking_position: number;
}

export interface RetrievalDecisionTrace {
  query: string;
  analysis: QueryAnalysisResult;
  selected_source_ids: string[];
  skipped_source_ids: string[];
  retrieval_mode: string;
  total_candidate_chunks_evaluated: number;
  retrieved_evidence_count: number;
  retrieved_evidence: EvidencePassage[];
  execution_time_ms: number;
  budget_info: Record<string, any>;
  trace_stages: string[];
  conflicts?: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  pruned_context?: PrunedContextResult;
  answer_readiness?: AnswerReadinessResult;
  counter_evidence?: CounterEvidenceResult;
  evidence_reliability?: EvidenceReliabilityResult;
}

export interface RetrieveResponse {
  query: string;
  query_analysis: QueryAnalysisResult;
  selected_sources: string[];
  skipped_sources: string[];
  retrieval_mode: string;
  retrieved_evidence: EvidencePassage[];
  decision_trace: RetrievalDecisionTrace;
  conflicts?: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  pruned_context?: PrunedContextResult;
  answer_readiness?: AnswerReadinessResult;
  counter_evidence?: CounterEvidenceResult;
  evidence_reliability?: EvidenceReliabilityResult;
}

export interface CounterEvidenceResult {
  executed: boolean;
  challenge_query?: string | null;
  counter_evidence_found: boolean;
  supporting_evidence_found: boolean;
  evidence_examined_count: number;
  new_passages_retrieved_count: number;
  budget_used_calls: number;
  budget_exhausted: boolean;
  impact_on_decision: string;
  summary: string;
  discovered_passages: EvidencePassage[];
}

export interface EvidenceReliabilityResult {
  status: string;
  reliability_score: number;
  supporting_evidence_count: number;
  contradictory_evidence_count: number;
  independent_sources_count: number;
  independent_source_ids: string[];
  missing_information: string[];
  confidence_limitations: string[];
  recommended_action: string;
  explanation: string;
}

// Phase 3 Types
export type ConflictType =
  | 'direct_contradiction'
  | 'temporal_supersedence'
  | 'version_divergence'
  | 'status_progression'
  | 'contextual_difference';

export type ConflictSeverity = 'critical' | 'warning' | 'info';

export type RecommendedAction = 'answer' | 'retrieve_more' | 'clarify' | 'abstain';

export type SufficiencyStatus = 'sufficient' | 'partially_sufficient' | 'insufficient' | 'conflicted';

export interface ConflictingPassageRef {
  chunk_id: string;
  source_id: string;
  source_name: string;
  citation: string;
  statement: string;
  timestamp?: string | null;
}

export interface ConflictReport {
  conflict_id: string;
  conflict_type: ConflictType | string;
  topic: string;
  is_direct_contradiction: boolean;
  severity: ConflictSeverity | string;
  conflicting_passages: ConflictingPassageRef[];
  explanation: string;
  resolution_hint?: string | null;
}

export interface ConflictDetectionResult {
  total_passages_evaluated: number;
  conflicts_detected_count: number;
  direct_contradictions_count: number;
  conflicts: ConflictReport[];
  has_unresolved_contradictions: boolean;
}

export interface EvidenceSufficiencyResult {
  is_sufficient: boolean;
  sufficiency_score: number;
  sufficiency_status: SufficiencyStatus | string;
  supporting_evidence: EvidencePassage[];
  missing_information: string[];
  conflicts_detected: ConflictReport[];
  explanation: string;
  recommended_action: RecommendedAction | string;
  dimension_scores: Record<string, number>;
}

export interface PruningDetail {
  chunk_id: string;
  original_file_path: string;
  sentence: string;
  reason: string;
}

export interface PrunedContextResult {
  original_passages_count: number;
  retained_passages_count: number;
  original_sentence_count: number;
  retained_sentence_count: number;
  pruned_sentence_count: number;
  pruned_details: PruningDetail[];
  retained_evidence: EvidencePassage[];
  conflict_passages_preserved_count: number;
  compression_ratio: number;
}

export interface AnswerReadinessResult {
  is_ready_to_answer: boolean;
  readiness_verdict: string;
  recommended_action: RecommendedAction | string;
  confidence_score: number;
  primary_justification: string;
  conflicts_summary: Record<string, any>;
  sufficiency_summary: Record<string, any>;
  pruning_summary: Record<string, any>;
}

