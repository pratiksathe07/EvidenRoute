import apiClient from './api';
import {
  SystemHealthResponse,
  SourceItem,
  EvaluationResult,
  QueryRunItem,
  RetrievalActivityPoint,
} from '../types/dashboard';

/**
 * Service response wrapper for safe asynchronous state management.
 */
export interface ServiceResponse<T> {
  data: T | null;
  error: string | null;
  isAvailable: boolean;
}

export interface IntelligenceHealthResponse {
  status: string;
  query_analyzer: string;
  source_registry: string;
  source_selector: string;
  external_llm_integration: string;
  active_sources_count: number;
  environment: string;
}

export interface IngestionStatusResponse {
  status: string;
  total_chunks_indexed: number;
  last_report?: Record<string, unknown> | null;
}

/**
 * 1. Check Backend & Engine Health (GET /api/health)
 * Real backend response: { "status": "healthy", "service": "...", "version": "1.0.0", "database": "sqlite" }
 */
export async function getSystemHealth(): Promise<ServiceResponse<SystemHealthResponse>> {
  try {
    const response = await apiClient.get<SystemHealthResponse>('/api/health');
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Backend connection unavailable (/api/health)';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 2. Check Intelligence Health (GET /api/intelligence/health)
 */
export async function getIntelligenceHealth(): Promise<ServiceResponse<IntelligenceHealthResponse>> {
  try {
    const response = await apiClient.get<IntelligenceHealthResponse>('/api/intelligence/health');
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Intelligence health endpoint unavailable';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 3. Fetch Ingestion Status (GET /api/intelligence/ingestion-status)
 */
export async function getIngestionStatus(): Promise<ServiceResponse<IngestionStatusResponse>> {
  try {
    const response = await apiClient.get<IngestionStatusResponse>('/api/intelligence/ingestion-status');
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Ingestion status endpoint unavailable';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 4. Fetch Connected Sources (GET /api/sources)
 * Real backend response: List[SourceInfo] from database
 */
export async function getSources(): Promise<ServiceResponse<SourceItem[]>> {
  try {
    const response = await apiClient.get<Array<{
      source_id: string;
      name: string;
      source_type: string;
      description: string;
      default_authority: number;
      enabled: boolean;
      record_count: number;
      last_ingested_at?: string | null;
      status: string;
      metadata?: Record<string, unknown>;
    }>>('/api/sources');

    const rawList = Array.isArray(response.data) ? response.data : [];
    const mapped: SourceItem[] = rawList.map((src) => ({
      id: src.source_id,
      name: src.name,
      category: src.source_type,
      status: src.enabled ? 'connected' : 'disconnected',
      itemCount: src.record_count,
      lastSynced: src.last_ingested_at || undefined,
      description: src.description,
    }));

    return {
      data: mapped,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Sources endpoint unavailable (/api/sources)';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 5. Fetch Recent Query History from Real Backend Database (GET /api/query)
 */
export async function getRecentQueries(): Promise<ServiceResponse<QueryRunItem[]>> {
  try {
    const response = await apiClient.get<Array<{
      query_id: string;
      question: string;
      outcome: string;
      final_answer: string | null;
      budget_calls_consumed: number;
      budget_tokens_consumed: number;
      stress_test_executed: boolean;
      stress_test_impact: string;
      created_at: string;
    }>>('/api/query');

    const mapped: QueryRunItem[] = (response.data || []).map((r) => ({
      id: r.query_id,
      query: r.question,
      selectedSources: [],
      evidenceCount: r.budget_calls_consumed,
      budgetUsed: `${r.budget_tokens_consumed} tokens (${r.budget_calls_consumed} calls)`,
      answerStatus:
        r.outcome === 'ANSWER'
          ? 'verified'
          : r.outcome === 'RETRIEVE_MORE'
          ? 'partial'
          : 'failed',
      timestamp: r.created_at ? new Date(r.created_at).toLocaleTimeString() : 'Recent',
    }));

    return {
      data: mapped,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Query history unavailable (/api/query)';
    return {
      data: [],
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 6. Build real Activity timeseries from recorded queries
 */
export function buildActivityFromQueries(queries: QueryRunItem[]): RetrievalActivityPoint[] {
  if (!queries || queries.length === 0) return [];

  // Reverse so oldest first, newest last
  const chronological = [...queries].reverse();

  return chronological.map((q, idx) => {
    const match = q.budgetUsed?.match(/(\d+)\s*tokens/);
    const tokens = match ? parseInt(match[1], 10) : 0;
    return {
      time: q.timestamp || `#${idx + 1}`,
      queries: 1,
      evidence: q.evidenceCount || 1,
      budgetTokens: tokens,
    };
  });
}

/**
 * 7. Fetch Evaluation Benchmarks (GET /api/evaluate/results)
 */
export async function getEvaluationResults(): Promise<ServiceResponse<EvaluationResult>> {
  try {
    const response = await apiClient.get<EvaluationResult>('/api/evaluate/results');
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Evaluation results endpoint not available';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 8. Fetch Retrieval Activity Timeseries from Telemetry (if available)
 */
export async function getRetrievalActivity(): Promise<ServiceResponse<RetrievalActivityPoint[]>> {
  try {
    const response = await apiClient.get<RetrievalActivityPoint[]>('/api/telemetry/retrieval-activity');
    return {
      data: response.data || [],
      error: null,
      isAvailable: true,
    };
  } catch {
    return {
      data: [],
      error: null,
      isAvailable: false,
    };
  }
}
