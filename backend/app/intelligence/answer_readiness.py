"""
EvidenRoute - Answer Readiness Decision Engine
Synthesizes conflict reports, sufficiency evaluations, and pruned context
into a final explainable readiness verdict prior to downstream LLM generation.
"""

from typing import Any, Dict
from .models import (
    AnswerReadinessResult,
    ConflictDetectionResult,
    EvidenceSufficiencyResult,
    PrunedContextResult,
    RecommendedAction,
)


class AnswerReadinessEvaluator:
    """
    Evaluates whether the system is cleared to generate a factual answer,
    or whether it must abstain, clarify, or retrieve additional context.
    """

    def evaluate_readiness(
        self,
        sufficiency: EvidenceSufficiencyResult,
        conflict_result: ConflictDetectionResult,
        pruning_result: PrunedContextResult,
    ) -> AnswerReadinessResult:
        """
        Synthesize readiness verdict and structured explanation.
        """
        action = sufficiency.recommended_action
        is_ready = action == RecommendedAction.ANSWER.value

        if action == RecommendedAction.ANSWER.value:
            verdict = "READY_TO_ANSWER"
            justification = (
                f"Retrieved evidence is sufficient (score {sufficiency.sufficiency_score:.2f}) "
                f"with {len(sufficiency.supporting_evidence)} corroborating passage(s) and zero unresolved contradictions."
            )
        elif action == RecommendedAction.CLARIFY.value:
            verdict = "NEEDS_CLARIFICATION"
            justification = (
                f"Factual contradictions detected across evidence ({conflict_result.direct_contradictions_count} direct contradiction(s)). "
                f"User clarification is required regarding contradictory versions or configurations."
            )
        elif action == RecommendedAction.RETRIEVE_MORE.value:
            verdict = "NEEDS_ADDITIONAL_RETRIEVAL"
            justification = (
                f"Evidence is incomplete (missing: {', '.join(sufficiency.missing_information) if sufficiency.missing_information else 'direct answers'}). "
                f"Recommend expanding search queries or relaxing source filters."
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

        return AnswerReadinessResult(
            is_ready_to_answer=is_ready,
            readiness_verdict=verdict,
            recommended_action=action,
            confidence_score=sufficiency.sufficiency_score,
            primary_justification=justification,
            conflicts_summary=conflicts_summary,
            sufficiency_summary=sufficiency_summary,
            pruning_summary=pruning_summary,
        )
