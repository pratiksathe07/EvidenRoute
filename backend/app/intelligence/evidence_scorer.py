"""
EvidenRoute - Evidence Scoring Engine
Evaluates retrieved candidate passages across four independent dimensions:
1. Relevance (R)
2. Authority (A)
3. Freshness (F)
4. Directness (D)

Formula:
  Evidence Score = 0.35 * R + 0.25 * A + 0.20 * F + 0.20 * D

Missing Freshness Normalization:
  When a chunk lacks timestamp metadata, freshness is marked as 'unknown' (None).
  The freshness weight (0.20) is omitted and the active weights for R, A, and D
  are proportionally normalized to sum to 1.0. This prevents artificial penalties
  or fabricated timestamps.
"""

from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Tuple
from .models import (
    ChunkData,
    EvidenceScore,
    EvidenceScoringConfig,
    QueryAnalysisResult,
)


# Domain-specific direct answer indicators
DIRECT_ANSWER_PATTERNS = [
    r"\broot cause\b",
    r"\bresolution\b",
    r"\bfinal decision recorded\b",
    r"\bwe decided to\b",
    r"\bdecision was to\b",
    r"\bpolicy handbook\b",
    r"\bentitled to\b",
    r"\berror rate back to normal\b",
    r"\bhotfix deployed\b",
    r"\bto resolve\b",
    r"\bstep-by-step resolution\b",
    r"\bcommon failure modes\b",
]

SUPPORTING_PATTERNS = [
    r"\bendpoint\b",
    r"\bconfiguration\b",
    r"\bparameter\b",
    r"\btroubleshooting\b",
    r"\bconnection pool\b",
    r"\btimeout\b",
    r"\blatency\b",
    r"\btranscript\b",
    r"\bstatus\b",
    r"\brequires\b",
]


class EvidenceScorer:
    """
    Computes transparent, multi-dimensional evidence scores for retrieved passages.
    """

    def __init__(self, config: Optional[EvidenceScoringConfig] = None):
        self.config = config or EvidenceScoringConfig()

    def score_evidence(
        self,
        chunk: ChunkData,
        retrieval_score: float,
        query_analysis: QueryAnalysisResult,
        reference_time: Optional[datetime] = None,
        config: Optional[EvidenceScoringConfig] = None,
    ) -> EvidenceScore:
        """
        Evaluate a single passage and return complete dimensional breakdown.
        """
        cfg = config or self.config

        # 1. Relevance: bound retrieval score to [0.0, 1.0]
        relevance = max(0.0, min(1.0, float(retrieval_score)))

        # 2. Authority: directly from chunk metadata [0.0, 1.0]
        authority = max(0.0, min(1.0, float(chunk.authority_level)))

        # 3. Freshness: exponential half-life decay F = 2^(-AgeDays / HalfLifeDays)
        freshness_score, freshness_status, age_days = self._calculate_freshness(
            chunk=chunk,
            half_life_days=cfg.freshness_half_life_days,
            ref_time=reference_time,
        )

        # 4. Directness: linguistic and keyword resolution alignment
        directness_score, directness_label, direct_notes = self._evaluate_directness(
            chunk=chunk,
            query_analysis=query_analysis,
        )

        # 5. Dynamic Weight Normalization (handles missing freshness)
        weights_applied, final_score = self._compute_final_score(
            cfg=cfg,
            relevance=relevance,
            authority=authority,
            freshness=freshness_score,
            directness=directness_score,
        )

        # 6. Formulate Explainable Summary
        explanation = self._build_explanation(
            relevance=relevance,
            authority=authority,
            freshness_score=freshness_score,
            freshness_status=freshness_status,
            age_days=age_days,
            directness_label=directness_label,
            final_score=final_score,
        )

        return EvidenceScore(
            relevance_score=round(relevance, 4),
            authority_score=round(authority, 4),
            freshness_score=round(freshness_score, 4) if freshness_score is not None else None,
            freshness_status=freshness_status,
            directness_score=round(directness_score, 4),
            directness_label=directness_label,
            final_evidence_score=round(final_score, 4),
            scoring_explanation=explanation,
            weights_applied={k: round(v, 4) for k, v in weights_applied.items()},
        )

    def _calculate_freshness(
        self,
        chunk: ChunkData,
        half_life_days: float,
        ref_time: Optional[datetime],
    ) -> Tuple[Optional[float], str, Optional[float]]:
        """Compute temporal freshness score and status."""
        timestamp_str = chunk.created_at or chunk.updated_at
        if not timestamp_str:
            return None, "unknown", None

        # Parse timestamp string safely
        parsed_dt = self._parse_datetime(timestamp_str)
        if not parsed_dt:
            return None, "unknown", None

        now = ref_time or datetime(2026, 10, 30, tzinfo=timezone.utc)
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)

        age_delta = now - parsed_dt
        age_days = max(0.0, age_delta.total_seconds() / 86400.0)

        # F = 2^(-AgeDays / HalfLifeDays)
        freshness = math.pow(2.0, -age_days / half_life_days)
        freshness = max(0.0, min(1.0, freshness))

        if freshness >= 0.75:
            status = "fresh"
        elif freshness >= 0.40:
            status = "decayed"
        else:
            status = "stale"

        return freshness, status, age_days

    def _evaluate_directness(
        self,
        chunk: ChunkData,
        query_analysis: QueryAnalysisResult,
    ) -> Tuple[float, str, List[str]]:
        """
        Estimate how directly the passage answers the query.
        Uses transparent rule-based analysis evaluating both title and content.
        """
        full_text = f"{chunk.title} {chunk.content}".lower()
        notes = []

        # Check for direct answer indicators
        direct_matches = [p for p in DIRECT_ANSWER_PATTERNS if re.search(p, full_text)]
        
        # Check query entity presence
        entity_matches = 0
        if query_analysis.entities:
            for entity in query_analysis.entities:
                if entity.lower() in full_text:
                    entity_matches += 1

        # Check query keywords presence
        kw_hits = 0
        for kw in query_analysis.keywords:
            if kw.lower() in full_text:
                kw_hits += 1

        total_kw = max(1, len(query_analysis.keywords))
        kw_ratio = kw_hits / total_kw

        # Decision matrix
        if direct_matches and (entity_matches > 0 or kw_ratio >= 0.50):
            return 1.00, "direct", ["Contains explicit resolution/decision statement and core entities"]
        elif entity_matches > 0 and kw_ratio >= 0.60:
            return 0.85, "supporting", ["Contains all key entities and strong topical coverage"]
        elif any(re.search(p, full_text) for p in SUPPORTING_PATTERNS) or kw_ratio >= 0.35:
            return 0.70, "supporting", ["Provides technical or procedural specifications supporting query"]
        elif kw_ratio > 0.15:
            return 0.45, "indirect", ["Provides contextual background"]
        else:
            return 0.15, "tangential", ["Peripheral mention with low topical alignment"]

    def _compute_final_score(
        self,
        cfg: EvidenceScoringConfig,
        relevance: float,
        authority: float,
        freshness: Optional[float],
        directness: float,
    ) -> Tuple[Dict[str, float], float]:
        """Combine dimensions with dynamic weight normalization for missing timestamps."""
        active_weights: Dict[str, float] = {
            "relevance": cfg.relevance_weight,
            "authority": cfg.authority_weight,
            "directness": cfg.directness_weight,
        }
        active_scores: Dict[str, float] = {
            "relevance": relevance,
            "authority": authority,
            "directness": directness,
        }

        if freshness is not None:
            active_weights["freshness"] = cfg.freshness_weight
            active_scores["freshness"] = freshness

        weight_sum = sum(active_weights.values())
        if weight_sum <= 0:
            return active_weights, 0.0

        normalized_weights = {k: v / weight_sum for k, v in active_weights.items()}
        final_score = sum(normalized_weights[k] * active_scores[k] for k in active_weights)

        return normalized_weights, max(0.0, min(1.0, final_score))

    def _build_explanation(
        self,
        relevance: float,
        authority: float,
        freshness_score: Optional[float],
        freshness_status: str,
        age_days: Optional[float],
        directness_label: str,
        final_score: float,
    ) -> str:
        """Construct human-readable explainability string."""
        fresh_text = (
            f"Freshness: {freshness_score:.2f} ({freshness_status}, ~{int(age_days)}d old)"
            if freshness_score is not None
            else "Freshness: unknown (normalized)"
        )
        return (
            f"Evidence Score {final_score:.2f} [Relevance: {relevance:.2f}, "
            f"Authority: {authority:.2f}, {fresh_text}, "
            f"Directness: {directness_label}]."
        )

    def _parse_datetime(self, val: str) -> Optional[datetime]:
        """Parse various ISO, UTC, or date formats."""
        for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(val.strip(), fmt)
            except (ValueError, TypeError):
                continue
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
