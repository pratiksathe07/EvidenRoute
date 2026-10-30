import apiClient from './api';
import { ServiceResponse } from './dashboardService';

export interface BenchmarkMetrics {
  mode: string;
  total_queries: number;
  average_precision: number;
  average_recall: number;
  average_relevance: number;
  source_selection_accuracy: number;
  contradiction_accuracy: number;
  sufficiency_accuracy: number;
  average_passages_retrieved: number;
  average_latency_ms: number;
  budget_calls_consumed: number;
  budget_tokens_consumed: number;
  irrelevant_evidence_reduction_pct: number;
}

export interface BaselineComparisonReport {
  baseline_metrics: BenchmarkMetrics;
  evidenroute_metrics: BenchmarkMetrics;
  improvements: {
    precision_gain_pct: number;
    call_budget_reduction_pct: number;
    irrelevant_passages_filtered_pct: number;
    decision_accuracy_gain: number;
  };
  evaluation_timestamp: string;
}

export interface StressTestSummary {
  total_scenarios: number;
  passed_scenarios: number;
  overall_pass_rate?: number;
  average_duration_ms?: number;
}

/**
 * Fetches the real side-by-side benchmark comparison between
 * Naive Baseline (broadcast all sources) vs EvidenRoute (Intelligent Pre-Routing).
 */
export async function getBaselineComparison(): Promise<ServiceResponse<BaselineComparisonReport>> {
  try {
    const response = await apiClient.get<BaselineComparisonReport>(
      '/api/intelligence/benchmark/baseline-comparison'
    );
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const msg =
      err instanceof Error
        ? err.message
        : 'Failed to fetch baseline evaluation comparison from /api/intelligence/benchmark/baseline-comparison';
    return {
      data: null,
      error: msg,
      isAvailable: false,
    };
  }
}

/**
 * Triggers or inspects the 14-scenario stress test results.
 */
export async function getStressTestReport(): Promise<ServiceResponse<StressTestSummary>> {
  try {
    const response = await apiClient.post<StressTestSummary>(
      '/api/intelligence/stress-test'
    );
    return {
      data: response.data,
      error: null,
      isAvailable: true,
    };
  } catch (err: unknown) {
    const msg =
      err instanceof Error
        ? err.message
        : 'Failed to execute stress test endpoint (/api/intelligence/stress-test)';
    return {
      data: null,
      error: msg,
      isAvailable: false,
    };
  }
}

