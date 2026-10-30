import React, { useState } from 'react';
import {
  Database,
  FileText,
  Webhook,
  Ticket,
  MessageSquare,
  Shield,
  ChevronDown,
  ChevronUp,
  Radio,
  Tag,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';
import { SourceMetadata } from '../../types/sourceSelection';
import './AvailableSourcesPanel.css';

interface AvailableSourcesPanelProps {
  sources: SourceMetadata[];
  isLoading: boolean;
}

export const AvailableSourcesPanel: React.FC<AvailableSourcesPanelProps> = ({
  sources,
  isLoading,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null);

  const getSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'documentation':
        return <FileText size={16} />;
      case 'apis':
      case 'api':
      case 'databases':
        return <Webhook size={16} />;
      case 'tickets':
      case 'incident_reports':
        return <Ticket size={16} />;
      case 'conversations':
      case 'chat_logs':
        return <MessageSquare size={16} />;
      default:
        return <Database size={16} />;
    }
  };

  const getSourceTypeBadgeClass = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'documentation':
        return 'type-blue';
      case 'apis':
      case 'api':
      case 'databases':
        return 'type-emerald';
      case 'tickets':
      case 'incident_reports':
        return 'type-orange';
      case 'conversations':
      case 'chat_logs':
        return 'type-purple';
      default:
        return 'type-neutral';
    }
  };

  const isSourceOnline = (availability: string | boolean) => {
    if (typeof availability === 'boolean') return availability;
    return availability.toLowerCase() === 'online' || availability.toLowerCase() === 'available';
  };

  const toggleSourceDetail = (id: string) => {
    setExpandedSourceId((prev) => (prev === id ? null : id));
  };

  const hasSources = sources && sources.length > 0;

  return (
    <div className="available-sources-card">
      <div className="available-sources-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="header-title-wrap">
          <div className="header-icon-container">
            <Database size={16} />
          </div>
          <div>
            <h3 className="available-sources-title">Available Context Sources</h3>
            <p className="available-sources-subtitle">
              Grounding repositories returned by <code>GET /api/sources</code>.
            </p>
          </div>
        </div>

        <div className="header-actions-wrap">
          <span className="source-count-pill">
            {hasSources ? `${sources.length} Ingested` : '0 Ingested'}
          </span>
          <button
            type="button"
            className="toggle-collapse-btn"
            aria-label={isExpanded ? 'Collapse panel' : 'Expand panel'}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="available-sources-content">
          {isLoading ? (
            <div className="sources-loading-box">
              <span className="sources-spinner" />
              <p>Fetching active source registry from <code>/api/sources</code>...</p>
            </div>
          ) : hasSources ? (
            <div className="sources-grid">
              {sources.map((src) => {
                const online = isSourceOnline(src.availability ?? (src.enabled ? 'online' : 'offline'));
                const isDetailOpen = expandedSourceId === src.source_id;
                const displayName = src.name || src.source_name || src.source_id;
                const authScore = src.default_authority ?? (typeof src.authority_level === 'number' ? src.authority_level : 0.5);

                return (
                  <div
                    key={src.source_id}
                    className={`source-card-item ${online ? 'source-online' : 'source-offline'}`}
                  >
                    <div className="source-card-main">
                      <div className="source-card-top">
                        <div className={`source-type-pill ${getSourceTypeBadgeClass(src.source_type)}`}>
                          {getSourceIcon(src.source_type)}
                          <span>{src.source_type}</span>
                        </div>

                        {/* Availability Status */}
                        <span className={`source-status-badge ${online ? 'online' : 'offline'}`}>
                          {online ? (
                            <>
                              <Radio size={10} className="status-radio-icon" />
                              <span>{String(src.status || src.availability || 'Online')}</span>
                            </>
                          ) : (
                            <>
                              <AlertTriangle size={11} />
                              <span>Offline</span>
                            </>
                          )}
                        </span>
                      </div>

                      <h4 className="source-name">{displayName}</h4>
                      <span className="source-identifier-tag">ID: {src.source_id}</span>

                      {src.description && (
                        <p className="source-description">{src.description}</p>
                      )}

                      {/* Meta Attributes: Authority & Records */}
                      <div className="source-meta-row">
                        <div className="meta-chip" title="Base Authority Score">
                          <Shield size={12} />
                          <span>Authority: {authScore.toFixed(2)}</span>
                        </div>
                        {src.record_count !== undefined && (
                          <div className="meta-chip" title="Ingested Chunks / Records">
                            <Database size={12} />
                            <span>{src.record_count} Records</span>
                          </div>
                        )}
                      </div>

                      {/* Supported Topics Tags */}
                      {src.supported_topics && src.supported_topics.length > 0 && (
                        <div className="supported-topics-container">
                          <span className="topics-heading">
                            <Tag size={11} /> Topics:
                          </span>
                          <div className="topics-chips-wrap">
                            {src.supported_topics.map((topic, i) => (
                              <span key={i} className="topic-chip">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <button
                        type="button"
                        className="btn-toggle-details"
                        onClick={() => toggleSourceDetail(src.source_id)}
                      >
                        <span>{isDetailOpen ? 'Hide Metadata Schema' : 'Inspect Metadata'}</span>
                        {isDetailOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                      </button>

                      {isDetailOpen && (
                        <div className="source-technical-details">
                          <div className="tech-field">
                            <span className="tech-label">Source ID:</span>
                            <code>{src.source_id}</code>
                          </div>
                          <div className="tech-field">
                            <span className="tech-label">Operational Status:</span>
                            <span>{src.status || 'healthy'}</span>
                          </div>
                          <div className="tech-field">
                            <span className="tech-label">Enabled:</span>
                            <span>{src.enabled !== false ? 'True' : 'False'}</span>
                          </div>
                          {src.metadata && (
                            <div className="tech-meta-block">
                              <span className="tech-label">Extended Metadata:</span>
                              <pre className="tech-json">
                                {JSON.stringify(src.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Honest Empty State */
            <div className="sources-empty-state">
              <div className="sources-empty-icon">
                <Database size={22} />
              </div>
              <h4 className="sources-empty-title">Awaiting Source Ingestion</h4>
              <p className="sources-empty-text">
                No connected sources returned by <code>GET /api/sources</code>. When sources are registered on the backend, they will appear here with authority scores and status.
              </p>
              <div className="sources-empty-hint">
                <HelpCircle size={14} />
                <span>Backend endpoint: <code>GET /api/sources</code></span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
