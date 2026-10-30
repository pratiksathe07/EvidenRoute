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
    const errorMessage = err instanceof Error ? err.message : 'Backend connection unavailable';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 2. Fetch Connected Sources (GET /api/sources)
 * Real backend response: List[SourceInfo]
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
    const errorMessage = err instanceof Error ? err.message : 'Sources endpoint not available';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 3. Fetch Evaluation Benchmarks (GET /api/evaluate/results)
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
    const errorMessage = err instanceof Error ? err.message : 'Evaluation results endpoint not available yet';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 4. Fetch Recent Query History from Real Backend (GET /api/query)
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
  } catch {
    return {
      data: [],
      error: null,
      isAvailable: false,
    };
  }
}

/**
 * 5. Fetch Retrieval Activity Timeseries
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
