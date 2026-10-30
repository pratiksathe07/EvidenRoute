import { LucideIcon } from 'lucide-react';

/**
 * Backend System Health Response (GET /api/health)
 */
export interface SystemHealthResponse {
  status: 'ok' | 'healthy' | 'degraded' | 'offline' | string;
  engine?: string;
  version?: string;
  uptime?: number;
  timestamp?: string;
}

/**
 * Context Source Item (GET /api/sources)
 */
export interface SourceItem {
  id: string;
  name: string;
  category: 'documents' | 'apis' | 'tickets' | 'conversations' | string;
  status: 'connected' | 'syncing' | 'disconnected' | 'pending';
  itemCount?: number;
  lastSynced?: string;
  description?: string;
}

export interface SourcesResponse {
  sources: SourceItem[];
  totalSources?: number;
}

/**
 * Evaluation Metrics (GET /api/evaluate/results)
 */
export interface EvaluationResult {
  precision?: number;
  recall?: number;
  faithfulness?: number;
  avgLatencyMs?: number;
  totalEvaluated?: number;
}

/**
 * Single Query Run record for Recent Queries table
 */
export interface QueryRunItem {
  id: string;
  query: string;
  selectedSources: string[];
  evidenceCount: number;
  budgetUsed: string;
  answerStatus: 'verified' | 'reliable' | 'partial' | 'failed';
  timestamp: string;
}

/**
 * Data point for Retrieval Activity chart
 */
export interface RetrievalActivityPoint {
  time: string;
  queries: number;
  evidence: number;
  budgetTokens: number;
}

/**
 * Metric Card configuration interface
 */
export interface MetricCardData {
  id: string;
  label: string;
  value: string;
  icon: LucideIcon;
  description: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  isAwaitingData: boolean;
}

/**
 * Overall state for Dashboard
 */
export interface DashboardDataState {
  health: SystemHealthResponse | null;
  sources: SourceItem[];
  evaluation: EvaluationResult | null;
  recentQueries: QueryRunItem[];
  activityData: RetrievalActivityPoint[];
  isConnected: boolean;
  isCheckingHealth: boolean;
  sourcesLoading: boolean;
  error: string | null;
}
