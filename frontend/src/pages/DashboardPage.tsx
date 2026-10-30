import React, { useEffect, useState, useCallback } from 'react';
import {
  MessageSquare,
  Database,
  Layers,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileText,
  Ticket,
  MessagesSquare,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  fetchDashboardData,
  DashboardMetrics,
} from '../services/dashboardService';
import './DashboardPage.css';

export const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  // loading handled via data null check
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    
    const res = await fetchDashboardData();
    if (res.isAvailable && res.data) {
      setMetrics(res.data);
      setIsBackendConnected(true);
    } else {
      setMetrics(res.data);
      setIsBackendConnected(false);
    }
    
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalQueriesDisplay = metrics?.totalQueries !== null && metrics?.totalQueries !== undefined
    ? String(metrics.totalQueries)
    : '--';

  const avgSourcesDisplay = metrics?.avgResourcesSelected !== null && metrics?.avgResourcesSelected !== undefined
    ? `${metrics.avgResourcesSelected} per query`
    : '--';

  const avgLatencyDisplay = metrics?.avgResponseTimeMs !== null && metrics?.avgResponseTimeMs !== undefined
    ? `${metrics.avgResponseTimeMs} ms`
    : '--';

  const avgQualityDisplay = metrics?.avgEvidenceQualityPct !== null && metrics?.avgEvidenceQualityPct !== undefined
    ? `${metrics.avgEvidenceQualityPct}%`
    : '--';

  return (
    <div className="dash-container">
      {/* 1. Header Banner */}
      <section className="dash-hero">
        <div className="dash-hero-content">
          <div className="dash-status-pill-row">
            <span className={`dash-connection-pill ${isBackendConnected ? 'online' : 'offline'}`}>
              <span className={`status-indicator-dot ${isBackendConnected ? 'pulse' : ''}`} />
              <span>{isBackendConnected ? 'Engine Online' : 'Connecting to Engine'}</span>
            </span>

            <span className="dash-provider-pill">
              <Sparkles size={13} className="sparkle-icon" />
              <span>{metrics?.aiProviderStatus.name}: {metrics?.aiProviderStatus.statusLabel}</span>
            </span>
          </div>

          <h1 className="dash-title">System Overview</h1>
          <p className="dash-subtitle">
            EvidenRoute intelligently selects the most relevant resources, verifies evidence, and protects context capacity.
          </p>
        </div>

        <div className="dash-hero-action">
          <Link to="/query-workspace" className="dash-cta-btn">
            <MessageSquare size={16} />
            <span>Ask a Question</span>
          </Link>
        </div>
      </section>

      {/* 2. Primary Metrics Row */}
      <section className="dash-metrics-grid">
        <div className="dash-metric-card">
          <div className="dash-metric-header">
            <span className="dash-metric-label">Total Questions Asked</span>
            <div className="dash-metric-icon-wrap blue">
              <MessageSquare size={18} />
            </div>
          </div>
          <div className="dash-metric-value">{totalQueriesDisplay}</div>
          <div className="dash-metric-subtext">
            {metrics?.totalQueries ? 'Questions processed through context engine' : 'No queries processed yet'}
          </div>
        </div>

        <div className="dash-metric-card">
          <div className="dash-metric-header">
            <span className="dash-metric-label">Available Resources</span>
            <div className="dash-metric-icon-wrap emerald">
              <Database size={18} />
            </div>
          </div>
          <div className="dash-metric-value">{metrics?.availableResourcesCount ?? '--'}</div>
          <div className="dash-metric-subtext">
            {metrics?.resourceBreakdown.totalRecords ?? 0} total verified records connected
          </div>
        </div>

        <div className="dash-metric-card">
          <div className="dash-metric-header">
            <span className="dash-metric-label">Resources Selected</span>
            <div className="dash-metric-icon-wrap purple">
              <Layers size={18} />
            </div>
          </div>
          <div className="dash-metric-value">{avgSourcesDisplay}</div>
          <div className="dash-metric-subtext">
            Only relevant sources searched, irrelevant sources skipped
          </div>
        </div>

        <div className="dash-metric-card">
          <div className="dash-metric-header">
            <span className="dash-metric-label">Average Response Time</span>
            <div className="dash-metric-icon-wrap orange">
              <Clock size={18} />
            </div>
          </div>
          <div className="dash-metric-value">{avgLatencyDisplay}</div>
          <div className="dash-metric-subtext">
            Sub-millisecond local context routing
          </div>
        </div>

        <div className="dash-metric-card">
          <div className="dash-metric-header">
            <span className="dash-metric-label">Average Evidence Quality</span>
            <div className="dash-metric-icon-wrap emerald">
              <TrendingUp size={18} />
            </div>
          </div>
          <div className="dash-metric-value">{avgQualityDisplay}</div>
          <div className="dash-metric-subtext">
            Relevance, authority, freshness, and correctness
          </div>
        </div>
      </section>

      {/* 3. Resource Usage Summary & Activity Row */}
      <section className="dash-split-section">
        {/* Resource Usage Breakdown */}
        <div className="dash-panel">
          <div className="dash-panel-header">
            <div className="dash-panel-title-wrap">
              <Database size={18} className="text-accent" />
              <h2 className="dash-panel-title">Resource Usage Summary</h2>
            </div>
            <Link to="/resource-ranking" className="dash-panel-link">
              <span>View All</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          <div className="dash-resource-cards">
            <div className="dash-resource-card">
              <div className="dash-resource-top">
                <FileText size={18} className="text-blue" />
                <span className="dash-resource-count">{metrics?.resourceBreakdown.documentsCount ?? 0} Sources</span>
              </div>
              <div className="dash-resource-name">Official Documentation</div>
              <div className="dash-resource-desc">Technical specifications, API guides, and policies</div>
            </div>

            <div className="dash-resource-card">
              <div className="dash-resource-top">
                <Ticket size={18} className="text-orange" />
                <span className="dash-resource-count">{metrics?.resourceBreakdown.ticketsCount ?? 0} Sources</span>
              </div>
              <div className="dash-resource-name">Support Tickets</div>
              <div className="dash-resource-desc">Historical incident logs, bug reports, and resolutions</div>
            </div>

            <div className="dash-resource-card">
              <div className="dash-resource-top">
                <MessagesSquare size={18} className="text-purple" />
                <span className="dash-resource-count">{metrics?.resourceBreakdown.conversationsCount ?? 0} Sources</span>
              </div>
              <div className="dash-resource-name">Team Conversations</div>
              <div className="dash-resource-desc">Production war room chats and decision records</div>
            </div>
          </div>
        </div>

        {/* System Activity Timeline */}
        <div className="dash-panel">
          <div className="dash-panel-header">
            <div className="dash-panel-title-wrap">
              <Clock size={18} className="text-accent" />
              <h2 className="dash-panel-title">Recent System Activity</h2>
            </div>
          </div>

          <div className="dash-activity-list">
            {metrics?.recentActivity && metrics.recentActivity.length > 0 ? (
              metrics.recentActivity.map((act) => (
                <div key={act.id} className="dash-activity-item">
                  <div className="dash-activity-bullet" />
                  <div className="dash-activity-body">
                    <div className="dash-activity-top">
                      <span className="dash-activity-title">{act.title}</span>
                      <span className="dash-activity-time">{act.timestamp}</span>
                    </div>
                    <div className="dash-activity-desc">{act.description}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="dash-empty-state">No recent activity logged yet.</div>
            )}
          </div>
        </div>
      </section>

      {/* 4. Recent Queries Table */}
      <section className="dash-panel full-width">
        <div className="dash-panel-header">
          <div className="dash-panel-title-wrap">
            <MessageSquare size={18} className="text-accent" />
            <h2 className="dash-panel-title">Recent Questions</h2>
          </div>
          <Link to="/query-workspace" className="dash-panel-link">
            <span>Open Chatbot</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        {metrics?.recentQueries && metrics.recentQueries.length > 0 ? (
          <div className="dash-table-wrap">
            <table className="dash-table">
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Outcome</th>
                  <th>Resources Used</th>
                  <th>Context Consumed</th>
                  <th>Time</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {metrics.recentQueries.map((q) => (
                  <tr key={q.id}>
                    <td className="font-medium text-primary">
                      <div className="dash-q-text" title={q.question}>
                        {q.question}
                      </div>
                    </td>
                    <td>
                      <span className={`dash-badge ${q.outcome === 'ANSWER' ? 'success' : q.outcome === 'ABSTAIN' ? 'warning' : 'info'}`}>
                        {q.outcome === 'ANSWER' ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                        <span>{q.outcomeLabel}</span>
                      </span>
                    </td>
                    <td>{q.evidenceCount} resource(s)</td>
                    <td>{q.tokensUsed} tokens</td>
                    <td className="text-muted">{q.timeAgo}</td>
                    <td>
                      <Link to="/evidence-explorer" className="dash-table-action-link">
                        Explore Evidence
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="dash-empty-queries">
            <MessageSquare size={32} className="text-muted" />
            <p className="dash-empty-title">No questions asked yet</p>
            <p className="dash-empty-desc">
              Ask your first question in the Query Workspace to see context selection and evidence ranking in action.
            </p>
            <Link to="/query-workspace" className="dash-empty-btn">
              Ask a Question Now
            </Link>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
