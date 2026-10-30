import React, { useEffect, useState, useCallback } from 'react';
import {
  MessageSquareCode,
  Database,
  FileSearch,
  Gauge,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { MetricCard } from '../components/dashboard/MetricCard';
import { ActivityChart } from '../components/dashboard/ActivityChart';
import { SourceOverview } from '../components/dashboard/SourceOverview';
import { RecentQueries } from '../components/dashboard/RecentQueries';
import { EngineStatus } from '../components/dashboard/EngineStatus';
import {
  getSystemHealth,
  getIntelligenceHealth,
  getIngestionStatus,
  getSources,
  getRecentQueries,
  buildActivityFromQueries,
  IntelligenceHealthResponse,
  IngestionStatusResponse,
} from '../services/dashboardService';
import {
  SystemHealthResponse,
  SourceItem,
  QueryRunItem,
  RetrievalActivityPoint,
} from '../types/dashboard';
import './DashboardPage.css';

export const DashboardPage: React.FC = () => {
  // Asynchronous Dashboard State
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [intelHealth, setIntelHealth] = useState<IntelligenceHealthResponse | null>(null);
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatusResponse | null>(null);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [recentQueries, setRecentQueries] = useState<QueryRunItem[]>([]);
  const [activityData, setActivityData] = useState<RetrievalActivityPoint[]>([]);

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCheckingHealth, setIsCheckingHealth] = useState<boolean>(false);

  // Health probe handler
  const probeSystemHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    const [healthRes, intelRes] = await Promise.all([
      getSystemHealth(),
      getIntelligenceHealth(),
    ]);

    if (
      healthRes.isAvailable &&
      healthRes.data &&
      (healthRes.data.status === 'healthy' || healthRes.data.status === 'ok')
    ) {
      setHealth(healthRes.data);
      setIsConnected(true);
    } else {
      setHealth(null);
      setIsConnected(false);
    }

    if (intelRes.isAvailable && intelRes.data) {
      setIntelHealth(intelRes.data);
    }

    setIsCheckingHealth(false);
  }, []);

  // Fetch all dashboard data from real backend endpoints
  const loadDashboardData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [sourcesRes, queriesRes, ingestionRes] = await Promise.all([
        getSources(),
        getRecentQueries(),
        getIngestionStatus(),
      ]);

      if (sourcesRes.isAvailable && sourcesRes.data) {
        setSources(sourcesRes.data);
      } else {
        setSources([]);
      }

      if (queriesRes.isAvailable && queriesRes.data) {
        setRecentQueries(queriesRes.data);
        setActivityData(buildActivityFromQueries(queriesRes.data));
      } else {
        setRecentQueries([]);
        setActivityData([]);
      }

      if (ingestionRes.isAvailable && ingestionRes.data) {
        setIngestionStatus(ingestionRes.data);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    probeSystemHealth();
    loadDashboardData();
  }, [probeSystemHealth, loadDashboardData]);

  // Real metric values derived strictly from backend
  const totalQueriesValue = isLoading
    ? '...'
    : isConnected
    ? String(recentQueries.length)
    : '--';

  const sourcesValue = isLoading
    ? '...'
    : isConnected
    ? intelHealth?.active_sources_count !== undefined
      ? String(intelHealth.active_sources_count)
      : String(sources.length)
    : '--';

  const chunksIndexedValue = isLoading
    ? '...'
    : isConnected && ingestionStatus?.total_chunks_indexed !== undefined
    ? String(ingestionStatus.total_chunks_indexed)
    : '--';

  // Calculate actual average tokens consumed across real queries in database
  const avgTokensValue = (() => {
    if (isLoading) return '...';
    if (!isConnected || recentQueries.length === 0) return '--';
    const totalTokens = recentQueries.reduce((acc, q) => {
      const match = q.budgetUsed?.match(/(\d+)\s*tokens/);
      return acc + (match ? parseInt(match[1], 10) : 0);
    }, 0);
    return `${Math.round(totalTokens / recentQueries.length)} tokens`;
  })();

  return (
    <div className="dashboard-container">
      {/* ====================================================================
          A. Welcome Section
          ==================================================================== */}
      <section className="dashboard-welcome-section">
        <div className="welcome-text-group">
          <h2 className="welcome-title">Intelligence Overview</h2>
          <p className="welcome-subtitle">
            Live telemetry monitoring context selection, evidence grounding, and retrieval performance.
          </p>
        </div>

        {/* Small Real-time System Status Indicator */}
        <div
          className={`welcome-status-badge ${isConnected ? 'status-connected' : 'status-pending'}`}
          title={
            isConnected
              ? 'Backend cluster probed successfully via /api/health'
              : 'Backend not detected at http://localhost:8000/api/health'
          }
        >
          <span className={`status-indicator-dot ${isConnected ? 'dot-active' : 'dot-pending'}`} />
          {isConnected ? (
            <>
              <CheckCircle2 size={13} />
              <span>Orchestrator Online</span>
            </>
          ) : (
            <>
              <AlertCircle size={13} />
              <span>Awaiting Backend Connection</span>
            </>
          )}
        </div>
      </section>

      {/* ====================================================================
          B. Key Metric Cards (Real Values from Backend)
          ==================================================================== */}
      <section className="dashboard-metrics-grid">
        {/* 1. Total Queries Recorded */}
        <MetricCard
          label="Total Queries Recorded"
          value={totalQueriesValue}
          icon={MessageSquareCode}
          description="Total questions recorded in the database query audit log."
          isAwaitingData={!isConnected}
        />

        {/* 2. Sources Available */}
        <MetricCard
          label="Sources Available"
          value={sourcesValue}
          icon={Database}
          description="Active grounding indices, documents, and API adapters."
          isAwaitingData={!isConnected}
        />

        {/* 3. Evidence Chunks Indexed */}
        <MetricCard
          label="Evidence Chunks Indexed"
          value={chunksIndexedValue}
          icon={FileSearch}
          description="Contextual evidence chunks indexed and available for retrieval."
          isAwaitingData={!isConnected}
        />

        {/* 4. Average Token Expenditure */}
        <MetricCard
          label="Avg Context Tokens"
          value={avgTokensValue}
          icon={Gauge}
          description="Average context window token budget consumed per recorded query."
          isAwaitingData={!isConnected || recentQueries.length === 0}
        />
      </section>

      {/* ====================================================================
          C. Retrieval Activity Section & D. Source Overview Section
          ==================================================================== */}
      <section className="dashboard-charts-layout">
        <div className="chart-column-main">
          <ActivityChart data={activityData} isLoading={isLoading} />
        </div>
        <div className="source-column-side">
          <SourceOverview sources={sources} isLoading={isLoading} />
        </div>
      </section>

      {/* ====================================================================
          E. Recent Query Runs Table (Real DB Records)
          ==================================================================== */}
      <section className="dashboard-queries-section">
        <RecentQueries queries={recentQueries} isLoading={isLoading} />
      </section>

      {/* ====================================================================
          F. System Activity / Engine Status
          ==================================================================== */}
      <section className="dashboard-engine-section">
        <EngineStatus
          health={health}
          isConnected={isConnected}
          isChecking={isCheckingHealth}
          onRefresh={probeSystemHealth}
          lastQueryTime={recentQueries[0]?.timestamp || null}
        />
      </section>
    </div>
  );
};

export default DashboardPage;
