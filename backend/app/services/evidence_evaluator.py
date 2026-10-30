from datetime import datetime, timezone
from typing import List
from backend.app.schemas.evidence import EvidenceScore, NormalizedEvidence
from backend.app.services.query_understanding import QueryProfile


class EvidenceEvaluatorService:
    """
    Evaluates evidence chunks across four explicit, orthogonal dimensions:
    Relevance, Authority, Freshness, and Directness.
    """

    @classmethod
    def evaluate(
        cls,
        evidence_items: List[NormalizedEvidence],
        profile: QueryProfile,
    ) -> List[EvidenceScore]:
        scores: List[EvidenceScore] = []
        now = datetime.now(timezone.utc)

        for ev in evidence_items:
            content_lower = ev.content.lower()
            title_lower = ev.title.lower()

            # 1. Relevance Score: query keywords & entity matches
            kw_hits = sum(1 for kw in profile.clean_keywords if kw in content_lower or kw in title_lower)
            entity_hits = sum(1 for e in profile.entities if e.lower() in content_lower or e.lower() in title_lower)

            total_search_terms = max(1, len(profile.clean_keywords) + len(profile.entities))
            relevance = min(1.0, 0.2 + ((kw_hits + entity_hits * 1.5) / total_search_terms) * 0.8)

            # 2. Authority Score: inherent source authority
            authority = max(0.1, min(1.0, ev.authority_score))

            # 3. Freshness Score: decay based on age in days
            freshness = 0.5
            item_date = ev.updated_at or ev.created_at
            if item_date:
                # Ensure timezone-awareness
                if item_date.tzinfo is None:
                    item_date = item_date.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - item_date).days)
                if age_days <= 180:
                    freshness = 1.0
                elif age_days <= 365:
                    freshness = 0.85
                elif age_days <= 730:
                    freshness = 0.65
                else:
                    freshness = 0.45

            # 4. Directness Score: explicit answer signals (percentages, days, actionable terms)
            directness_signals = ["%", "days", "guarantee", "eligible", "policy", "refund", "credit", "status", "version"]
            signal_count = sum(1 for s in directness_signals if s in content_lower)
            directness = min(1.0, 0.3 + (signal_count * 0.18))

            # Composite weighted calculation:
            # Relevance (40%), Authority (30%), Freshness (15%), Directness (15%)
            composite = (
                (relevance * 0.40)
                + (authority * 0.30)
                + (freshness * 0.15)
                + (directness * 0.15)
            )

            notes = (
                f"Relevance: {relevance:.2f} ({kw_hits} kw hits, {entity_hits} entities); "
                f"Authority: {authority:.2f}; "
                f"Freshness: {freshness:.2f}; "
                f"Directness: {directness:.2f}"
            )

            scores.append(
                EvidenceScore(
                    evidence_id=ev.evidence_id,
                    relevance_score=round(relevance, 3),
                    authority_score=round(authority, 3),
                    freshness_score=round(freshness, 3),
                    directness_score=round(directness, 3),
                    composite_score=round(composite, 3),
                    evaluation_notes=notes,
                )
            )

        return scores
