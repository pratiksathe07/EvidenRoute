import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Database,
  ChevronDown,
  ChevronUp,
  FileText,
  MessageSquare,
  Ticket,
} from 'lucide-react';
import { SourceMetadata } from '../../types/sourceSelection';
import './SourceResultsPanel.css';

interface SourceResultsPanelProps {
  selectedSources: string[];
  skippedSources: string[];
  allAvailableSources?: SourceMetadata[];
}

export const SourceResultsPanel: React.FC<SourceResultsPanelProps> = ({
  selectedSources,
  skippedSources,
  allAvailableSources = [],
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Helper lookup for rich metadata
  const sourceMap = new Map<string, { name: string; type: string; authority: number }>();
  for (const s of allAvailableSources) {
    sourceMap.set(s.source_id, {
      name: s.source_name || s.name || s.source_id,
      type: s.source_type || 'documents',
      authority: s.default_authority ?? (typeof s.authority_level === 'number' ? s.authority_level : 0.8),
    });
  }

  const getSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'document':
        return <FileText size={14} />;
      case 'conversations':
      case 'conversation':
        return <MessageSquare size={14} />;
      case 'tickets':
      case 'ticket':
        return <Ticket size={14} />;
      default:
        return <Database size={14} />;
    }
  };

  const totalSources = selectedSources.length + skippedSources.length;
  const prunedPercent = totalSources > 0 ? Math.round((skippedSources.length / totalSources) * 100) : 0;

  return (
    <div className="qw-sources-card">
      <div className="qw-sources-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="qw-sources-title-wrap">
          <div className="qw-sources-icon">
            <Database size={16} />
          </div>
          <div>
            <h4 className="qw-sources-title">Context Sources Routing (Pre-Retrieval)</h4>
            <p className="qw-sources-subtitle">
              Grounding repositories evaluated before executing vector or lexical queries.
            </p>
          </div>
        </div>

        <div className="qw-sources-header-actions">
          <span className="qw-pruning-badge">
            {prunedPercent}% Noise Pruned
          </span>
          <button
            type="button"
            className="qw-toggle-btn"
            aria-label={isExpanded ? 'Collapse sources panel' : 'Expand sources panel'}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="qw-sources-body">
          {/* 1. Selected Sources Section */}
          <div className="qw-sources-group">
            <div className="qw-group-label selected">
              <CheckCircle2 size={14} />
              <span>Selected for Bounded Retrieval ({selectedSources.length})</span>
            </div>

            {selectedSources.length > 0 ? (
              <div className="qw-source-chips-grid">
                {selectedSources.map((id) => {
                  const meta = sourceMap.get(id);
                  const name = meta?.name || id;
                  const type = meta?.type || 'documents';
                  const auth = meta?.authority ?? 0.8;

                  return (
                    <div key={id} className="qw-source-chip selected">
                      <div className="qw-chip-icon-box">{getSourceIcon(type)}</div>
                      <div className="qw-chip-content">
                        <span className="qw-chip-name" title={name}>{name}</span>
                        <div className="qw-chip-meta">
                          <span className="qw-chip-id font-mono">{id}</span>
                          <span className="qw-chip-auth">Auth: {auth.toFixed(2)}</span>
                        </div>
                      </div>
                      <span className="qw-chip-status-tag selected">Selected</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="qw-empty-selected">
                <span>No sources met the minimum relevance threshold for this query.</span>
              </div>
            )}
          </div>

          {/* 2. Skipped Sources Section */}
          <div className="qw-sources-group">
            <div className="qw-group-label skipped">
              <XCircle size={14} />
              <span>Skipped to Conserve Retrieval Budget ({skippedSources.length})</span>
            </div>

            {skippedSources.length > 0 ? (
              <div className="qw-source-chips-grid">
                {skippedSources.map((id) => {
                  const meta = sourceMap.get(id);
                  const name = meta?.name || id;
                  const type = meta?.type || 'documents';

                  return (
                    <div key={id} className="qw-source-chip skipped">
                      <div className="qw-chip-icon-box">{getSourceIcon(type)}</div>
                      <div className="qw-chip-content">
                        <span className="qw-chip-name" title={name}>{name}</span>
                        <div className="qw-chip-meta">
                          <span className="qw-chip-id font-mono">{id}</span>
                          <span className="qw-chip-status">Pruned</span>
                        </div>
                      </div>
                      <span className="qw-chip-status-tag skipped">Skipped</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="qw-empty-skipped">
                <span>All registered sources were selected.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
