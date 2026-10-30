"""
EvidenRoute - Intelligent Source Selector
Calculates explainable, multi-factor ranking scores for knowledge sources
prior to any retrieval execution.

Scoring Formula:
  Raw Score = W_rel * Relevance
            + W_suit * Type_Suitability
            + W_auth * Authority
            + W_hist * Historical_Usefulness
            + W_avail * Availability

Weight Normalization Strategy for Missing Historical Usefulness:
  When a source lacks historical usefulness (e.g. metadata is missing or None),
  EvidenRoute does not fabricate or guess a number. Instead, the historical weight
  is omitted and the active weights are proportionally normalized so their sum equals 1.0:
    W'_k = W_k / sum(W_active)
    Final Score = sum(W'_k * S_k)
  This guarantees that sources without audit logs are neither unfairly penalized
  nor given artificial boosts.
"""

import re
from typing import Dict, List, Optional, Tuple
from .models import (
    QueryAnalysisResult,
    SelectionConfig,
    SelectionStatus,
    SourceMetadata,
    SourceRankResult,
    SourceScoreBreakdown,
)


class SourceSelector:
    """
    Ranks and selects candidate sources using multi-factor explainable scoring.
    """

    def __init__(self, default_config: Optional[SelectionConfig] = None):
        self.default_config = default_config or SelectionConfig()

    def rank_and_select(
        self,
        analysis: QueryAnalysisResult,
        sources: List[SourceMetadata],
        config: Optional[SelectionConfig] = None,
    ) -> List[SourceRankResult]:
        """
        Evaluate candidate sources against query analysis and return ordered, explainable decisions.
        """
        cfg = config or self.default_config

        if not sources:
            return []

        scored_results: List[Tuple[float, SourceRankResult]] = []

        for source in sources:
            # 1. Component Scores
            rel_score, rel_notes = self._compute_relevance(analysis, source)
            suit_score = self._compute_type_suitability(analysis, source)
            auth_score = max(0.0, min(1.0, source.authority_level))
            hist_score = self._extract_historical_usefulness(source)
            avail_score = 1.0 if source.availability else 0.0

            # 2. Dynamic Weight Normalization
            weights_applied, final_score = self._calculate_final_score(
                cfg=cfg,
                rel_score=rel_score,
                suit_score=suit_score,
                auth_score=auth_score,
                hist_score=hist_score,
                avail_score=avail_score,
            )

            # 3. Decision Verdict & Explainability
            status, reason = self._determine_verdict(
                source=source,
                final_score=final_score,
                relevance_score=rel_score,
                suitability_score=suit_score,
                availability=source.availability,
                cfg=cfg,
            )

            calc_notes = [
                f"Relevance: {rel_score:.2f} ({', '.join(rel_notes) if rel_notes else 'no topic hits'})",
                f"Suitability: {suit_score:.2f} (type '{source.source_type}' vs likely {analysis.likely_source_types})",
                f"Authority: {auth_score:.2f}",
                f"Historical: {f'{hist_score:.2f}' if hist_score is not None else 'N/A (weight normalized)'}",
                f"Availability: {avail_score:.1f} ({'Online' if source.availability else 'Offline'})",
            ]

            breakdown = SourceScoreBreakdown(
                relevance_score=round(rel_score, 4),
                type_suitability_score=round(suit_score, 4),
                authority_score=round(auth_score, 4),
                historical_usefulness_score=round(hist_score, 4) if hist_score is not None else None,
                availability_score=round(avail_score, 4),
                weights_applied={k: round(v, 4) for k, v in weights_applied.items()},
                calculation_notes=calc_notes,
            )

            result = SourceRankResult(
                source_id=source.source_id,
                source_name=source.source_name,
                source_type=source.source_type,
                relevance_score=round(rel_score, 4),
                type_suitability_score=round(suit_score, 4),
                authority_score=round(auth_score, 4),
                historical_usefulness_score=round(hist_score, 4) if hist_score is not None else None,
                availability_score=round(avail_score, 4),
                final_score=round(final_score, 4),
                selection_status=status,
                selection_reason=reason,
                ranking_position=0,  # Will be assigned after sort
                score_breakdown=breakdown,
            )

            scored_results.append((final_score, result))

        # Sort descending: final_score desc, then relevance_score desc, then authority desc
        scored_results.sort(
            key=lambda x: (
                x[1].selection_status == SelectionStatus.SELECTED.value,
                x[0],
                x[1].relevance_score,
                x[1].authority_score,
            ),
            reverse=True,
        )

        ranked: List[SourceRankResult] = []
        for rank_idx, (_, res) in enumerate(scored_results, start=1):
            res.ranking_position = rank_idx
            ranked.append(res)

        return ranked

    def _compute_relevance(
        self, analysis: QueryAnalysisResult, source: SourceMetadata
    ) -> Tuple[float, List[str]]:
        """
        Compute topical and lexical relevance score [0.0, 1.0].
        Designed with an interface ready for local embeddings / BM25 in Phase 2.
        """
        notes: List[str] = []
        if not analysis.keywords and not analysis.entities:
            return 0.0, ["Empty query analysis"]

        # Collect source text tokens
        source_topics = [t.lower() for t in (source.supported_topics or [])]
        source_text = f"{source.source_name} {source.description}".lower()
        source_tokens = set(re.findall(r"[A-Za-z0-9_]+", source_text))

        # 1. Entity Matching (High value semantic signal)
        entity_score = 0.0
        if analysis.entities:
            matched_entities = []
            for entity in analysis.entities:
                ent_lower = entity.lower()
                # Check exact or partial topic match
                if any(ent_lower in t or t in ent_lower for t in source_topics):
                    matched_entities.append(entity)
                elif ent_lower in source_text:
                    matched_entities.append(entity)
            if matched_entities:
                entity_score = len(matched_entities) / len(analysis.entities)
                notes.append(f"matched entities: {matched_entities}")

        # 2. Keyword & Technical Term Overlap
        query_words = set(w.lower() for w in analysis.keywords)
        query_words.update(w.lower() for w in analysis.technical_terms)

        if not query_words:
            keyword_score = 0.0
        else:
            topic_hits = set()
            text_hits = set()
            for w in query_words:
                if any(w in t for t in source_topics):
                    topic_hits.add(w)
                if w in source_tokens:
                    text_hits.add(w)

            total_hits = topic_hits.union(text_hits)
            keyword_score = len(total_hits) / len(query_words)
            if total_hits:
                notes.append(f"matched terms: {list(total_hits)[:4]}")

        # Blend: Entity matches weighted at 55%, broad keyword/topic hits at 45%
        if analysis.entities:
            relevance = (0.55 * entity_score) + (0.45 * keyword_score)
        else:
            relevance = keyword_score

        # Bound strictly between 0.0 and 1.0
        return max(0.0, min(1.0, relevance)), notes

    def _compute_type_suitability(
        self, analysis: QueryAnalysisResult, source: SourceMetadata
    ) -> float:
        """
        Score how well the source type aligns with the query's identified intent.
        """
        likely_types = [t.lower() for t in analysis.likely_source_types]
        source_type = source.source_type.lower()

        if not likely_types:
            return 0.50

        if source_type in likely_types:
            idx = likely_types.index(source_type)
            if idx == 0:
                return 1.00  # Primary target
            elif idx == 1:
                return 0.85  # Secondary target
            else:
                return 0.70  # Tertiary target
        return 0.20  # Unlikely source type for this intent

    def _extract_historical_usefulness(self, source: SourceMetadata) -> Optional[float]:
        """Safely extract historical usefulness from metadata, or None if missing."""
        if not source.metadata:
            return None
        val = source.metadata.get("historical_usefulness")
        if val is None:
            return None
        try:
            val_float = float(val)
            return max(0.0, min(1.0, val_float))
        except (ValueError, TypeError):
            return None

    def _calculate_final_score(
        self,
        cfg: SelectionConfig,
        rel_score: float,
        suit_score: float,
        auth_score: float,
        hist_score: Optional[float],
        avail_score: float,
    ) -> Tuple[Dict[str, float], float]:
        """
        Dynamically normalize weights when historical usefulness is unavailable.
        """
        active_weights: Dict[str, float] = {
            "relevance": cfg.relevance_weight,
            "suitability": cfg.suitability_weight,
            "authority": cfg.authority_weight,
            "availability": cfg.availability_weight,
        }
        active_scores: Dict[str, float] = {
            "relevance": rel_score,
            "suitability": suit_score,
            "authority": auth_score,
            "availability": avail_score,
        }

        if hist_score is not None:
            active_weights["historical"] = cfg.historical_weight
            active_scores["historical"] = hist_score

        weight_sum = sum(active_weights.values())
        if weight_sum <= 0:
            return active_weights, 0.0

        # Proportional weight normalization
        normalized_weights = {k: v / weight_sum for k, v in active_weights.items()}

        final_score = sum(
            normalized_weights[k] * active_scores[k] for k in active_weights
        )

        return normalized_weights, max(0.0, min(1.0, final_score))

    def _determine_verdict(
        self,
        source: SourceMetadata,
        final_score: float,
        relevance_score: float,
        suitability_score: float,
        availability: bool,
        cfg: SelectionConfig,
    ) -> Tuple[str, str]:
        """
        Produce a clear, explainable decision statement for selection or omission.
        """
        # Rule 1: Unavailable sources must always be skipped
        if not availability:
            return (
                SelectionStatus.SKIPPED.value,
                f"Skipped: Source '{source.source_name}' is currently offline or unreachable."
            )

        # Rule 2: Minimum relevance threshold
        # High authority must not force selection of completely irrelevant sources
        if relevance_score < cfg.min_relevance_threshold:
            return (
                SelectionStatus.SKIPPED.value,
                f"Skipped: Low query relevance ({relevance_score:.2f} < threshold {cfg.min_relevance_threshold:.2f}). "
                f"Topics do not align with query intent."
            )

        # Rule 3: Final score threshold
        if final_score >= cfg.selection_threshold:
            return (
                SelectionStatus.SELECTED.value,
                f"Selected: Score {final_score:.2f} meets threshold {cfg.selection_threshold:.2f}. "
                f"High relevance ({relevance_score:.2f}) and type suitability ({suitability_score:.2f})."
            )
        else:
            return (
                SelectionStatus.SKIPPED.value,
                f"Skipped: Final score {final_score:.2f} is below selection threshold {cfg.selection_threshold:.2f}."
            )
