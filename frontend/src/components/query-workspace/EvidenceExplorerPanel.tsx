import React, { useState } from 'react';
import {
  FileText,
  MessageSquare,
  Ticket,
  ChevronDown,
  ChevronUp,
  Award,
  Compass,
  Search,
  Filter,
} from 'lucide-react';
import { EvidencePassage } from '../../types';
import './EvidenceExplorerPanel.css';

interface EvidenceExplorerPanelProps {
  evidenceList: EvidencePassage[];
}

export const EvidenceExplorerPanel: React.FC<EvidenceExplorerPanelProps> = ({ evidenceList }) => {
  const [expandedChunkIds, setExpandedChunkIds] = useState<Record<string, boolean>>({});
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const toggleChunk = (chunkId: string) => {
    setExpandedChunkIds((prev) => ({
      ...prev,
      [chunkId]: !prev[chunkId],
    }));
  };

  const expandAll = () => {
    const allExpanded: Record<string, boolean> = {};
    evidenceList.forEach((e) => {
      allExpanded[e.chunk_id] = true;
    });
    setExpandedChunkIds(allExpanded);
  };

  const collapseAll = () => {
    setExpandedChunkIds({});
  };

  const getSourceIcon = (type?: string) => {
    const t = (type || '').toLowerCase();
    if (t.includes('conv') || t.includes('chat') || t.includes('meeting')) {
      return <MessageSquare size={14} className="source-icon-conv" />;
    }
    if (t.includes('ticket') || t.includes('alert') || t.includes('issue')) {
      return <Ticket size={14} className="source-icon-ticket" />;
    }
    return <FileText size={14} className="source-icon-doc" />;
  };

  const getSourceBadgeClass = (type?: string) => {
    const t = (type || '').toLowerCase();
    if (t.includes('conv')) return 'badge-type-conv';
    if (t.includes('ticket')) return 'badge-type-ticket';
    return 'badge-type-doc';
  };

  // Filtered evidence
  const filtered = evidenceList.filter((item) => {
    const matchesType =
      filterType === 'all' ||
      (item.source_type && item.source_type.toLowerCase().includes(filterType.toLowerCase()));
    const matchesSearch =
      !searchTerm ||
      item.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.source_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.title && item.title.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesType && matchesSearch;
  });

  return (
    <div className="evidence-explorer-panel">
      {/* Explorer Header */}
      <div className="evidence-explorer-header">
        <div className="evidence-title-row">
          <div className="evidence-header-title">
            <Compass size={18} />
            <h3>Evidence Explorer</h3>
            <span className="evidence-count-badge">{filtered.length} Passages</span>
          </div>

          <div className="evidence-quick-actions">
            <button
              type="button"
              className="evidence-toggle-all-btn"
              onClick={expandAll}
              title="Expand all evidence cards"
            >
              Expand All
            </button>
            <span className="action-sep">•</span>
            <button
              type="button"
              className="evidence-toggle-all-btn"
              onClick={collapseAll}
              title="Collapse all evidence cards"
            >
              Collapse All
            </button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="evidence-filters-bar">
          <div className="evidence-search-wrap">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Search retrieved passage text or source..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="evidence-search-input"
            />
          </div>

          <div className="evidence-filter-chips">
            <Filter size={13} className="filter-icon" />
            {(['all', 'document', 'conversation', 'ticket'] as const).map((type) => (
              <button
                key={type}
                type="button"
                className={`filter-chip ${filterType === type ? 'chip-active' : ''}`}
                onClick={() => setFilterType(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Passages List */}
      <div className="evidence-passages-list">
        {filtered.length === 0 ? (
          <div className="evidence-empty-box">
            <p>No evidence passages match your current filter.</p>
          </div>
        ) : (
          filtered.map((passage, index) => {
            const isExpanded = expandedChunkIds[passage.chunk_id] ?? (index === 0);
            const score = passage.evidence_score;
            const compositeScore = score?.final_evidence_score ?? 0;

            return (
              <div
                key={passage.chunk_id}
                className={`evidence-card ${isExpanded ? 'card-expanded' : ''}`}
              >
                <div
                  className="evidence-card-header"
                  onClick={() => toggleChunk(passage.chunk_id)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="card-header-left">
                    <span className="passage-rank-badge">#{index + 1}</span>

                    <span className={`source-type-badge ${getSourceBadgeClass(passage.source_type)}`}>
                      {getSourceIcon(passage.source_type)}
                      <span>{passage.source_name}</span>
                    </span>

                    {passage.citation && (
                      <span className="passage-cite-tag">
                        [{passage.citation}]
                      </span>
                    )}

                    {passage.title && (
                      <span className="passage-title-snippet">{passage.title}</span>
                    )}
                  </div>

                  <div className="card-header-right">
                    {score && (
                      <div className="composite-score-badge">
                        <Award size={13} />
                        <span>Score: <strong>{(compositeScore * 100).toFixed(0)}</strong></span>
                      </div>
                    )}

                    <span className="card-toggle-icon">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </span>
                  </div>
                </div>

                {/* Content snippet */}
                <div className="evidence-card-body">
                  <div className={`passage-content ${isExpanded ? 'content-full' : 'content-collapsed'}`}>
                    "{passage.content}"
                  </div>

                  {/* 4D Multi-factor Evidence Metrics (Expanded) */}
                  {isExpanded && score && (
                    <div className="evidence-metrics-grid">
                      <div className="metric-pill">
                        <span className="metric-name">Relevance</span>
                        <div className="metric-progress-track">
                          <div
                            className="metric-progress-bar bar-rel"
                            style={{ width: `${(score.relevance_score * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className="metric-val">{score.relevance_score.toFixed(2)}</span>
                      </div>

                      <div className="metric-pill">
                        <span className="metric-name">Authority</span>
                        <div className="metric-progress-track">
                          <div
                            className="metric-progress-bar bar-auth"
                            style={{ width: `${(score.authority_score * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className="metric-val">{score.authority_score.toFixed(2)}</span>
                      </div>

                      <div className="metric-pill">
                        <span className="metric-name">Freshness</span>
                        <div className="metric-progress-track">
                          <div
                            className="metric-progress-bar bar-fresh"
                            style={{ width: `${score.freshness_score !== null ? (score.freshness_score * 100).toFixed(0) : 0}%` }}
                          />
                        </div>
                        <span className="metric-val">
                          {score.freshness_score !== null ? score.freshness_score.toFixed(2) : 'N/A'}
                        </span>
                      </div>

                      <div className="metric-pill">
                        <span className="metric-name">Directness</span>
                        <div className="metric-progress-track">
                          <div
                            className="metric-progress-bar bar-dir"
                            style={{ width: `${(score.directness_score * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className="metric-val">{score.directness_score.toFixed(2)}</span>
                      </div>
                    </div>
                  )}

                  {/* Metadata footer */}
                  {isExpanded && (
                    <div className="evidence-card-footer">
                      <span className="meta-chunk-id">Chunk ID: <code>{passage.chunk_id}</code></span>
                      {passage.source_id && (
                        <span className="meta-source-id">Source ID: <code>{passage.source_id}</code></span>
                      )}
                      {passage.record_id && (
                        <span className="meta-record-id">Record ID: <code>{passage.record_id}</code></span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
