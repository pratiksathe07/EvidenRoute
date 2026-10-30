import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FileSearch,
  Search,
  FolderOpen,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  MessageSquare,
  Ticket,
  Database,
  ShieldAlert,
  Layers,
} from 'lucide-react';
import { retrieveEvidence } from '../services/retrievalService';
import { EvidencePassage, ConflictReport } from '../types/retrieval';
import './EvidenceExplorerPage.css';

const PRESET_QUERIES = [
  'Why did the payment API fail after deployment?',
  'What is the database connection timeout limit?',
  'What is the employee leave policy for parental leave?',
  'How is Kafka clustered across AZs?',
];

export const EvidenceExplorerPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>(PRESET_QUERIES[0]);
  const [evidenceList, setEvidenceList] = useState<EvidencePassage[]>([]);
  const [conflicts, setConflicts] = useState<ConflictReport[]>([]);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>('all');
  const [qualityFilter, setQualityFilter] = useState<string>('all');

  // Expanded card state
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchEvidence = useCallback(async (queryToRun: string) => {
    const trimmed = queryToRun.trim();
    if (!trimmed) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      // Call actual retrieval pipeline endpoint: POST /api/intelligence/retrieve
      const res = await retrieveEvidence({
        question: trimmed,
        top_k: 12,
      });

      if (res.data) {
        setEvidenceList(res.data.retrieved_evidence || []);
        setConflicts(res.data.conflicts || []);
      } else {
        setErrorMsg(res.error || 'Failed to retrieve evidence from backend.');
        setEvidenceList([]);
        setConflicts([]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error connecting to evidence retrieval engine.';
      setErrorMsg(msg);
      setEvidenceList([]);
      setConflicts([]);
    } finally {
      setIsLoading(false);
      setHasSearched(true);
    }
  }, []);

  // Fetch initial evidence on mount using real backend query
  useEffect(() => {
    fetchEvidence(PRESET_QUERIES[0]);
  }, [fetchEvidence]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEvidence(searchQuery);
  };

  const handleSelectPreset = (preset: string) => {
    setSearchQuery(preset);
    fetchEvidence(preset);
  };

  const toggleExpand = (id: string) => {
    setExpandedCards((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleCopyCitation = (citation: string, id: string) => {
    navigator.clipboard.writeText(citation);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'documents':
      case 'document':
        return <FileText size={13} />;
      case 'conversations':
      case 'conversation':
        return <MessageSquare size={13} />;
      case 'tickets':
      case 'ticket':
        return <Ticket size={13} />;
      default:
        return <Database size={13} />;
    }
  };

  // Filtered evidence list (operates strictly on actual returned passages)
  const filteredEvidence = useMemo(() => {
    return evidenceList.filter((ev) => {
      // 1. Source type filter
      if (selectedType !== 'all') {
        const t = ev.source_type.toLowerCase();
        if (selectedType === 'documents' && !t.includes('document')) return false;
        if (selectedType === 'tickets' && !t.includes('ticket')) return false;
        if (selectedType === 'conversations' && !t.includes('conversation')) return false;
      }

      // 2. Quality filter
      if (qualityFilter === 'high_authority') {
        if (ev.authority_level < 0.85) return false;
      } else if (qualityFilter === 'direct') {
        if (ev.evidence_score?.directness_label !== 'direct' && (ev.evidence_score?.directness_score ?? 0) < 0.9) {
          return false;
        }
      }

      return true;
    });
  }, [evidenceList, selectedType, qualityFilter]);

  return (
    <div className="ee-page-container">
      {/* 1. Page Header */}
      <header className="ee-page-header">
        <div className="ee-header-title-group">
          <div className="ee-badge-row">
            <span className="ee-badge">
              <Layers size={13} />
              Evidence Repository
            </span>
            <span className="ee-badge">4D Multi-Dimensional Scoring</span>
          </div>
          <h1 className="ee-page-title">Evidence Explorer</h1>
          <p className="ee-page-subtitle">
            Inspect retrieved knowledge passages, provenance citations, 4D scoring dimensions
            (Relevance, Authority, Freshness, Directness), and detected factual contradictions.
          </p>
        </div>
      </header>

      {/* 2. Search & Filter Bar */}
      <section className="ee-search-card">
        <form className="ee-search-form" onSubmit={handleSearchSubmit}>
          <div className="ee-search-input-wrap">
            <Search size={17} className="ee-search-icon" />
            <input
              type="text"
              className="ee-search-input"
              placeholder="Search or enter an inquiry to explore retrieved evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="ee-submit-btn"
            disabled={isLoading || !searchQuery.trim()}
          >
            <FileSearch size={15} />
            <span>{isLoading ? 'Retrieving...' : 'Explore Evidence'}</span>
          </button>
        </form>

        {/* Preset Chips */}
        <div className="ee-preset-chips-row">
          <span className="ee-preset-label">Preset Inquiries:</span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              type="button"
              className={`ee-preset-chip ${searchQuery === preset ? 'active' : ''}`}
              onClick={() => handleSelectPreset(preset)}
            >
              {preset}
            </button>
          ))}
        </div>

        {/* Type & Quality Filters */}
        <div className="ee-filters-row">
          <div className="ee-filter-group">
            <span className="ee-preset-label">Source Type:</span>
            {['all', 'documents', 'tickets', 'conversations'].map((type) => (
              <button
                key={type}
                type="button"
                className={`ee-filter-pill ${selectedType === type ? 'active' : ''}`}
                onClick={() => setSelectedType(type)}
              >
                {type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>

          <div className="ee-filter-group">
            <span className="ee-preset-label">Quality Filter:</span>
            {[
              { id: 'all', label: 'All Evidence' },
              { id: 'direct', label: 'Direct Coverage' },
              { id: 'high_authority', label: 'High Authority (≥0.85)' },
            ].map((q) => (
              <button
                key={q.id}
                type="button"
                className={`ee-filter-pill ${qualityFilter === q.id ? 'active' : ''}`}
                onClick={() => setQualityFilter(q.id)}
              >
                {q.label}
              </button>
            ))}
          </div>

          <span className="ee-results-count">
            Showing {filteredEvidence.length} of {evidenceList.length} passage(s)
          </span>
        </div>
      </section>

      {/* 3. Contradictions Banner if present in actual response */}
      {conflicts && conflicts.length > 0 && (
        <section className="ee-conflict-card" aria-label="Detected Contradictions">
          <div className="ee-conflict-header">
            <div className="ee-conflict-title-wrap">
              <ShieldAlert size={18} />
              <span>Factual Contradictions &amp; Divergences Detected</span>
            </div>
            <span className="ee-conflict-severity">
              {conflicts[0].severity} • {conflicts.length} conflict(s)
            </span>
          </div>

          {conflicts.map((conf) => (
            <div key={conf.conflict_id} style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <p className="ee-conflict-desc">
                <strong>{conf.topic}:</strong> {conf.explanation}
              </p>
              {conf.conflicting_passages && conf.conflicting_passages.length > 0 && (
                <div className="ee-conflict-passages">
                  {conf.conflicting_passages.map((p, idx) => (
                    <div key={idx} className="ee-conflict-box">
                      <strong>
                        {p.source_name} ({p.chunk_id})
                      </strong>
                      <span>{p.statement}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      {/* 4. Evidence Passages List */}
      <section className="ee-evidence-list" aria-label="Evidence Passages">
        {isLoading ? (
          <div className="ee-empty-state">
            <span className="qw-evidence-spinner" />
            <h3 className="ee-empty-title">Retrieving and Scoring Evidence Passages...</h3>
            <p className="ee-empty-desc">
              Searching bounded sources and computing 4D relevance, authority, freshness, and directness scores.
            </p>
          </div>
        ) : errorMsg ? (
          <div className="ee-empty-state">
            <div className="ee-empty-icon" style={{ color: '#EF4444' }}>
              <ShieldAlert size={26} />
            </div>
            <h3 className="ee-empty-title">Evidence Retrieval Failed</h3>
            <p className="ee-empty-desc">{errorMsg}</p>
          </div>
        ) : filteredEvidence.length === 0 ? (
          <div className="ee-empty-state">
            <div className="ee-empty-icon">
              <FolderOpen size={26} />
            </div>
            <h3 className="ee-empty-title">
              {hasSearched ? 'No Evidence Found for This Inquiry' : 'Awaiting Query Search'}
            </h3>
            <p className="ee-empty-desc">
              {hasSearched
                ? 'The backend evaluated available knowledge sources but returned zero candidate passages satisfying the relevance threshold.'
                : 'Enter an inquiry above to retrieve and explore verified evidence passages directly from the backend.'}
            </p>
          </div>
        ) : (
          filteredEvidence.map((passage, index) => {
            const isExpanded = Boolean(expandedCards[passage.chunk_id]);
            const score = passage.evidence_score;

            return (
              <article key={passage.chunk_id} className="ee-card">
                {/* Top Row: Rank, Source Info, Authority Badge */}
                <div className="ee-card-top-row">
                  <div className="ee-source-meta-group">
                    <span className="ee-rank-badge">#{passage.ranking_position || index + 1}</span>
                    <span className={`ee-source-type-pill ${passage.source_type.toLowerCase()}`}>
                      {getSourceIcon(passage.source_type)}
                      <span>{passage.source_type}</span>
                    </span>
                    <span className="ee-source-name-label">{passage.source_name}</span>
                  </div>

                  <span className="ee-authority-badge">
                    Authority: {passage.authority_level !== undefined ? passage.authority_level.toFixed(2) : 'N/A'}
                  </span>
                </div>

                {/* Citation & File Reference */}
                <div className="ee-citation-ref-row">
                  <span className="ee-citation-text" title={passage.citation}>
                    {passage.citation || `${passage.original_file_path} (Chunk ${passage.chunk_index})`}
                  </span>
                  <button
                    type="button"
                    className="ee-copy-citation-btn"
                    onClick={() => handleCopyCitation(passage.citation, passage.chunk_id)}
                    title="Copy full citation"
                  >
                    {copiedId === passage.chunk_id ? (
                      <>
                        <Check size={12} style={{ color: 'var(--color-success)' }} />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy size={12} />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Title & Extracted Content */}
                <h3 className="ee-passage-title">{passage.title}</h3>
                <div className="ee-passage-content">{passage.content}</div>

                {/* 4D Evidence Scores Row */}
                {score && (
                  <div className="ee-scores-bar">
                    <span className="ee-score-pill">
                      Relevance: <strong>{score.relevance_score !== undefined ? score.relevance_score.toFixed(2) : 'N/A'}</strong>
                    </span>
                    <span className="ee-score-pill">
                      Authority: <strong>{score.authority_score !== undefined ? score.authority_score.toFixed(2) : 'N/A'}</strong>
                    </span>
                    <span className="ee-score-pill">
                      Freshness:{' '}
                      <strong>
                        {score.freshness_score !== null && score.freshness_score !== undefined
                          ? score.freshness_score.toFixed(2)
                          : 'N/A'}{' '}
                        ({score.freshness_status || 'unknown'})
                      </strong>
                    </span>
                    <span className="ee-score-pill">
                      Directness:{' '}
                      <strong>
                        {score.directness_score !== undefined ? score.directness_score.toFixed(2) : 'N/A'}{' '}
                        ({score.directness_label || 'unclassified'})
                      </strong>
                    </span>
                    <span className="ee-score-pill composite">
                      Composite Score:{' '}
                      <strong>
                        {score.final_evidence_score !== undefined ? score.final_evidence_score.toFixed(2) : 'N/A'}
                      </strong>
                    </span>

                    {/* Expandable toggle */}
                    <button
                      type="button"
                      className="ee-details-toggle"
                      onClick={() => toggleExpand(passage.chunk_id)}
                      title={isExpanded ? 'Hide passage details' : 'Show passage details'}
                    >
                      <span>{isExpanded ? 'Less Details' : 'More Details'}</span>
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>
                )}

                {/* Expandable Details Drawer */}
                {isExpanded && (
                  <div className="ee-details-drawer">
                    <div className="ee-detail-row">
                      <span className="ee-detail-label">Chunk ID:</span>
                      <code>{passage.chunk_id}</code>
                    </div>
                    <div className="ee-detail-row">
                      <span className="ee-detail-label">Original File:</span>
                      <span>{passage.original_file_path} (Chunk #{passage.chunk_index})</span>
                    </div>
                    {passage.created_at && (
                      <div className="ee-detail-row">
                        <span className="ee-detail-label">Created / Updated:</span>
                        <span>{passage.created_at}</span>
                      </div>
                    )}
                    <div className="ee-detail-row">
                      <span className="ee-detail-label">Retrieval Mode:</span>
                      <span>
                        {passage.retrieval_mode} (BM25: {passage.bm25_score !== undefined ? passage.bm25_score.toFixed(3) : 'N/A'})
                      </span>
                    </div>
                    {score?.scoring_explanation && (
                      <div className="ee-detail-row">
                        <span className="ee-detail-label">Scoring Logic:</span>
                        <span>{score.scoring_explanation}</span>
                      </div>
                    )}
                  </div>
                )}
              </article>
            );
          })
        )}
      </section>
    </div>
  );
};

export default EvidenceExplorerPage;
