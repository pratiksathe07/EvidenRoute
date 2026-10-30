from typing import List, Tuple
from backend.app.schemas.source import SourceInfo, SourceSelectionDecision
from backend.app.services.query_understanding import QueryProfile


class SourceSelectorService:
    """
    Intelligently ranks and chooses which sources to query.
    Prevents indiscriminate, wasteful querying across all repositories.
    """

    @classmethod
    def select_sources(
        cls,
        profile: QueryProfile,
        available_sources: List[SourceInfo],
        max_to_select: int = 2,
        min_relevance_threshold: float = 0.35,
    ) -> List[SourceSelectionDecision]:
        decisions: List[SourceSelectionDecision] = []
        scored_candidates: List[Tuple[float, SourceInfo, str]] = []

        for src in available_sources:
            if not src.enabled or src.status == "disabled" or src.status == "offline":
                decisions.append(
                    SourceSelectionDecision(
                        source_id=src.source_id,
                        selected=False,
                        relevance_score=0.0,
                        reason=f"Source is inactive or offline ({src.status}).",
                        allocated_limit=0,
                    )
                )
                continue

            # 1. Source type compatibility
            type_compat = 0.0
            if src.source_type in profile.expected_source_types:
                # Rank priority by position in expected types
                idx = profile.expected_source_types.index(src.source_type)
                type_compat = max(0.2, 0.45 - (idx * 0.1))

            # 2. Textual relevance between query keywords and source name + description
            src_text = f"{src.name} {src.description}".lower()
            keyword_hits = sum(1 for kw in profile.clean_keywords if kw in src_text)
            kw_score = min(0.35, keyword_hits * 0.12)

            # 3. Baseline source authority contribution (up to 0.20)
            authority_contribution = src.default_authority * 0.20

            # Composite source suitability score
            total_score = min(1.0, type_compat + kw_score + authority_contribution)

            reason_parts = []
            if type_compat > 0:
                reason_parts.append(f"Type '{src.source_type.value}' matches query profile ({type_compat:.2f})")
            if keyword_hits > 0:
                reason_parts.append(f"{keyword_hits} keyword match(es) in source description ({kw_score:.2f})")
            reason_parts.append(f"Base authority factor ({authority_contribution:.2f})")

            scored_candidates.append((total_score, src, "; ".join(reason_parts)))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Allocate selection
        selected_count = 0
        for score, src, justification in scored_candidates:
            if selected_count < max_to_select and score >= min_relevance_threshold:
                selected_count += 1
                decisions.append(
                    SourceSelectionDecision(
                        source_id=src.source_id,
                        selected=True,
                        relevance_score=round(score, 3),
                        reason=f"Selected: {justification}",
                        allocated_limit=5,
                    )
                )
            else:
                reason = "Rejected: Insufficient relevance score below threshold" if score < min_relevance_threshold else "Rejected: Exceeded max source allocation limit"
                decisions.append(
                    SourceSelectionDecision(
                        source_id=src.source_id,
                        selected=False,
                        relevance_score=round(score, 3),
                        reason=f"{reason} (Score: {score:.2f}).",
                        allocated_limit=0,
                    )
                )

        return decisions
