"""
EvidenRoute - Evidence Sufficiency Evaluation Engine
Assesses whether retrieved passages provide adequate, authoritative, and consistent
information to answer the user's inquiry without relying on high retrieval scores alone.
Produces explainable recommended actions: 'answer', 'retrieve_more', 'clarify', or 'abstain'.
"""

from typing import Dict, List, Optional
from .models import (
    ConflictReport,
    EvidencePassage,
    EvidenceSufficiencyResult,
    QueryAnalysisResult,
    RecommendedAction,
    SufficiencyStatus,
)


class SufficiencyEvaluator:
    """
    Evaluates evidence sufficiency across 6 core dimensions:
    relevance, authority, freshness, directness, source diversity, and expected coverage.
    Applies penalties for unresolved direct contradictions.
    """

    def __init__(
        self,
        relevance_weight: float = 0.25,
        directness_weight: float = 0.20,
        coverage_weight: float = 0.20,
        authority_weight: float = 0.15,
        diversity_weight: float = 0.10,
        freshness_weight: float = 0.10,
        min_sufficiency_threshold: float = 0.70,
    ):
        self.weights = {
            "relevance": relevance_weight,
            "directness": directness_weight,
            "coverage": coverage_weight,
            "authority": authority_weight,
            "diversity": diversity_weight,
            "freshness": freshness_weight,
        }
        self.min_sufficiency_threshold = min_sufficiency_threshold

    def evaluate_sufficiency(
        self,
        query: str,
        analysis: QueryAnalysisResult,
        passages: List[EvidencePassage],
        conflicts: List[ConflictReport],
    ) -> EvidenceSufficiencyResult:
        """
        Synthesize multi-dimensional sufficiency score and select actionable next step.
        """
        # Guard: Zero passages retrieved
        if not passages:
            return EvidenceSufficiencyResult(
                is_sufficient=False,
                sufficiency_score=0.0,
                sufficiency_status=SufficiencyStatus.INSUFFICIENT.value,
                supporting_evidence=[],
                missing_information=analysis.expected_information or ["All topical evidence"],
                conflicts_detected=[],
                explanation="No evidence passages were retrieved for this query.",
                recommended_action=RecommendedAction.ABSTAIN.value,
                dimension_scores={k: 0.0 for k in self.weights},
            )

        # 1. Relevance Score Dimension
        top_relevance = max(p.evidence_score.relevance_score for p in passages)
        avg_relevance = sum(p.evidence_score.relevance_score for p in passages) / len(passages)
        rel_dim = (0.7 * top_relevance) + (0.3 * avg_relevance)

        # 2. Directness Score Dimension
        directness_levels = [p.evidence_score.directness_label for p in passages]
        has_direct = "direct" in directness_levels
        has_supporting = "supporting" in directness_levels

        if has_direct:
            dir_dim = 1.00
        elif has_supporting:
            dir_dim = 0.75
        elif "indirect" in directness_levels:
            dir_dim = 0.40
        else:
            dir_dim = 0.15  # Only tangential mentions

        # 3. Expected Information Coverage & Missing Info Extraction
        missing_info, cov_dim = self._evaluate_coverage(analysis, passages)

        # 4. Authority Score Dimension
        auth_dim = max(p.evidence_score.authority_score for p in passages)

        # 5. Independent Source Diversity
        unique_sources = set(p.source_id for p in passages if p.evidence_score.final_evidence_score >= 0.35)
        source_count = len(unique_sources)
        if source_count >= 3:
            div_dim = 1.00
        elif source_count == 2:
            div_dim = 0.85
        elif source_count == 1:
            div_dim = 0.65
        else:
            div_dim = 0.20

        # 6. Freshness Dimension
        fresh_scores = [
            p.evidence_score.freshness_score
            for p in passages
            if p.evidence_score.freshness_score is not None
        ]
        fresh_dim = (sum(fresh_scores) / len(fresh_scores)) if fresh_scores else 0.70

        # Raw Composite Score before conflict penalty
        raw_score = (
            (self.weights["relevance"] * rel_dim)
            + (self.weights["directness"] * dir_dim)
            + (self.weights["coverage"] * cov_dim)
            + (self.weights["authority"] * auth_dim)
            + (self.weights["diversity"] * div_dim)
            + (self.weights["freshness"] * fresh_dim)
        )

        # 7. Conflict Penalty Calculation
        direct_contradictions = [c for c in conflicts if c.is_direct_contradiction]
        conflict_penalty = 0.35 * len(direct_contradictions)
        final_score = max(0.0, min(1.0, raw_score - conflict_penalty))

        # Check for deadlock (opposing high-authority claims)
        has_critical_deadlock = False
        if direct_contradictions:
            for dc in direct_contradictions:
                if len(dc.conflicting_passages) >= 2:
                    has_critical_deadlock = True
                    break

        # 8. Verdict & Recommended Action Assignment
        if has_critical_deadlock:
            # When direct factual contradiction exists on essential claims
            # Check if one claim clearly out-authorizes the other
            is_sufficient = False
            sufficiency_status = SufficiencyStatus.CONFLICTED.value
            recommended_action = RecommendedAction.CLARIFY.value
            final_score = min(final_score, 0.45)
            explanation = (
                f"Conflicting evidence detected ({len(direct_contradictions)} direct contradiction(s)). "
                f"Topic '{direct_contradictions[0].topic}' has opposing claims: {direct_contradictions[0].explanation} "
                f"User clarification is recommended before generating an answer."
            )
        elif final_score < 0.30 or top_relevance < 0.20:
            is_sufficient = False
            sufficiency_status = SufficiencyStatus.INSUFFICIENT.value
            recommended_action = RecommendedAction.ABSTAIN.value
            explanation = (
                f"Evidence score ({final_score:.2f}) is insufficient to substantiate an answer. "
                f"Retrieved content lacks authoritative coverage for query intent '{analysis.intent}'."
            )
        elif final_score < self.min_sufficiency_threshold or not (has_direct or has_supporting) or missing_info:
            is_sufficient = False
            sufficiency_status = SufficiencyStatus.PARTIALLY_SUFFICIENT.value
            recommended_action = RecommendedAction.RETRIEVE_MORE.value
            explanation = (
                f"Evidence is partially sufficient (score {final_score:.2f} < threshold {self.min_sufficiency_threshold:.2f}). "
                f"Missing key information: {', '.join(missing_info) if missing_info else 'direct answer statements'}."
            )
        else:
            is_sufficient = True
            sufficiency_status = SufficiencyStatus.SUFFICIENT.value
            recommended_action = RecommendedAction.ANSWER.value
            explanation = (
                f"Evidence is sufficient (score {final_score:.2f}). "
                f"Provides direct coverage across {source_count} independent source(s) without unhandled contradictions."
            )

        dimension_scores = {
            "relevance": round(rel_dim, 4),
            "directness": round(dir_dim, 4),
            "coverage": round(cov_dim, 4),
            "authority": round(auth_dim, 4),
            "diversity": round(div_dim, 4),
            "freshness": round(fresh_dim, 4),
            "conflict_penalty": round(conflict_penalty, 4),
        }

        # Filter supporting evidence (passages with score >= 0.40)
        supporting = [p for p in passages if p.evidence_score.final_evidence_score >= 0.40]

        return EvidenceSufficiencyResult(
            is_sufficient=is_sufficient,
            sufficiency_score=round(final_score, 4),
            sufficiency_status=sufficiency_status,
            supporting_evidence=supporting,
            missing_information=missing_info,
            conflicts_detected=conflicts,
            explanation=explanation,
            recommended_action=recommended_action,
            dimension_scores=dimension_scores,
        )

    def _evaluate_coverage(
        self, analysis: QueryAnalysisResult, passages: List[EvidencePassage]
    ) -> tuple[List[str], float]:
        """
        Compare expected information artifacts against retrieved text.
        Returns list of missing info items and coverage score [0.0, 1.0].
        """
        expected = analysis.expected_information or []
        if not expected:
            return [], 1.00

        all_text = " ".join(
            f"{p.source_name} {p.source_type} {p.title} {p.content}" for p in passages
        ).lower()
        missing = []

        for item in expected:
            tokens = [t.lower() for t in item.split() if len(t) > 3]
            # Check if any token or its root/stem appears in retrieved evidence
            matched = False
            for tok in tokens:
                tok_stem = tok[:-1] if tok.endswith("s") else (tok[:6] if len(tok) >= 6 else tok)
                if tok in all_text or tok_stem in all_text:
                    matched = True
                    break
            if not matched:
                missing.append(item)

        covered_count = len(expected) - len(missing)
        coverage_score = covered_count / len(expected)

        return missing, max(0.0, min(1.0, coverage_score))
