import apiClient from './api';
import {
  SourceInfo,
  SourceMetadata,
  PlanRequest,
  PlanResponse,
  SourceRankResult,
} from '../types/sourceSelection';
import { ServiceResponse } from './dashboardService';

/**
 * 1. Fetch available sources from the real backend endpoint:
 * Endpoint: GET /api/intelligence/sources (with fallback to GET /api/sources)
 */
export async function getAvailableSources(): Promise<ServiceResponse<SourceMetadata[]>> {
  try {
    // Prefer intelligence candidate sources
    const response = await apiClient.get<Array<{
      source_id: string;
      source_name: string;
      source_type: string;
      description: string;
      authority_level: number;
      supported_topics: string[];
      availability: boolean;
      metadata?: Record<string, unknown>;
    }>>('/api/intelligence/sources');

    const rawList = Array.isArray(response.data) ? response.data : [];

    const mapped: SourceMetadata[] = rawList.map((src) => ({
      source_id: src.source_id,
      name: src.source_name,
      source_name: src.source_name,
      source_type: src.source_type,
      description: src.description,
      default_authority: src.authority_level,
      authority_level: src.authority_level,
      enabled: src.availability,
      availability: src.availability ? 'online' : 'offline',
      record_count: (src.metadata?.doc_count as number) || (src.metadata?.ticket_count as number) || 0,
      status: src.availability ? 'healthy' : 'disabled',
      supported_topics: src.supported_topics || [],
      metadata: src.metadata || {},
    }));

    return {
      data: mapped,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    // Secondary fallback: GET /api/sources
    try {
      const fbResponse = await apiClient.get<SourceInfo[]>('/api/sources');
      const rawList = Array.isArray(fbResponse.data) ? fbResponse.data : [];
      const mapped: SourceMetadata[] = rawList.map((src) => ({
        ...src,
        source_name: src.name,
        authority_level: src.default_authority,
        availability: src.enabled && src.status === 'healthy' ? 'online' : src.status || 'offline',
        supported_topics: Array.isArray(src.metadata?.topics)
          ? (src.metadata.topics as string[])
          : [],
      }));

      return {
        data: mapped,
        error: null,
        isAvailable: true,
      };
    } catch {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Available sources endpoint unavailable (/api/intelligence/sources)';
      return {
        data: null,
        error: errorMessage,
        isAvailable: false,
      };
    }
  }
}

/**
 * 2. Execute Explainable Selection Plan & Query Pipeline:
 * Endpoint: POST /api/intelligence/plan
 * Real request payload: { question: string, config?: SelectionConfig }
 * Response: PlanResponse with real decision_trace from backend
 */
export async function getIntelligencePlan(
  payload: PlanRequest
): Promise<ServiceResponse<PlanResponse>> {
  try {
    const response = await apiClient.post<PlanResponse>('/api/intelligence/plan', {
      question: payload.question,
      config: payload.config || null,
    });

    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.message
        : 'Query orchestration service is currently unreachable (POST /api/intelligence/plan)';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 3. Standalone Source Selection
 * Calls POST /api/intelligence/plan and returns ranked sources
 */
export async function selectSourcesStandalone(
  payload: PlanRequest
): Promise<ServiceResponse<SourceRankResult[]>> {
  const result = await getIntelligencePlan(payload);
  if (result.isAvailable && result.data?.decision_trace) {
    return {
      data: result.data.decision_trace.ranked_sources,
      error: null,
      isAvailable: true,
    };
  }
  return {
    data: null,
    error: result.error,
    isAvailable: false,
  };
}
