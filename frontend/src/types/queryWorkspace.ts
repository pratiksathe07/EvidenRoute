import {
  RetrieveResponse,
  EvidencePassage,
  ConflictReport,
  EvidenceSufficiencyResult,
  PrunedContextResult,
  CounterEvidenceResult,
  EvidenceReliabilityResult,
} from '../types';
import {
  QueryResponse,
} from './sourceSelection';

/**
 * Pipeline stage status for visual tracking
 */
export type StageStatus = 'pending' | 'running' | 'completed' | 'skipped' | 'failed';

export interface PipelineStageInfo {
  id: string;
  name: string;
  description: string;
  status: StageStatus;
  durationMs?: number;
  summary?: string;
  details?: Record<string, any>;
}

/**
 * Unified execution result combining both the rich intelligence engine output
 * (POST /api/intelligence/retrieve) and the database-persisted orchestrator output (POST /api/query).
 */
export interface WorkspaceExecutionResult {
  queryId?: string;
  question: string;
  outcome: 'ANSWER' | 'RETRIEVE_MORE' | 'CLARIFY' | 'ABSTAIN' | string;
  finalAnswer?: string | null;
  abstentionReason?: string | null;
  isReadyToAnswer: boolean;
  readinessVerdict: string;
  confidenceScore: number;
  primaryJustification: string;
  geminiStatus: {
    isConfigured: boolean;
    provider: string;
    message: string;
  };
  retrievedEvidence: EvidencePassage[];
  conflicts: ConflictReport[];
  sufficiency?: EvidenceSufficiencyResult;
  prunedContext?: PrunedContextResult;
  counterEvidence?: CounterEvidenceResult;
  evidenceReliability?: EvidenceReliabilityResult;
  budgetStatus: {
    callsConsumed: number;
    callsMax: number;
    candidatesConsumed: number;
    candidatesMax: number;
    tokensConsumed: number;
    tokensMax: number;
    isExhausted: boolean;
  };
  stages: PipelineStageInfo[];
  executionTimeMs: number;
  timestamp: string;
  rawRetrieveResponse?: RetrieveResponse;
  rawQueryResponse?: QueryResponse;
}

/**
 * Single item returned from GET /api/query
 */
export interface QueryHistoryRecord {
  query_id: string;
  question: string;
  outcome: string;
  final_answer?: string | null;
  budget_calls_consumed: number;
  budget_tokens_consumed: number;
  stress_test_executed: boolean;
  stress_test_impact?: string;
  created_at: string;
}
