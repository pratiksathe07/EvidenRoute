/**
 * Type definitions matching the actual EvidenRoute Backend Pydantic Models
 * and REST APIs (FastAPI /api/sources and /api/query).
 */

/**
 * Source types supported by EvidenRoute engine
 */
export type SourceType = 'document' | 'conversation' | 'ticket' | 'web' | 'database';

/**
 * SourceInfo matching backend.app.schemas.source.SourceInfo
 * Returned by GET /api/sources
 */
export interface SourceInfo {
  source_id: string;
  name: string;
  source_type: SourceType | string;
  description: string;
  default_authority: number;
  enabled: boolean;
  record_count: number;
  last_ingested_at?: string | null;
  status: string; // 'healthy' | 'disabled' | 'offline'
  metadata: Record<string, unknown>;
}

/**
 * Extended SourceMetadata for component rendering and backwards-compatibility
 */
export interface SourceMetadata extends SourceInfo {
  source_name?: string;
  authority_level?: string | number;
  availability?: string | boolean;
  supported_topics?: string[];
}

/**
 * SourceSelectionDecision matching backend.app.schemas.source.SourceSelectionDecision
 * Produced during Step 2 of the Query Orchestration pipeline
 */
export interface SourceSelectionDecision {
  source_id: string;
  selected: boolean;
  relevance_score: number;
  reason: string;
  allocated_limit: number;
}

/**
 * TraceStep matching backend.app.schemas.query.TraceStep
 * Audit log for each pipeline phase
 */
export interface TraceStep {
  step_name: string;
  timestamp: string;
  status: string;
  duration_ms: number;
  summary: string;
  details: Record<string, unknown>;
}

/**
 * Budget schemas matching backend.app.schemas.budget
 */
export interface BudgetConfig {
  max_source_calls: number;
  max_candidates: number;
  max_tokens: number;
}

export interface BudgetUsage {
  calls_consumed: number;
  candidates_consumed: number;
  tokens_consumed: number;
}

export interface BudgetStatus {
  configured: BudgetConfig;
  consumed: BudgetUsage;
  remaining_calls: number;
  remaining_candidates: number;
  remaining_tokens: number;
  is_exhausted: boolean;
}

/**
 * Normalized evidence and scoring schemas matching backend.app.schemas.evidence
 */
export interface NormalizedEvidence {
  evidence_id: string;
  source_id: string;
  source_type: SourceType | string;
  title: string;
  content: string;
  uri?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  author?: string | null;
  authority_score: number;
  metadata?: Record<string, unknown>;
}

export interface EvidenceScore {
  evidence_id: string;
  relevance_score: number;
  authority_score: number;
  freshness_score: number;
  directness_score: number;
  composite_score: number;
  evaluation_notes?: string | null;
}

export interface ContradictionItem {
  conflict_id: string;
  evidence_a_id: string;
  evidence_b_id: string;
  contradiction_type: string;
  description: string;
  severity: string;
  resolution_status: string;
  resolution_reasoning?: string | null;
}

export interface StressTestResult {
  executed: boolean;
  hypothesis_tested?: string | null;
  verification_query?: string | null;
  counterevidence_found: boolean;
  supporting_evidence_found: boolean;
  evidence_examined_count: number;
  budget_used_calls: number;
  impact_on_decision: string;
  summary: string;
}

/**
 * Comprehensive response returned by POST /api/query
 */
export interface QueryResponse {
  query_id: string;
  question: string;
  outcome: 'ANSWER' | 'RETRIEVE_MORE' | 'ABSTAIN';
  final_answer?: string | null;
  abstention_reason?: string | null;
  citations: string[];
  selected_sources: SourceSelectionDecision[];
  retrieved_evidence: NormalizedEvidence[];
  evidence_scores: EvidenceScore[];
  contradictions: ContradictionItem[];
  budget_status: BudgetStatus;
  stress_test: StressTestResult;
  execution_trace: TraceStep[];
}

/**
 * Request payload sent to POST /api/query
 */
export interface QueryRequest {
  question: string;
  budget?: Partial<BudgetConfig> | null;
  enable_stress_test?: boolean;
}

/**
 * Score breakdown details for multi-criteria ranking display
 */
export interface ScoreBreakdown {
  type_suitability?: number;
  keyword_relevance?: number;
  base_authority?: number;
  historical_usefulness?: number | null;
  allocated_limit?: number;
  reason?: string;
  [key: string]: unknown;
}

/**
 * Source ranking result from decision_trace.ranked_sources
 */
export interface SourceRankResult {
  source_id: string;
  source_name: string;
  source_type: string;
  relevance_score: number;
  type_suitability_score: number;
  authority_score: number;
  historical_usefulness_score: number | null; // Nullable! Displays "N/A" when null
  availability_score: number;
  final_score: number;
  selection_status: 'selected' | 'skipped';
  selection_reason: string;
  ranking_position: number;
  score_breakdown?: ScoreBreakdown;
}

/**
 * Query analysis produced by the intent & entity analyzer
 */
export interface QueryAnalysis {
  intent: string;
  confidence: number;
  keywords: string[];
  entities: string[];
  technical_terms: string[];
  information_category: string;
  expected_information: string;
  likely_source_types: string[];
  analyzer_type: string;
  limitations_note?: string;
}

/**
 * Full explainable decision trace for Source Selection Studio
 */
export interface DecisionTrace {
  query: string;
  analysis: QueryAnalysis;
  available_sources_count: number;
  evaluated_sources_count: number;
  selected_sources_count: number;
  skipped_sources_count: number;
  ranked_sources: SourceRankResult[];
  execution_time_ms: number;
  config_used: Record<string, unknown>;
  notes: string[];
  trace_steps?: TraceStep[];
}

/**
 * Response schema for Source Selection Studio
 */
export interface PlanResponse {
  decision_trace: DecisionTrace;
  raw_query_response?: QueryResponse;
}

/**
 * Request payload for Source Selection Studio
 */
export interface PlanRequest {
  question: string;
  config?: Record<string, unknown> | null;
  budget?: Partial<BudgetConfig> | null;
}

/**
 * Request payload for standalone selection
 */
export interface SelectSourcesRequest {
  question: string;
  config?: Record<string, unknown> | null;
  sources?: SourceMetadata[] | null;
}
