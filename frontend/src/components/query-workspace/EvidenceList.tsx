import React, { useState, useMemo } from 'react';
import {
  FileSearch,
  FolderOpen,
  ArrowUpDown,
} from 'lucide-react';
import { EvidencePassage } from '../../types/retrieval';
import { EvidenceCard } from './EvidenceCard';
import './EvidenceList.css';

interface EvidenceListProps {
  evidence: EvidencePassage[];
  hasExecuted: boolean;
  isLoading: boolean;
}

type SortCriteria = 'composite' | 'relevance' | 'authority' | 'freshness';

export const EvidenceList: React.FC<EvidenceListProps> = ({
  evidence,
  hasExecuted,
  isLoading,
}) => {
  const [sortBy, setSortBy] = useState<SortCriteria>('composite');

  const sortedEvidence = useMemo(() => {
    const list = [...evidence];
    switch (sortBy) {
      case 'relevance':
        return list.sort(
          (a, b) => b.evidence_score.relevance_score - a.evidence_score.relevance_score
        );
      case 'authority':
        return list.sort(
          (a, b) => b.evidence_score.authority_score - a.evidence_score.authority_score
        );
      case 'freshness':
        return list.sort(
          (a, b) =>
            (b.evidence_score.freshness_score ?? 0) - (a.evidence_score.freshness_score ?? 0)
        );
      case 'composite':
      default:
        return list.sort(
          (a, b) => b.evidence_score.final_evidence_score - a.evidence_score.final_evidence_score
        );
    }
  }, [evidence, sortBy]);

  if (isLoading) {
    return (
      <div className="qw-evidence-list-card">
        <div className="qw-evidence-loading">
          <span className="qw-evidence-spinner" />
          <p className="qw-loading-title">Retrieving and Scoring Context Passages...</p>
          <p className="qw-loading-sub">
            Executing hybrid bounded retrieval through authorized adapters and calculating 4D evidence weights.
          </p>
        </div>
      </div>
    );
  }

  if (!hasExecuted) {
    return (
      <div className="qw-evidence-list-card">
        <div className="qw-evidence-empty">
          <div className="qw-empty-icon-wrap">
            <FileSearch size={28} />
          </div>
          <h4 className="qw-empty-title">Awaiting Query Execution</h4>
          <p className="qw-empty-sub">
            Submit a question above to retrieve grounding evidence, inspect multi-dimensional scores, and verify citations.
          </p>
        </div>
      </div>
    );
  }

  if (evidence.length === 0) {
    return (
      <div className="qw-evidence-list-card">
        <div className="qw-evidence-empty">
          <div className="qw-empty-icon-wrap warning">
            <FolderOpen size={28} />
          </div>
          <h4 className="qw-empty-title">No Grounding Evidence Retrieved</h4>
          <p className="qw-empty-sub">
            The engine evaluated available context sources but found zero passages satisfying the query relevance threshold.
            Check the Insufficient Evidence Notice above for the engine&apos;s abstention verdict.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="qw-evidence-list-card">
      <div className="qw-evidence-list-header">
        <div className="qw-list-title-wrap">
          <h3 className="qw-list-title">Retrieved Evidence & Citations</h3>
          <span className="qw-count-badge">{evidence.length} Passages Grounded</span>
        </div>

        {/* Sort Controls */}
        <div className="qw-sort-controls">
          <div className="qw-sort-label">
            <ArrowUpDown size={13} />
            <span>Sort by:</span>
          </div>
          <div className="qw-sort-buttons">
            <button
              type="button"
              className={`btn-sort ${sortBy === 'composite' ? 'active' : ''}`}
              onClick={() => setSortBy('composite')}
            >
              Composite
            </button>
            <button
              type="button"
              className={`btn-sort ${sortBy === 'relevance' ? 'active' : ''}`}
              onClick={() => setSortBy('relevance')}
            >
              Relevance
            </button>
            <button
              type="button"
              className={`btn-sort ${sortBy === 'authority' ? 'active' : ''}`}
              onClick={() => setSortBy('authority')}
            >
              Authority
            </button>
            <button
              type="button"
              className={`btn-sort ${sortBy === 'freshness' ? 'active' : ''}`}
              onClick={() => setSortBy('freshness')}
            >
              Freshness
            </button>
          </div>
        </div>
      </div>

      <div className="qw-evidence-items-stack">
        {sortedEvidence.map((passage, idx) => (
          <EvidenceCard key={passage.chunk_id || idx} passage={passage} index={idx} />
        ))}
      </div>
    </div>
  );
};
