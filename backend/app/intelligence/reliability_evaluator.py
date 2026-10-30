"""
EvidenRoute - Evidence Reliability Evaluator
Comprehensive multi-factor reliability assessment of the retrieved evidence set.

Core Principles:
1. Keeps individual evidence scores separate from the overall evidence-set evaluation.
2. Does NOT treat multiple duplicate passages from the same source as independent confirmation.
3. Evaluates independent source diversity, contradiction severity, freshness, and completeness.
4. Produces transparent, explainable reliability ratings and recommended actions.
"""

from typing import Dict, List, Optional, Set
from .models import (
    ConflictReport,
    ConflictSeverity,
    CounterEvidenceResult,
    EvidencePassage,
    EvidenceReliabilityResult,
    EvidenceReliabilityStatus,
    QueryAnalysisResult,
    RecommendedAction,
)


class EvidenceReliabilityEvaluator:
    """
    Evaluates the holistic credibility, corroboration, and completeness of an evidence set.
    """

    def evaluate_reliability(
        self,
        query: str,
        analysis: QueryAnalysisResult,
        passages: List[EvidencePassage],
        conflicts: Optional[List[ConflictReport]] = None,
        counter_evidence: Optional[CounterEvidenceResult] = None,
    ) -> EvidenceReliabilityResult:
        """
        Produce structured reliability assessment across 7 dimensions.
        """
        conflicts = conflicts or []

        # 1. Edge Case: Empty evidence set
        if not passages:
            return EvidenceReliabilityResult(
                status=EvidenceReliabilityStatus.INSUFFICIENT.value,
                reliability_score=0.0,
                supporting_evidence_count=0,
                contradictory_evidence_count=0,
                independent_sources_count=0,
                independent_source_ids=[],
                missing_information=["No evidence passages were retrieved for the query."],
                confidence_limitations=["Zero information retrieved from selected sources."],
                recommended_action=RecommendedAction.ABSTAIN.value,
                explanation="Reliability evaluation failed: zero evidence passages retrieved.",
            )

        # 2. Extract unique independent sources
        # Multiple chunks from the same source_id do NOT count as independent sources
        unique_source_ids: Set[str] = set()
        supporting_source_ids: Set[str] = set()
        for p in passages:
            unique_source_ids.add(p.source_id)

        # 3. Identify passages involved in contradictions
        conflicting_chunk_ids: Set[str] = set()
        critical_conflicts: List[ConflictReport] = []
        warning_conflicts: List[ConflictReport] = []

        for c in conflicts:
            if c.severity == ConflictSeverity.CRITICAL.value or c.severity == "critical":
                critical_conflicts.append(c)
            else:
                warning_conflicts.append(c)
            for p_ref in c.conflicting_passages:
                conflicting_chunk_ids.add(p_ref.chunk_id)

        supporting_passages = [p for p in passages if p.chunk_id not in conflicting_chunk_ids]
        contradictory_passages = [p for p in passages if p.chunk_id in conflicting_chunk_ids]

        for p in supporting_passages:
            supporting_source_ids.add(p.source_id)

        # 4. Dimension Calculations
        # 4.1 Relevance
        avg_relevance = sum(p.evidence_score.relevance_score for p in passages) / len(passages)
        top_relevance = max(p.evidence_score.relevance_score for p in passages)

        # 4.2 Authority
        avg_authority = sum(p.authority_level for p in passages) / len(passages)

        # 4.3 Freshness
        freshness_scores = [
            p.evidence_score.freshness_score
            for p in passages
            if p.evidence_score.freshness_score is not None
        ]
        avg_freshness = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.75

        # 4.4 Directness
        avg_directness = sum(p.evidence_score.directness_score for p in passages) / len(passages)

        # 4.5 Independent Source Multiplier
        # Independent sources provide cross-verification
        independent_count = len(supporting_source_ids)
        if independent_count >= 3:
            diversity_factor = 1.0
        elif independent_count == 2:
            diversity_factor = 0.85
        elif independent_count == 1:
            diversity_factor = 0.65
        else:
            diversity_factor = 0.30

        # 4.6 Completeness & Missing Info
        missing_info: List[str] = []
        limitations: List[str] = []

        query_terms = set(analysis.keywords) | set(analysis.entities)
        combined_text = " ".join(p.content.lower() for p in passages)
        for term in query_terms:
            if term.lower() not in combined_text:
                missing_info.append(f"Entity/term '{term}' not corroborated in evidence text.")

        if independent_count == 1 and len(passages) > 1:
            limitations.append(
                f"All {len(passages)} passages originate from a single source ('{list(unique_source_ids)[0]}'); "
                f"duplicate passages do not provide independent external confirmation."
            )

        if avg_authority < 0.65:
            limitations.append(f"Low average authority level ({avg_authority:.2f}); evidence relies on informal channels.")

        if any(p.evidence_score.freshness_status == "stale" for p in passages):
            limitations.append("One or more evidence items are stale (> 365 days old).")

        # 5. Composite Reliability Scoring
        # Base quality
        base_score = (
            0.30 * avg_relevance
            + 0.25 * avg_authority
            + 0.20 * avg_directness
            + 0.15 * avg_freshness
            + 0.10 * diversity_factor
        )

        # Contradiction Penalties
        if critical_conflicts:
            base_score *= 0.40  # Severe penalty for unresolved critical conflicts
            limitations.append(
                f"Critical contradiction detected: {critical_conflicts[0].explanation}"
            )
        elif warning_conflicts:
            base_score *= 0.80
            limitations.append(
                f"Divergence detected: {warning_conflicts[0].explanation}"
            )

        # Counter-Evidence Impact
        if counter_evidence and counter_evidence.counter_evidence_found:
            base_score *= 0.85
            limitations.append(
                f"Counter-evidence search surfaced caveats/exceptions: {counter_evidence.summary}"
            )

        reliability_score = round(max(0.0, min(1.0, base_score)), 4)

        # 6. Status Determination & Action
        if critical_conflicts:
            status = EvidenceReliabilityStatus.CONTRADICTED.value
            action = RecommendedAction.CLARIFY.value
            explanation = (
                f"Evidence set contains direct critical contradictions across {len(conflicts)} point(s). "
                f"Requires user clarification or authoritative reconciliation."
            )
        elif reliability_score >= 0.70 and independent_count >= 1 and avg_authority >= 0.65:
            status = EvidenceReliabilityStatus.HIGH.value
            action = RecommendedAction.ANSWER.value
            explanation = (
                f"High reliability evidence confirmed across {independent_count} independent source(s) "
                f"with strong authority ({avg_authority:.2f}) and directness ({avg_directness:.2f})."
            )
        elif reliability_score >= 0.45:
            status = EvidenceReliabilityStatus.MODERATE.value
            if missing_info:
                action = RecommendedAction.RETRIEVE_MORE.value
                explanation = (
                    f"Moderate reliability ({reliability_score:.2f}). Additional information needed for complete coverage."
                )
            else:
                action = RecommendedAction.ANSWER.value
                explanation = (
                    f"Moderate reliability ({reliability_score:.2f}). Sufficient to answer with noted qualifications."
                )
        elif reliability_score >= 0.25:
            status = EvidenceReliabilityStatus.UNRELIABLE.value
            action = RecommendedAction.RETRIEVE_MORE.value
            explanation = (
                f"Evidence reliability is poor ({reliability_score:.2f}) due to low authority, staleness, or missing key facts."
            )
        else:
            status = EvidenceReliabilityStatus.INSUFFICIENT.value
            action = RecommendedAction.ABSTAIN.value
            explanation = (
                f"Evidence set is insufficient to answer reliably (score {reliability_score:.2f})."
            )

        return EvidenceReliabilityResult(
            status=status,
            reliability_score=reliability_score,
            supporting_evidence_count=len(supporting_passages),
            contradictory_evidence_count=len(contradictory_passages),
            independent_sources_count=independent_count,
            independent_source_ids=sorted(list(supporting_source_ids)),
            missing_information=missing_info,
            confidence_limitations=limitations,
            recommended_action=action,
            explanation=explanation,
        )
