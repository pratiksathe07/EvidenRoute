import apiClient from './api';
import {
  RetrieveRequest,
  RetrieveResponse,
  RetrievalHealthResponse,
} from '../types/retrieval';
import { ServiceResponse } from './dashboardService';

/**
 * 1. Execute Intelligent Context Selection, Retrieval & Evidence Evaluation
 * Endpoint: POST /api/intelligence/retrieve
 * Real backend response: RetrieveResponse
 */
export async function retrieveEvidence(
  request: RetrieveRequest
): Promise<ServiceResponse<RetrieveResponse>> {
  try {
    const response = await apiClient.post<RetrieveResponse>(
      '/api/intelligence/retrieve',
      {
        question: request.question,
        top_k: request.top_k || 10,
        selection_config: request.selection_config ?? null,
        retrieval_config: request.retrieval_config ?? null,
      }
    );

    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.message
        : 'Evidence retrieval service unreachable (POST /api/intelligence/retrieve)';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}

/**
 * 2. Probe Retrieval Subsystem Diagnostics
 * Endpoint: GET /api/intelligence/retrieval-health
 */
export async function getRetrievalHealth(): Promise<ServiceResponse<RetrievalHealthResponse>> {
  try {
    const response = await apiClient.get<RetrievalHealthResponse>(
      '/api/intelligence/retrieval-health'
    );
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error
        ? err.message
        : 'Retrieval diagnostic endpoint unavailable (/api/intelligence/retrieval-health)';
    return {
      data: null,
      error: errorMessage,
      isAvailable: false,
    };
  }
}
