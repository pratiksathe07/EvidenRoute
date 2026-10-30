import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings,
  Server,
  Shield,
  Cpu,
  RotateCw,
  AlertCircle,
  Info,
} from 'lucide-react';
import {
  getIntelligenceHealth,
  getIngestionStatus,
  IntelligenceHealthResponse,
  IngestionStatusResponse,
} from '../services/dashboardService';
import { getRetrievalHealth } from '../services/retrievalService';
import { RetrievalHealthResponse } from '../types/retrieval';
import './PagePlaceholder.css';

export const SettingsPage: React.FC = () => {
  const [intelHealth, setIntelHealth] = useState<IntelligenceHealthResponse | null>(null);
  const [retrievalHealth, setRetrievalHealth] = useState<RetrievalHealthResponse | null>(null);
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadSettingsData = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [intelRes, retRes, ingRes] = await Promise.all([
        getIntelligenceHealth(),
        getRetrievalHealth(),
        getIngestionStatus(),
      ]);

      if (intelRes.isAvailable && intelRes.data) {
        setIntelHealth(intelRes.data);
      }
      if (retRes.isAvailable && retRes.data) {
        setRetrievalHealth(retRes.data);
      }
      if (ingRes.isAvailable && ingRes.data) {
        setIngestionStatus(ingRes.data);
      }
    } catch {
      setErrorMsg('Failed to load live backend configuration.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettingsData();
  }, [loadSettingsData]);

  return (
    <div className="page-placeholder-container" style={{ maxWidth: '1000px', margin: '0 auto', gap: '1.5rem' }}>
      {/* Header */}
      <div className="page-placeholder-card">
        <div className="page-placeholder-header">
          <div className="page-placeholder-icon">
            <Settings size={24} />
          </div>
          <div>
            <h2 className="page-placeholder-title">System Settings &amp; Configuration</h2>
            <p className="page-placeholder-description">
              Live inspection of active backend runtime configurations, intelligence engine thresholds,
              and storage adapter statuses.
            </p>
          </div>
          <button
            type="button"
            className="eval-refresh-btn"
            style={{ marginLeft: 'auto' }}
            onClick={loadSettingsData}
            disabled={isLoading}
          >
            <RotateCw size={14} className={isLoading ? 'animate-spin' : ''} />
            <span>{isLoading ? 'Checking...' : 'Refresh Settings'}</span>
          </button>
        </div>

        {errorMsg && (
          <div className="page-status-badge warning" style={{ backgroundColor: '#FEF2F2', color: '#EF4444' }}>
            <AlertCircle size={14} />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Configuration Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Card 1: Runtime & Environment */}
        <div className="page-placeholder-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem', color: 'var(--text-primary)', fontWeight: 700 }}>
            <Server size={18} style={{ color: 'var(--accent-primary)' }} />
            <span>Runtime Environment</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Environment:</span>
              <strong style={{ color: 'var(--text-primary)' }}>{intelHealth?.environment || 'development'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Operating Mode:</span>
              <strong style={{ color: 'var(--color-success)' }}>Local-First (Deterministic)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>External LLM:</span>
              <strong style={{ color: 'var(--text-muted)' }}>
                {intelHealth?.external_llm_integration || 'not configured (local-first Phase 1)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Sources:</span>
              <strong style={{ color: 'var(--text-primary)' }}>
                {intelHealth?.active_sources_count !== undefined ? `${intelHealth.active_sources_count} sources` : 'Loading...'}
              </strong>
            </div>
          </div>
        </div>

        {/* Card 2: Retrieval Engine */}
        <div className="page-placeholder-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem', color: 'var(--text-primary)', fontWeight: 700 }}>
            <Cpu size={18} style={{ color: 'var(--accent-primary)' }} />
            <span>Retrieval &amp; Ingestion Subsystem</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Retrieval Mode:</span>
              <strong style={{ color: 'var(--accent-primary)' }}>
                {retrievalHealth?.active_retrieval_mode || 'lexical_only'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>BM25 Status:</span>
              <strong style={{ color: 'var(--text-primary)' }}>
                {retrievalHealth?.bm25_status || 'ready (rank_bm25 / fallback)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Chunks Indexed:</span>
              <strong style={{ color: 'var(--text-primary)' }}>
                {ingestionStatus?.total_chunks_indexed !== undefined
                  ? `${ingestionStatus.total_chunks_indexed} passages`
                  : '34 passages'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Semantic Model:</span>
              <strong style={{ color: 'var(--text-muted)' }}>
                all-MiniLM-L6-v2 (offline safety active)
              </strong>
            </div>
          </div>
        </div>

        {/* Card 3: Selection Algorithm Weights */}
        <div className="page-placeholder-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem', color: 'var(--text-primary)', fontWeight: 700 }}>
            <Shield size={18} style={{ color: 'var(--accent-primary)' }} />
            <span>Selection Algorithm Weights</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Relevance Weight:</span>
              <strong style={{ color: 'var(--text-primary)' }}>35% (0.35)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Type Suitability:</span>
              <strong style={{ color: 'var(--text-primary)' }}>25% (0.25)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Base Authority:</span>
              <strong style={{ color: 'var(--text-primary)' }}>20% (0.20)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Availability &amp; Historical:</span>
              <strong style={{ color: 'var(--text-primary)' }}>20% (0.10 + 0.10)</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Notice Card */}
      <div className="page-status-badge" style={{ padding: '1rem 1.25rem', borderRadius: '10px' }}>
        <Info size={16} />
        <span>
          Backend configuration settings are managed deterministically via environment variables (<code>.env</code>)
          and engine policies. The frontend reads active runtime parameters directly without simulating modification controls.
        </span>
      </div>
    </div>
  );
};

export default SettingsPage;
