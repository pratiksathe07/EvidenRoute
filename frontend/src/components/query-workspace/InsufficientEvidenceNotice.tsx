import React from 'react';
import {
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { AnswerReadinessResult, EvidenceSufficiencyResult } from '../../types/retrieval';
import './InsufficientEvidenceNotice.css';

interface InsufficientEvidenceNoticeProps {
  readiness?: AnswerReadinessResult;
  sufficiency?: EvidenceSufficiencyResult;
}

export const InsufficientEvidenceNotice: React.FC<InsufficientEvidenceNoticeProps> = ({
  readiness,
  sufficiency,
}) => {
  if (!readiness && !sufficiency) return null;

  const isReady = readiness?.is_ready_to_answer ?? sufficiency?.is_sufficient ?? true;
  const verdict = readiness?.readiness_verdict || (sufficiency?.is_sufficient ? 'SUFFICIENT' : 'INSUFFICIENT');
  const action = readiness?.recommended_action || sufficiency?.recommended_action || 'answer';
  const justification = readiness?.primary_justification || sufficiency?.explanation || '';
  const missingInfo = sufficiency?.missing_information || [];

  // If evidence is sufficient and ready, show a subtle green confirmation badge
  if (isReady && action === 'answer') {
    return (
      <div className="qw-notice-banner ready">
        <div className="qw-notice-icon-box">
          <CheckCircle2 size={18} />
        </div>
        <div className="qw-notice-content">
          <div className="qw-notice-title-row">
            <span className="qw-notice-heading">Evidence Verified & Sufficient</span>
            <span className="qw-verdict-pill ready">{verdict}</span>
          </div>
          <p className="qw-notice-text">{justification}</p>
        </div>
      </div>
    );
  }

  // If abstaining or insufficient
  return (
    <div className={`qw-notice-banner ${action === 'abstain' ? 'abstain' : 'warning'}`}>
      <div className="qw-notice-icon-box">
        {action === 'abstain' ? <ShieldAlert size={20} /> : <AlertTriangle size={20} />}
      </div>
      <div className="qw-notice-content">
        <div className="qw-notice-title-row">
          <span className="qw-notice-heading">
            {action === 'abstain'
              ? 'Honest Abstention — Insufficient Grounding Evidence'
              : 'Uncertainty / Clarification Needed'}
          </span>
          <span className={`qw-verdict-pill ${action === 'abstain' ? 'abstain' : 'warning'}`}>
            {verdict}
          </span>
        </div>

        <p className="qw-notice-text">
          {justification ||
            'The EvidenRoute engine evaluated candidate grounding sources and determined that evidence is insufficient to formulate a reliable answer without risk of hallucination.'}
        </p>

        {missingInfo.length > 0 && (
          <div className="qw-missing-info-block">
            <span className="qw-missing-info-title">
              <Info size={12} /> Identified Information Gaps:
            </span>
            <ul className="qw-missing-info-list">
              {missingInfo.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="qw-notice-policy-note">
          <HelpCircle size={13} />
          <span>
            <strong>EvidenRoute Integrity Principle:</strong> When grounding evidence does not substantiate a claim, our engine transparently abstains rather than inventing plausible-sounding hallucinations.
          </span>
        </div>
      </div>
    </div>
  );
};
