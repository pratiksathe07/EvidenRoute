import React from 'react';
import {
  FileText,
  Webhook,
  Ticket,
  MessageSquare,
  AlertCircle,
  Database,
  CheckCircle2,
} from 'lucide-react';
import { SourceItem } from '../../types/dashboard';
import './SourceOverview.css';

interface SourceOverviewProps {
  sources: SourceItem[];
  isLoading?: boolean;
}

// Illustrative context categories as defined in EvidenRoute architecture
const SOURCE_CATEGORIES = [
  {
    id: 'documents',
    name: 'Documents',
    description: 'Policies, guides, PDFs & technical specs',
    icon: FileText,
    badgeClass: 'badge-blue',
  },
  {
    id: 'apis',
    name: 'APIs & Databases',
    description: 'Real-time REST endpoints & database tables',
    icon: Webhook,
    badgeClass: 'badge-emerald',
  },
  {
    id: 'tickets',
    name: 'Tickets',
    description: 'Support cases, Jira issues & incident logs',
    icon: Ticket,
    badgeClass: 'badge-orange',
  },
  {
    id: 'conversations',
    name: 'Conversations',
    description: 'Engineering channels, chats & customer logs',
    icon: MessageSquare,
    badgeClass: 'badge-purple',
  },
];

export const SourceOverview: React.FC<SourceOverviewProps> = ({
  sources,
  isLoading = false,
}) => {
  const hasConnectedSources = sources && sources.length > 0;

  return (
    <div className="source-overview-card">
      <div className="source-overview-header">
        <div>
          <h3 className="source-overview-title">Context Source Overview</h3>
          <p className="source-overview-subtitle">
            Grounding repositories and live indices available for selective retrieval orchestration.
          </p>
        </div>
        <div className="source-counter-badge">
          <Database size={13} />
          <span>{hasConnectedSources ? `${sources.length} Connected` : '0 Active'}</span>
        </div>
      </div>

      {isLoading ? (
        <div className="source-loading-state">
          <span className="source-spinner" />
          <p>Querying connected source registry...</p>
        </div>
      ) : hasConnectedSources ? (
        /* Connected Sources List */
        <div className="connected-sources-list">
          {sources.map((src) => (
            <div key={src.id} className="source-item-card">
              <div className="source-item-left">
                <div className="source-item-avatar">
                  <Database size={16} />
                </div>
                <div>
                  <h4 className="source-item-name">{src.name}</h4>
                  <p className="source-item-category">{src.category}</p>
                </div>
              </div>
              <div className="source-item-right">
                <span className="source-status-badge connected">
                  <CheckCircle2 size={12} />
                  <span>Connected</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State with Illustrative Architecture Categories */
        <div className="source-empty-container">
          <div className="source-categories-grid">
            {SOURCE_CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <div key={cat.id} className="category-preview-card">
                  <div className="category-header">
                    <div className={`category-icon-wrapper ${cat.badgeClass}`}>
                      <Icon size={18} />
                    </div>
                    <span className="category-status-tag">Not Connected</span>
                  </div>
                  <h4 className="category-title">{cat.name}</h4>
                  <p className="category-desc">{cat.description}</p>
                </div>
              );
            })}
          </div>

          <div className="source-integration-note">
            <AlertCircle size={16} className="note-icon" />
            <div className="note-text">
              <span className="note-title">Awaiting Source Ingestion:</span>
              <p>
                No active source connections detected. Connected data feeds will appear here after integration with{' '}
                <code>GET /api/sources</code> or when configured in the Source Selection workspace.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
