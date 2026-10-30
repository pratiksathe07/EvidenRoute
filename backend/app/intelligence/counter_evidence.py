"""
EvidenRoute - Counter-Evidence Search Service
Proactively searches for challenges, exceptions, superseding updates,
and counter-evidence to verify primary factual claims within budget limits.

Strict Guarantees:
1. Searches ONLY within eligible sources selected by Phase 1 (never queries skipped sources).
2. Respects and enforces central BudgetManager limits (calls, candidate limits, token limits).
3. Deduplicates against already retrieved chunk IDs to prevent redundant processing.
4. Preserves full citations, source attributions, and author provenance.
5. Accurately reports budget exhaustion or counter-evidence impact in the decision trace.
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple

from backend.app.services.budget_manager import BudgetManager
from .evidence_scorer import EvidenceScorer
from .models import (
    CounterEvidenceResult,
    EvidencePassage,
    EvidenceScoringConfig,
    QueryAnalysisResult,
)
from .retriever import BM25Retriever
from .source_registry import BaseSourceRegistry, SourceRegistry
from .storage import BaseChunkStore, ChunkStore


class CounterEvidenceService:
    """
    Executes bounded counter-evidence discovery over Phase 1 selected sources.
    """

    CHALLENGE_KEYWORDS: List[str] = [
        "exception", "deprecated", "removed", "revision", "updated", "superseded",
        "workaround", "limitation", "override", "dispute", "conflict", "incident",
        "rollback", "outage", "enterprise only", "rider", "special case",
    ]

    COUNTER_CUES: List[str] = [
        "deprecated", "removed", "permanently", "superseded", "instead of",
        "exception", "override", "enterprise", "discontinued", "rollback",
        "misconfigured", "failing", "hotfix", "downgraded", "non-refundable",
    ]

    def __init__(
        self,
        retriever: Optional[BM25Retriever] = None,
        chunk_store: Optional[BaseChunkStore] = None,
        source_registry: Optional[BaseSourceRegistry] = None,
        evidence_scorer: Optional[EvidenceScorer] = None,
    ):
        self.chunk_store = chunk_store or ChunkStore
        self.source_registry = source_registry or SourceRegistry
        self.retriever = retriever or BM25Retriever(chunk_store=self.chunk_store)
        self.evidence_scorer = evidence_scorer or EvidenceScorer()

    def search_counter_evidence(
        self,
        query: str,
        analysis: QueryAnalysisResult,
        initial_evidence: List[EvidencePassage],
        selected_source_ids: List[str],
        budget_manager: Optional[BudgetManager] = None,
        max_candidates: int = 3,
        evidence_config: Optional[EvidenceScoringConfig] = None,
    ) -> Tuple[CounterEvidenceResult, List[EvidencePassage]]:
        """
        Execute bounded counter-evidence search within remaining budget.
        """
        # 1. Guard: If no selected sources or no initial evidence, skip
        if not selected_source_ids or not initial_evidence:
            return (
                CounterEvidenceResult(
                    executed=False,
                    summary="Counter-evidence search skipped: No selected sources or no initial evidence to challenge.",
                ),
                [],
            )

        # 2. Guard: Central budget check
        if budget_manager is not None:
            if not budget_manager.can_allocate(calls=1, candidates=1, tokens=50):
                return (
                    CounterEvidenceResult(
                        executed=False,
                        budget_exhausted=True,
                        summary="Counter-evidence search skipped: Remaining retrieval budget exhausted.",
                    ),
                    [],
                )
            reserved = budget_manager.reserve(calls=1, candidates=max_candidates, tokens=max_candidates * 100)
            if not reserved:
                return (
                    CounterEvidenceResult(
                        executed=False,
                        budget_exhausted=True,
                        summary="Counter-evidence search skipped: Failed to reserve budget.",
                    ),
                    [],
                )

        # 3. Formulate challenge verification query from primary evidence assertions
        challenge_query = self._formulate_challenge_query(query, analysis, initial_evidence)

        # 4. Execute constrained retrieval strictly on selected_source_ids
        # Skipped sources are NEVER queried
        raw_matches = self.retriever.retrieve(
            query=challenge_query,
            selected_source_ids=selected_source_ids,
            top_k=max_candidates * 2,
        )

        # 5. Filter out already retrieved chunks (deduplication)
        initial_chunk_ids: Set[str] = {e.chunk_id for e in initial_evidence}
        new_matches = [
            (chunk, raw_score, norm_score)
            for chunk, raw_score, norm_score in raw_matches
            if chunk.chunk_id not in initial_chunk_ids
        ][:max_candidates]

        # 6. Score newly discovered counter-evidence candidates
        source_name_map = {
            s.source_id: s.source_name for s in self.source_registry.list_sources()
        }
        cfg = evidence_config or EvidenceScoringConfig()
        discovered_passages: List[EvidencePassage] = []

        total_text = ""
        for chunk, raw_bm25, norm_bm25 in new_matches:
            ev_score = self.evidence_scorer.score_evidence(
                chunk=chunk,
                retrieval_score=norm_bm25,
                query_analysis=analysis,
                config=cfg,
            )
            source_name = source_name_map.get(chunk.source_id, chunk.source_id)
            file_name = Path(chunk.original_file_path).name if chunk.original_file_path else "source"
            citation = (
                f"[{source_name} ({chunk.source_id}) § Chunk {chunk.chunk_index}, "
                f"File: {file_name}, Record: {chunk.record_id}]"
            )
            passage = EvidencePassage(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                source_name=source_name,
                source_type=chunk.source_type,
                record_id=chunk.record_id,
                title=chunk.title,
                content=chunk.content,
                authority_level=chunk.authority_level,
                created_at=chunk.created_at,
                original_file_path=chunk.original_file_path,
                chunk_index=chunk.chunk_index,
                retrieval_score=round(norm_bm25, 4),
                bm25_score=round(raw_bm25, 4),
                semantic_score=None,
                retrieval_mode="lexical_counterevidence",
                evidence_score=ev_score,
                citation=citation,
                ranking_position=len(initial_evidence) + len(discovered_passages) + 1,
            )
            discovered_passages.append(passage)
            total_text += " " + chunk.content

        # 7. Commit actual budget consumption
        if budget_manager is not None:
            actual_tokens = BudgetManager.estimate_tokens(total_text)
            budget_manager.commit(
                reserved_calls=1,
                reserved_candidates=max_candidates,
                reserved_tokens=max_candidates * 100,
                actual_calls=1,
                actual_candidates=len(discovered_passages),
                actual_tokens=actual_tokens,
            )

        # 8. Analyze counter-evidence impact
        if not discovered_passages:
            return (
                CounterEvidenceResult(
                    executed=True,
                    challenge_query=challenge_query,
                    counter_evidence_found=False,
                    supporting_evidence_found=True,
                    evidence_examined_count=0,
                    new_passages_retrieved_count=0,
                    budget_used_calls=1,
                    budget_exhausted=False,
                    impact_on_decision="confirmed_answer",
                    summary="Counter-evidence search executed across selected sources. No contradictory or challenge clauses found.",
                    discovered_passages=[],
                ),
                [],
            )

        # Check for challenge cues in discovered passages
        counter_notes: List[str] = []
        is_counter = False

        for p in discovered_passages:
            content_lower = p.content.lower()
            matched_cues = [cue for cue in self.COUNTER_CUES if cue in content_lower]
            if matched_cues:
                is_counter = True
                counter_notes.append(
                    f"[{p.citation}]: Highlights qualification/caveats ({', '.join(matched_cues)})."
                )

        if is_counter:
            impact = "weakened_confidence"
            summary = (
                f"Surfaced {len(discovered_passages)} qualifying counter-evidence item(s): "
                + " ".join(counter_notes)
            )
        else:
            impact = "confirmed_answer"
            summary = (
                f"Retrieved {len(discovered_passages)} corroborating passage(s) "
                f"without finding contradictory clauses or exceptions."
            )

        return (
            CounterEvidenceResult(
                executed=True,
                challenge_query=challenge_query,
                counter_evidence_found=is_counter,
                supporting_evidence_found=not is_counter,
                evidence_examined_count=len(discovered_passages),
                new_passages_retrieved_count=len(discovered_passages),
                budget_used_calls=1,
                budget_exhausted=False,
                impact_on_decision=impact,
                summary=summary,
                discovered_passages=discovered_passages,
            ),
            discovered_passages,
        )

    def _formulate_challenge_query(
        self,
        query: str,
        analysis: QueryAnalysisResult,
        initial_evidence: List[EvidencePassage],
    ) -> str:
        """
        Formulate a challenge query combining core entities/keywords with challenge terms.
        """
        terms: List[str] = []
        if analysis.entities:
            terms.extend(analysis.entities[:2])
        if analysis.keywords:
            terms.extend([k for k in analysis.keywords if k not in terms][:2])

        # Extract numerical or version identifiers from initial evidence
        for ev in initial_evidence[:2]:
            nums = re.findall(r"\b\d+(?:\.\d+)?(?:%|ms|s|h|d|days)?\b", ev.content)
            if nums:
                terms.extend(nums[:1])

        # Append top adversarial keywords
        challenge_part = " ".join(self.CHALLENGE_KEYWORDS[:3])
        if terms:
            return f"{' '.join(terms)} {challenge_part}"
        return f"{query} {challenge_part}"
