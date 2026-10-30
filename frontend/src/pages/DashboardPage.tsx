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
  getSources,
  getRecentQueries,
  getRetrievalActivity,
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
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [recentQueries, setRecentQueries] = useState<QueryRunItem[]>([]);
  const [activityData, setActivityData] = useState<RetrievalActivityPoint[]>([]);
  
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState<boolean>(false);
  const [isLoadingSources, setIsLoadingSources] = useState<boolean>(false);

  // Health probe handler (called once on mount, and on manual retry)
  const probeSystemHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    const result = await getSystemHealth();
    if (result.isAvailable && result.data && (result.data.status === 'healthy' || result.data.status === 'ok')) {
      setHealth(result.data);
      setIsConnected(true);
    } else {
      setHealth(null);
      setIsConnected(false);
    }
    setIsCheckingHealth(false);
  }, []);

  // Fetch sources registry
  const loadSources = useCallback(async () => {
    setIsLoadingSources(true);
    const result = await getSources();
    if (result.isAvailable && result.data) {
      setSources(result.data);
    } else {
      setSources([]);
    }
    setIsLoadingSources(false);
  }, []);

  // Load telemetry & query history placeholders
  const loadTelemetry = useCallback(async () => {
    const [queriesRes, activityRes] = await Promise.all([
      getRecentQueries(),
      getRetrievalActivity(),
    ]);

    if (queriesRes.isAvailable && queriesRes.data) {
      setRecentQueries(queriesRes.data);
    }
    if (activityRes.isAvailable && activityRes.data) {
      setActivityData(activityRes.data);
    }
  }, []);

  // Initialize data once on mount without polling spam
  useEffect(() => {
    probeSystemHealth();
    loadSources();
    loadTelemetry();
  }, [probeSystemHealth, loadSources, loadTelemetry]);

  // Derived display values adhering strictly to no-fake-data rule
  const sourcesMetricValue = sources.length > 0 ? String(sources.length) : '--';
  const hasRealSources = sources.length > 0;

  return (
    <div className="dashboard-container">
      {/* ====================================================================
          A. Welcome Section
          ==================================================================== */}
      <section className="dashboard-welcome-section">
        <div className="welcome-text-group">
          <h2 className="welcome-title">Intelligence Overview</h2>
          <p className="welcome-subtitle">
            Monitor context selection, evidence quality and retrieval performance.
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
          B. Key Metric Cards (4 Cards with Honest Placeholders)
          ==================================================================== */}
      <section className="dashboard-metrics-grid">
        {/* 1. Total Queries */}
        <MetricCard
          label="Total Queries"
          value="--"
          icon={MessageSquareCode}
          description="Total questions orchestrated through context selection pipeline."
          isAwaitingData={true}
        />

        {/* 2. Sources Available */}
        <MetricCard
          label="Sources Available"
          value={sourcesMetricValue}
          icon={Database}
          description="Active grounding indices, documents, and API endpoints."
          isAwaitingData={!hasRealSources}
        />

        {/* 3. Evidence Retrieved */}
        <MetricCard
          label="Evidence Retrieved"
          value="--"
          icon={FileSearch}
          description="Contextual evidence chunks evaluated for query grounding."
          isAwaitingData={true}
        />

        {/* 4. Average Retrieval Budget Used */}
        <MetricCard
          label="Avg Retrieval Budget Used"
          value="--"
          icon={Gauge}
          description="Average context window token budget utilized per request."
          isAwaitingData={true}
        />
      </section>

      {/* ====================================================================
          C. Retrieval Activity Section & D. Source Overview Section
          ==================================================================== */}
      <section className="dashboard-charts-layout">
        <div className="chart-column-main">
          <ActivityChart data={activityData} isLoading={false} />
        </div>
        <div className="source-column-side">
          <SourceOverview sources={sources} isLoading={isLoadingSources} />
        </div>
      </section>

      {/* ====================================================================
          E. Recent Query Runs Table
          ==================================================================== */}
      <section className="dashboard-queries-section">
        <RecentQueries queries={recentQueries} isLoading={false} />
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
          lastQueryTime={null}
        />
      </section>
    </div>
  );
};

export default DashboardPage;
