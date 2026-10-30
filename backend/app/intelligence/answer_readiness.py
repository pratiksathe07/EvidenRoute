"""
EvidenRoute - Answer Readiness Decision Engine
Synthesizes conflict reports, sufficiency evaluations, and pruned context
into a final explainable readiness verdict prior to downstream LLM generation.
"""

from typing import Any, Dict, Optional
from .models import (
    AnswerReadinessResult,
    ConflictDetectionResult,
    CounterEvidenceResult,
    EvidenceReliabilityResult,
    EvidenceReliabilityStatus,
    EvidenceSufficiencyResult,
    PrunedContextResult,
    RecommendedAction,
)


class AnswerReadinessEvaluator:
    """
    Evaluates whether the system is cleared to generate a factual answer,
    or whether it must abstain, clarify, or retrieve additional context.
    Integrates evidence sufficiency, conflict detection, counter-evidence search,
    and holistic evidence reliability.
    """

    def evaluate_readiness(
        self,
        sufficiency: EvidenceSufficiencyResult,
        conflict_result: ConflictDetectionResult,
        pruning_result: PrunedContextResult,
        reliability: Optional[EvidenceReliabilityResult] = None,
        counter_evidence: Optional[CounterEvidenceResult] = None,
    ) -> AnswerReadinessResult:
        """
        Synthesize readiness verdict and structured explanation.
        """
        # Base action from sufficiency
        action = sufficiency.recommended_action

        # If reliability evaluation detected critical contradiction or poor reliability, override
        if reliability is not None:
            if reliability.status == EvidenceReliabilityStatus.CONTRADICTED.value:
                action = RecommendedAction.CLARIFY.value
            elif reliability.status == EvidenceReliabilityStatus.INSUFFICIENT.value:
                action = RecommendedAction.ABSTAIN.value
            elif reliability.status == EvidenceReliabilityStatus.UNRELIABLE.value and action == RecommendedAction.ANSWER.value:
                action = RecommendedAction.RETRIEVE_MORE.value

        is_ready = action == RecommendedAction.ANSWER.value

        if action == RecommendedAction.ANSWER.value:
            verdict = "READY_TO_ANSWER"
            caveat_str = ""
            if counter_evidence and counter_evidence.counter_evidence_found:
                caveat_str = f" [Note: Qualifying caveat identified: {counter_evidence.summary}]"

            justification = (
                f"Retrieved evidence is sufficient (score {sufficiency.sufficiency_score:.2f}) "
                f"with {len(sufficiency.supporting_evidence)} corroborating passage(s) "
                f"across {reliability.independent_sources_count if reliability else 'multiple'} independent source(s) "
                f"and zero unresolved contradictions.{caveat_str}"
            )
        elif action == RecommendedAction.CLARIFY.value:
            verdict = "NEEDS_CLARIFICATION"
            justification = (
                f"Factual contradictions detected across evidence ({conflict_result.direct_contradictions_count} direct contradiction(s)). "
                f"User clarification is required regarding contradictory versions or configurations."
            )
        elif action == RecommendedAction.RETRIEVE_MORE.value:
            verdict = "NEEDS_ADDITIONAL_RETRIEVAL"
            missing_str = ", ".join(sufficiency.missing_information) if sufficiency.missing_information else "direct answers"
            justification = (
                f"Evidence is incomplete (missing: {missing_str}). "
                f"Recommend expanding search queries or relaxing source filters within budget."
            )
        else:
            verdict = "ABSTAIN_INSUFFICIENT_EVIDENCE"
            justification = (
                "Insufficient evidence available in registered knowledge sources. "
                "Abstaining prevents hallucinated or misleading responses."
            )

        conflicts_summary = {
            "total_detected": conflict_result.conflicts_detected_count,
            "direct_contradictions": conflict_result.direct_contradictions_count,
            "has_unresolved": conflict_result.has_unresolved_contradictions,
        }

        sufficiency_summary = {
            "is_sufficient": sufficiency.is_sufficient,
            "score": sufficiency.sufficiency_score,
            "status": sufficiency.sufficiency_status,
            "missing_info_count": len(sufficiency.missing_information),
        }

        pruning_summary = {
            "original_sentences": pruning_result.original_sentence_count,
            "retained_sentences": pruning_result.retained_sentence_count,
            "pruned_sentences": pruning_result.pruned_sentence_count,
            "compression_ratio": pruning_result.compression_ratio,
            "conflicts_preserved": pruning_result.conflict_passages_preserved_count,
        }

        reliability_summary = {}
        if reliability is not None:
            reliability_summary = {
                "status": reliability.status,
                "score": reliability.reliability_score,
                "independent_sources_count": reliability.independent_sources_count,
                "independent_sources": reliability.independent_source_ids,
                "limitations_count": len(reliability.confidence_limitations),
            }

        # Calculate final confidence score
        if reliability is not None:
            final_confidence = round(0.50 * sufficiency.sufficiency_score + 0.50 * reliability.reliability_score, 4)
        else:
            final_confidence = sufficiency.sufficiency_score

        return AnswerReadinessResult(
            is_ready_to_answer=is_ready,
            readiness_verdict=verdict,
            recommended_action=action,
            confidence_score=final_confidence,
            primary_justification=justification,
            conflicts_summary=conflicts_summary,
            sufficiency_summary=sufficiency_summary,
            pruning_summary=pruning_summary,
            reliability_summary=reliability_summary,
        )

