import React from 'react';
import {
  Server,
  Cpu,
  RefreshCw,
  Clock,
  Radio,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { SystemHealthResponse } from '../../types/dashboard';
import './EngineStatus.css';

interface EngineStatusProps {
  health: SystemHealthResponse | null;
  isConnected: boolean;
  isChecking: boolean;
  onRefresh: () => void;
  lastQueryTime?: string | null;
}

export const EngineStatus: React.FC<EngineStatusProps> = ({
  health,
  isConnected,
  isChecking,
  onRefresh,
  lastQueryTime = null,
}) => {
  const isHealthy = isConnected && (health?.status === 'healthy' || health?.status === 'ok');

  return (
    <div className="engine-status-card">
      <div className="engine-status-header">
        <div>
          <h3 className="engine-status-title">System Activity & Engine Status</h3>
          <p className="engine-status-subtitle">
            Monitors health probes, vector retriever availability, and orchestration cluster states.
          </p>
        </div>
        <button
          type="button"
          className="engine-refresh-btn"
          onClick={onRefresh}
          disabled={isChecking}
          title="Test backend connection"
        >
          <RefreshCw size={14} className={isChecking ? 'spinning' : ''} />
          <span>{isChecking ? 'Checking...' : 'Check Connection'}</span>
        </button>
      </div>

      <div className="engine-status-grid">
        {/* 1. Backend Connectivity */}
        <div className="status-metric-box">
          <div className="status-metric-icon-wrap">
            <Server size={18} />
          </div>
          <div className="status-metric-info">
            <span className="status-metric-label">Backend Connectivity</span>
            <div className="status-metric-value-row">
              {isHealthy ? (
                <span className="status-pill connected">
                  <CheckCircle2 size={13} />
                  <span>Connected (200 OK)</span>
                </span>
              ) : (
                <span className="status-pill disconnected">
                  <AlertCircle size={13} />
                  <span>Not Connected</span>
                </span>
              )}
            </div>
            <p className="status-metric-sub">
              Probe target:{' '}
              <code>/api/health</code>
            </p>
          </div>
        </div>

        {/* 2. Retrieval Engine Core */}
        <div className="status-metric-box">
          <div className="status-metric-icon-wrap">
            <Cpu size={18} />
          </div>
          <div className="status-metric-info">
            <span className="status-metric-label">Retrieval Engine Core</span>
            <div className="status-metric-value-row">
              {isHealthy ? (
                <span className="status-pill connected">
                  <Radio size={13} />
                  <span>{health?.engine || 'Engine Ready'}</span>
                </span>
              ) : (
                <span className="status-pill pending">
                  <Radio size={13} />
                  <span>Awaiting Backend Service</span>
                </span>
              )}
            </div>
            <p className="status-metric-sub">
              {isHealthy ? `v${health?.version || '1.0.0'} online` : 'Requires backend orchestrator'}
            </p>
          </div>
        </div>

        {/* 3. Last Successful Query */}
        <div className="status-metric-box">
          <div className="status-metric-icon-wrap">
            <Clock size={18} />
          </div>
          <div className="status-metric-info">
            <span className="status-metric-label">Last Successful Query</span>
            <div className="status-metric-value-row">
              <span className="status-metric-text">
                {lastQueryTime || 'None yet (Awaiting first query)'}
              </span>
            </div>
            <p className="status-metric-sub">Updated on query completion</p>
          </div>
        </div>
      </div>

      {/* Honest Backend Integration Banner */}
      {!isHealthy && (
        <div className="backend-guidance-banner">
          <HelpCircle size={16} className="guidance-icon" />
          <p className="guidance-text">
            <strong>Backend Integration Notice:</strong> The frontend is running in isolated client mode. To connect the real engine, start the Python/FastAPI backend on port <code>8000</code> exposing <code>GET /api/health</code>, then click &ldquo;Check Connection&rdquo;.
          </p>
        </div>
      )}
    </div>
  );
};
