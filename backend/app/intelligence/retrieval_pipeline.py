"""
EvidenRoute - Hybrid Retrieval & Evidence Scoring Pipeline
Connects Phase 1 Context Selection with Phase 2 Passage Retrieval and Evidence Scoring.

Crucial Architectural Guarantees:
1. Retrieval is strictly constrained to Phase 1 'selected' sources.
2. Skipped sources are never searched, preserving token and compute budget.
3. If Phase 1 selects zero sources, retrieval immediately terminates with an explainable trace.
4. Citations, source names, and original file paths are rigorously preserved.
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from backend.app.services.budget_manager import BudgetManager
from backend.app.schemas.budget import BudgetConfig
from .embedding_provider import BaseEmbeddingProvider, EmbeddingProvider
from .evidence_scorer import EvidenceScorer
from .conflict_detector import ConflictDetector
from .sufficiency_evaluator import SufficiencyEvaluator
from .context_pruner import ContextPruner
from .answer_readiness import AnswerReadinessEvaluator
from .counter_evidence import CounterEvidenceService
from .reliability_evaluator import EvidenceReliabilityEvaluator
from .models import (
    AnswerReadinessResult,
    ConflictDetectionResult,
    ConflictReport,
    CounterEvidenceResult,
    EvidencePassage,
    EvidenceReliabilityResult,
    EvidenceReliabilityStatus,
    EvidenceSufficiencyResult,
    PipelineDecisionTrace,
    PrunedContextResult,
    QueryAnalysisResult,
    RetrievalConfig,
    RetrievalDecisionTrace,
    SelectionConfig,
    SelectionStatus,
    SourceRankResult,
)
from .pipeline import IntelligencePipeline
from .query_analyzer import QueryAnalyzer
from .retriever import BM25Retriever
from .source_registry import BaseSourceRegistry, SourceRegistry
from .source_selector import SourceSelector
from .storage import BaseChunkStore, ChunkStore


class RetrievalPipeline:
    """
    Coordinates end-to-end evidence discovery:
    Question -> Query Analysis -> Source Selection -> Filtered Retrieval -> Evidence Scoring
    -> Conflict Detection -> Sufficiency Evaluation -> Counter-Evidence Search -> Re-evaluation
    -> Evidence Reliability -> Context Pruning -> Answer Readiness.
    """

    def __init__(
        self,
        phase1_pipeline: Optional[IntelligencePipeline] = None,
        retriever: Optional[BM25Retriever] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        evidence_scorer: Optional[EvidenceScorer] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        sufficiency_evaluator: Optional[SufficiencyEvaluator] = None,
        context_pruner: Optional[ContextPruner] = None,
        readiness_evaluator: Optional[AnswerReadinessEvaluator] = None,
        counter_evidence_service: Optional[CounterEvidenceService] = None,
        reliability_evaluator: Optional[EvidenceReliabilityEvaluator] = None,
        chunk_store: Optional[BaseChunkStore] = None,
        source_registry: Optional[BaseSourceRegistry] = None,
    ):
        self.chunk_store = chunk_store or ChunkStore
        self.source_registry = source_registry or SourceRegistry
        self.phase1_pipeline = phase1_pipeline or IntelligencePipeline(
            registry=self.source_registry
        )
        self.retriever = retriever or BM25Retriever(chunk_store=self.chunk_store)
        self.embedding_provider = embedding_provider or EmbeddingProvider
        self.evidence_scorer = evidence_scorer or EvidenceScorer()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.sufficiency_evaluator = sufficiency_evaluator or SufficiencyEvaluator()
        self.context_pruner = context_pruner or ContextPruner()
        self.readiness_evaluator = readiness_evaluator or AnswerReadinessEvaluator()
        self.counter_evidence_service = counter_evidence_service or CounterEvidenceService(
            retriever=self.retriever,
            chunk_store=self.chunk_store,
            source_registry=self.source_registry,
            evidence_scorer=self.evidence_scorer,
        )
        self.reliability_evaluator = reliability_evaluator or EvidenceReliabilityEvaluator()


    def run(
        self,
        question: str,
        top_k: int = 10,
        selection_config: Optional[SelectionConfig] = None,
        retrieval_config: Optional[RetrievalConfig] = None,
        enable_stress_test: bool = False,
        budget_manager: Optional[BudgetManager] = None,
        max_budget_calls: Optional[int] = None,
        max_budget_candidates: Optional[int] = None,
    ) -> RetrievalDecisionTrace:
        """
        Execute Phase 1 source selection followed by constrained Phase 2 retrieval and evidence ranking.
        """
        start_time = time.perf_counter()
        stages: List[str] = []
        ret_cfg = retrieval_config or RetrievalConfig(top_k=top_k)
        budget_mgr = budget_manager or BudgetManager(
            BudgetConfig(
                max_source_calls=max_budget_calls or 5,
                max_candidates=max_budget_candidates or max(20, ret_cfg.top_k * 2),
                max_tokens=15000,
            )
        )

        # -------------------------------------------------------------
        # STAGE 1 & 2: Query Analysis & Source Selection (Phase 1)
        # -------------------------------------------------------------
        phase1_trace: PipelineDecisionTrace = self.phase1_pipeline.run(
            question=question,
            config=selection_config,
        )
        stages.append(
            f"Stage 1: Analyzed query intent as '{phase1_trace.analysis.intent}' "
            f"(confidence {phase1_trace.analysis.confidence:.2f})"
        )

        selected_sources: List[SourceRankResult] = [
            s for s in phase1_trace.ranked_sources if s.selection_status == SelectionStatus.SELECTED.value
        ]
        skipped_sources: List[SourceRankResult] = [
            s for s in phase1_trace.ranked_sources if s.selection_status == SelectionStatus.SKIPPED.value
        ]

        selected_source_ids = [s.source_id for s in selected_sources]
        skipped_source_ids = [s.source_id for s in skipped_sources]

        stages.append(
            f"Stage 2: Source selection evaluated {len(phase1_trace.ranked_sources)} sources: "
            f"{len(selected_source_ids)} selected, {len(skipped_source_ids)} skipped."
        )

        # -------------------------------------------------------------
        # GUARD: Zero Selected Sources (e.g. Unrelated Query)
        # -------------------------------------------------------------
        if not selected_source_ids:
            stages.append(
                "Stage 3: Terminated retrieval early — no sources met relevance/score threshold. "
                "Preserved 100% of retrieval budget."
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            empty_sufficiency = self.sufficiency_evaluator.evaluate_sufficiency(
                query=question,
                analysis=phase1_trace.analysis,
                passages=[],
                conflicts=[],
            )
            empty_conflicts = ConflictDetectionResult(
                total_passages_evaluated=0,
                conflicts_detected_count=0,
                direct_contradictions_count=0,
                conflicts=[],
                has_unresolved_contradictions=False,
            )
            empty_pruning = self.context_pruner.prune_context(passages=[])
            empty_reliability = self.reliability_evaluator.evaluate_reliability(
                query=question,
                analysis=phase1_trace.analysis,
                passages=[],
                conflicts=[],
            )
            empty_counter = CounterEvidenceResult(
                executed=False,
                summary="Counter-evidence search bypassed: Zero sources selected.",
            )
            empty_readiness = self.readiness_evaluator.evaluate_readiness(
                sufficiency=empty_sufficiency,
                conflict_result=empty_conflicts,
                pruning_result=empty_pruning,
                reliability=empty_reliability,
                counter_evidence=empty_counter,
            )
            return RetrievalDecisionTrace(
                query=question,
                analysis=phase1_trace.analysis,
                selected_source_ids=[],
                skipped_source_ids=skipped_source_ids,
                retrieval_mode="lexical_only",
                total_candidate_chunks_evaluated=0,
                retrieved_evidence_count=0,
                retrieved_evidence=[],
                execution_time_ms=round(elapsed_ms, 2),
                budget_info={
                    "status": "budget_preserved",
                    "reason": "zero_sources_selected",
                    "chunks_scanned": 0,
                    "top_k_limit": ret_cfg.top_k,
                    "calls_consumed": 0,
                    "candidates_consumed": 0,
                    "tokens_consumed": 0,
                },
                trace_stages=stages,
                conflicts=[],
                sufficiency=empty_sufficiency,
                pruned_context=empty_pruning,
                answer_readiness=empty_readiness,
                counter_evidence=empty_counter,
                evidence_reliability=empty_reliability,
            )

        # -------------------------------------------------------------
        # STAGE 3: Constrained BM25 Keyword Retrieval
        # -------------------------------------------------------------
        # Candidate chunks pool count for metrics
        candidate_chunks = self.chunk_store.get_chunks_by_source_ids(selected_source_ids)
        total_candidate_chunks = len(candidate_chunks)

        bm25_matches = self.retriever.retrieve(
            query=question,
            selected_source_ids=selected_source_ids,
            top_k=ret_cfg.top_k * 2,  # Fetch ample candidates for scoring
        )

        # Track budget consumption for primary retrieval calls
        primary_text = " ".join(chunk.content for chunk, _, _ in bm25_matches)
        budget_mgr.commit(
            reserved_calls=0,
            reserved_candidates=0,
            reserved_tokens=0,
            actual_calls=len(selected_source_ids),
            actual_candidates=len(bm25_matches),
            actual_tokens=BudgetManager.estimate_tokens(primary_text),
        )

        stages.append(
            f"Stage 3: Scanned {total_candidate_chunks} passages across {len(selected_source_ids)} "
            f"selected sources; retrieved {len(bm25_matches)} lexical candidates."
        )

        # -------------------------------------------------------------
        # STAGE 4: Semantic Provider Check & Hybrid Combination
        # -------------------------------------------------------------
        is_hybrid = ret_cfg.enable_semantic and self.embedding_provider.is_enabled()
        retrieval_mode = "hybrid" if is_hybrid else "lexical_only"

        candidate_list = [c for c, _, _ in bm25_matches]
        semantic_scores: Optional[List[float]] = None

        if is_hybrid and candidate_list:
            semantic_scores = self.embedding_provider.compute_similarity(
                query=question, chunks=candidate_list
            )
            stages.append("Stage 4: Computed local Sentence Transformers dense cosine similarity.")
        else:
            stages.append("Stage 4: Semantic provider disabled/offline; using pure lexical retrieval.")

        # -------------------------------------------------------------
        # STAGE 5: Multi-Dimensional Evidence Scoring
        # -------------------------------------------------------------
        scored_evidence: List[EvidencePassage] = []

        # Source name lookup map
        source_name_map = {
            s.source_id: s.source_name for s in self.source_registry.list_sources()
        }

        for idx, (chunk, raw_bm25, norm_bm25) in enumerate(bm25_matches):
            sem_score = semantic_scores[idx] if semantic_scores else None

            # Calculate composite retrieval relevance
            if is_hybrid and sem_score is not None:
                combined_relevance = (
                    ret_cfg.bm25_weight * norm_bm25 + ret_cfg.semantic_weight * sem_score
                )
            else:
                combined_relevance = norm_bm25

            # Compute evidence score across Relevance, Authority, Freshness, Directness
            ev_score = self.evidence_scorer.score_evidence(
                chunk=chunk,
                retrieval_score=combined_relevance,
                query_analysis=phase1_trace.analysis,
                config=ret_cfg.evidence_config,
            )

            # Generate formal citation
            source_name = source_name_map.get(chunk.source_id, chunk.source_id)
            file_name = Path(chunk.original_file_path).name if chunk.original_file_path else "source"
            citation = (
                f"[{source_name} ({chunk.source_id}) § Chunk {chunk.chunk_index}, "
                f"File: {file_name}, Record: {chunk.record_id}]"
            )

            scored_evidence.append(
                EvidencePassage(
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
                    retrieval_score=round(combined_relevance, 4),
                    bm25_score=round(raw_bm25, 4),
                    semantic_score=round(sem_score, 4) if sem_score is not None else None,
                    retrieval_mode=retrieval_mode,
                    evidence_score=ev_score,
                    citation=citation,
                    ranking_position=0,  # Assigned after sort
                )
            )

        # -------------------------------------------------------------
        # STAGE 6: Ranking & Top-K Truncation
        # -------------------------------------------------------------
        scored_evidence.sort(
            key=lambda x: (
                x.evidence_score.final_evidence_score,
                x.evidence_score.relevance_score,
                x.authority_level,
            ),
            reverse=True,
        )

        final_evidence: List[EvidencePassage] = []
        for rank_pos, ev in enumerate(scored_evidence[: ret_cfg.top_k], start=1):
            ev.ranking_position = rank_pos
            final_evidence.append(ev)

        stages.append(
            f"Stage 5: Scored {len(scored_evidence)} evidence passages; ranked and selected top {len(final_evidence)}."
        )

        # -------------------------------------------------------------
        # STAGE 6: Conflict Detection
        # -------------------------------------------------------------
        conflict_res = self.conflict_detector.detect_conflicts(final_evidence)

        # Compute meaningful Correctness factor based on conflict detection & source corroboration
        unique_sources_in_set = {p.source_id for p in final_evidence}
        critical_chunk_ids = set()
        divergent_chunk_ids = set()
        for c in conflict_res.conflicts:
            for pref in c.conflicting_passages:
                if c.severity in ("critical", "high"):
                    critical_chunk_ids.add(pref.chunk_id)
                else:
                    divergent_chunk_ids.add(pref.chunk_id)

        for ev in final_evidence:
            if ev.chunk_id in critical_chunk_ids:
                ev.evidence_score.correctness_score = 0.20
                ev.evidence_score.correctness_status = "contradicted"
                ev.evidence_score.correctness_explanation = "Direct factual contradiction flagged against other evidence."
            elif ev.chunk_id in divergent_chunk_ids:
                ev.evidence_score.correctness_score = 0.70
                ev.evidence_score.correctness_status = "temporally_updated"
                ev.evidence_score.correctness_explanation = "Temporal revision or policy evolution noted between sources."
            elif len(unique_sources_in_set) >= 2 and ev.evidence_score.relevance_score >= 0.40:
                ev.evidence_score.correctness_score = 0.95
                ev.evidence_score.correctness_status = "cross_verified"
                ev.evidence_score.correctness_explanation = "Cross-verified across multiple independent retrieved sources."
            elif ev.authority_level >= 0.85:
                ev.evidence_score.correctness_score = 0.90
                ev.evidence_score.correctness_status = "consistent"
                ev.evidence_score.correctness_explanation = "Consistent with official authoritative repository records."
            else:
                ev.evidence_score.correctness_score = 0.65
                ev.evidence_score.correctness_status = "unverified_single_source"
                ev.evidence_score.correctness_explanation = "Single-source observation awaiting independent corroboration."
        stages.append(
            f"Stage 6: Evaluated {len(final_evidence)} passages for conflicts: "
            f"detected {conflict_res.conflicts_detected_count} total divergence(s), "
            f"{conflict_res.direct_contradictions_count} direct contradiction(s)."
        )

        # -------------------------------------------------------------
        # STAGE 7: Evidence Sufficiency Evaluation
        # -------------------------------------------------------------
        sufficiency_res = self.sufficiency_evaluator.evaluate_sufficiency(
            query=question,
            analysis=phase1_trace.analysis,
            passages=final_evidence,
            conflicts=conflict_res.conflicts,
        )
        stages.append(
            f"Stage 7: Evaluated evidence sufficiency: score {sufficiency_res.sufficiency_score:.2f} "
            f"({sufficiency_res.sufficiency_status}), recommended action '{sufficiency_res.recommended_action}'."
        )

        # -------------------------------------------------------------
        # STAGE 8: Bounded Counter-Evidence Search & Re-Evaluation
        # -------------------------------------------------------------
        counter_res = CounterEvidenceResult(
            executed=False,
            summary="Counter-evidence search was not requested or was bypassed.",
        )
        challenge_passages: List[EvidencePassage] = []

        if enable_stress_test and sufficiency_res.recommended_action == "answer":
            counter_res, challenge_passages = self.counter_evidence_service.search_counter_evidence(
                query=question,
                analysis=phase1_trace.analysis,
                initial_evidence=final_evidence,
                selected_source_ids=selected_source_ids,
                budget_manager=budget_mgr,
                max_candidates=3,
                evidence_config=ret_cfg.evidence_config,
            )
            if challenge_passages:
                final_evidence.extend(challenge_passages)
                final_evidence.sort(
                    key=lambda x: (
                        x.evidence_score.final_evidence_score,
                        x.evidence_score.relevance_score,
                        x.authority_level,
                    ),
                    reverse=True,
                )
                final_evidence = final_evidence[: ret_cfg.top_k]
                for rank_pos, ev in enumerate(final_evidence, start=1):
                    ev.ranking_position = rank_pos
                # Re-evaluate conflicts across combined set
                conflict_res = self.conflict_detector.detect_conflicts(final_evidence)

        # Compute meaningful Correctness factor based on conflict detection & source corroboration
        unique_sources_in_set = {p.source_id for p in final_evidence}
        critical_chunk_ids = set()
        divergent_chunk_ids = set()
        for c in conflict_res.conflicts:
            for pref in c.conflicting_passages:
                if c.severity in ("critical", "high"):
                    critical_chunk_ids.add(pref.chunk_id)
                else:
                    divergent_chunk_ids.add(pref.chunk_id)

        for ev in final_evidence:
            if ev.chunk_id in critical_chunk_ids:
                ev.evidence_score.correctness_score = 0.20
                ev.evidence_score.correctness_status = "contradicted"
                ev.evidence_score.correctness_explanation = "Direct factual contradiction flagged against other evidence."
            elif ev.chunk_id in divergent_chunk_ids:
                ev.evidence_score.correctness_score = 0.70
                ev.evidence_score.correctness_status = "temporally_updated"
                ev.evidence_score.correctness_explanation = "Temporal revision or policy evolution noted between sources."
            elif len(unique_sources_in_set) >= 2 and ev.evidence_score.relevance_score >= 0.40:
                ev.evidence_score.correctness_score = 0.95
                ev.evidence_score.correctness_status = "cross_verified"
                ev.evidence_score.correctness_explanation = "Cross-verified across multiple independent retrieved sources."
            elif ev.authority_level >= 0.85:
                ev.evidence_score.correctness_score = 0.90
                ev.evidence_score.correctness_status = "consistent"
                ev.evidence_score.correctness_explanation = "Consistent with official authoritative repository records."
            else:
                ev.evidence_score.correctness_score = 0.65
                ev.evidence_score.correctness_status = "unverified_single_source"
                ev.evidence_score.correctness_explanation = "Single-source observation awaiting independent corroboration."
                # Re-evaluate sufficiency
                sufficiency_res = self.sufficiency_evaluator.evaluate_sufficiency(
                    query=question,
                    analysis=phase1_trace.analysis,
                    passages=final_evidence,
                    conflicts=conflict_res.conflicts,
                )
            stages.append(
                f"Stage 8: Counter-evidence search ({counter_res.impact_on_decision}): "
                f"retrieved {len(challenge_passages)} passage(s), counter-evidence found: {counter_res.counter_evidence_found}."
            )

            # STAGE 9: Holistic Evidence Reliability Assessment
            reliability_res = self.reliability_evaluator.evaluate_reliability(
                query=question,
                analysis=phase1_trace.analysis,
                passages=final_evidence,
                conflicts=conflict_res.conflicts,
                counter_evidence=counter_res,
            )
            stages.append(
                f"Stage 9: Evidence reliability evaluated: status '{reliability_res.status}', "
                f"score {reliability_res.reliability_score:.2f}, independent sources {reliability_res.independent_sources_count}."
            )

            # STAGE 10: Budget-Aware Context Pruning
            pruned_res = self.context_pruner.prune_context(
                passages=final_evidence,
                conflicts=conflict_res.conflicts,
            )
            stages.append(
                f"Stage 10: Context pruning: deduplicated {pruned_res.pruned_sentence_count} redundant sentences, "
                f"preserved {pruned_res.conflict_passages_preserved_count} conflict passage(s), "
                f"compression ratio {pruned_res.compression_ratio:.2f}."
            )

            # STAGE 11: Final Answer Readiness Decision
            readiness_res = self.readiness_evaluator.evaluate_readiness(
                sufficiency=sufficiency_res,
                conflict_result=conflict_res,
                pruning_result=pruned_res,
                reliability=reliability_res,
                counter_evidence=counter_res,
            )
            stages.append(
                f"Stage 11: Answer readiness verdict: {readiness_res.readiness_verdict} "
                f"(cleared to answer: {readiness_res.is_ready_to_answer})."
            )
        else:
            # Baseline / Phase 3 workflow when stress testing is disabled
            reliability_res = self.reliability_evaluator.evaluate_reliability(
                query=question,
                analysis=phase1_trace.analysis,
                passages=final_evidence,
                conflicts=conflict_res.conflicts,
                counter_evidence=counter_res,
            )
            pruned_res = self.context_pruner.prune_context(
                passages=final_evidence,
                conflicts=conflict_res.conflicts,
            )
            stages.append(
                f"Stage 8: Context pruning: deduplicated {pruned_res.pruned_sentence_count} redundant sentences, "
                f"preserved {pruned_res.conflict_passages_preserved_count} conflict passage(s), "
                f"compression ratio {pruned_res.compression_ratio:.2f}."
            )
            readiness_res = self.readiness_evaluator.evaluate_readiness(
                sufficiency=sufficiency_res,
                conflict_result=conflict_res,
                pruning_result=pruned_res,
                reliability=reliability_res,
                counter_evidence=counter_res,
            )
            stages.append(
                f"Stage 9: Answer readiness verdict: {readiness_res.readiness_verdict} "
                f"(cleared to answer: {readiness_res.is_ready_to_answer})."
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        budget_info = {
            "status": "completed",
            "top_k_limit": ret_cfg.top_k,
            "passages_returned": len(final_evidence),
            "total_candidates_scanned": total_candidate_chunks,
            "skipped_sources_filtered": len(skipped_source_ids),
            "calls_consumed": budget_mgr.calls_consumed,
            "candidates_consumed": budget_mgr.candidates_consumed,
            "tokens_consumed": budget_mgr.tokens_consumed,
        }

        return RetrievalDecisionTrace(
            query=question,
            analysis=phase1_trace.analysis,
            selected_source_ids=selected_source_ids,
            skipped_source_ids=skipped_source_ids,
            retrieval_mode=retrieval_mode,
            total_candidate_chunks_evaluated=total_candidate_chunks,
            retrieved_evidence_count=len(final_evidence),
            retrieved_evidence=final_evidence,
            execution_time_ms=round(elapsed_ms, 2),
            budget_info=budget_info,
            trace_stages=stages,
            conflicts=conflict_res.conflicts,
            sufficiency=sufficiency_res,
            pruned_context=pruned_res,
            answer_readiness=readiness_res,
            counter_evidence=counter_res,
            evidence_reliability=reliability_res,
        )
