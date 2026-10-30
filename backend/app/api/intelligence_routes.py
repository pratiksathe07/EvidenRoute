"""
EvidenRoute - Intelligence API Routes
REST API endpoints for query understanding, source ranking,
knowledge ingestion, hybrid retrieval, and evidence scoring.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from ..core.config import settings
from ..intelligence import (
    ChunkStore,
    ConflictDetector,
    ContextPruner,
    DocumentChunker,
    EmbeddingProvider,
    EvidenceScorer,
    IngestionReport,
    IngestionService,
    IntelligencePipeline,
    QueryAnalysisResult,
    QueryAnalyzer,
    RetrievalPipeline,
    SourceMetadata,
    SourceRegistry,
    SourceSelector,
    SufficiencyEvaluator,
    AnswerReadinessEvaluator,
)
from ..intelligence.models import (
    AnalyzeQueryRequest,
    ConflictDetectionResult,
    DetectConflictsRequest,
    EvaluateEvidenceRequest,
    EvaluateEvidenceResponse,
    HealthResponse,
    PlanRequest,
    PlanResponse,
    PruneContextRequest,
    PrunedContextResult,
    RetrievalHealthResponse,
    RetrieveRequest,
    RetrieveResponse,
    SelectSourcesRequest,
    SelectSourcesResponse,
)

router = APIRouter()

# Instantiate shared singletons
analyzer = QueryAnalyzer()
selector = SourceSelector()
pipeline = IntelligencePipeline(analyzer=analyzer, registry=SourceRegistry, selector=selector)
ingestion_service = IngestionService(chunk_store=ChunkStore, source_registry=SourceRegistry)
conflict_detector = ConflictDetector()
sufficiency_evaluator = SufficiencyEvaluator()
context_pruner = ContextPruner()
readiness_evaluator = AnswerReadinessEvaluator()
retrieval_pipeline = RetrievalPipeline(
    phase1_pipeline=pipeline,
    chunk_store=ChunkStore,
    source_registry=SourceRegistry,
    embedding_provider=EmbeddingProvider,
    conflict_detector=conflict_detector,
    sufficiency_evaluator=sufficiency_evaluator,
    context_pruner=context_pruner,
    readiness_evaluator=readiness_evaluator,
)

# Cache last ingestion report
_last_ingestion_report: Optional[IngestionReport] = None


def ensure_initial_ingestion():
    """Ensure data files are indexed at startup if store is empty."""
    global _last_ingestion_report
    if ChunkStore.count() == 0:
        try:
            _last_ingestion_report = ingestion_service.run_ingestion()
        except Exception:
            pass


# Pre-populate on module load
ensure_initial_ingestion()


# ==============================================================
# PHASE 1 ENDPOINTS (PRESERVED)
# ==============================================================

@router.post(
    "/analyze-query",
    response_model=QueryAnalysisResult,
    summary="Analyze query intent and extract metadata",
    description="Deterministic local query analyzer extracting intent, keywords, entities, and likely sources."
)
async def analyze_query(payload: AnalyzeQueryRequest) -> QueryAnalysisResult:
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query question cannot be empty or whitespace only."
        )
    return analyzer.analyze(payload.question)


@router.post(
    "/select-sources",
    response_model=SelectSourcesResponse,
    summary="Rank and select relevant sources",
    description="Ranks registered sources using multi-factor explainable scoring without retrieving records."
)
async def select_sources(payload: SelectSourcesRequest) -> SelectSourcesResponse:
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query question cannot be empty or whitespace only."
        )

    analysis = analyzer.analyze(payload.question)
    candidate_sources = payload.sources if payload.sources is not None else SourceRegistry.list_sources()

    ranked = selector.rank_and_select(
        analysis=analysis,
        sources=candidate_sources,
        config=payload.config,
    )

    selected_count = sum(1 for s in ranked if s.selection_status == "selected")
    skipped_count = len(ranked) - selected_count

    return SelectSourcesResponse(
        question=payload.question,
        selected_sources_count=selected_count,
        skipped_sources_count=skipped_count,
        ranked_sources=ranked,
    )


@router.post(
    "/plan",
    response_model=PlanResponse,
    summary="Full context selection plan and audit trace",
    description="Connects Query Analyzer -> Source Registry -> Source Selector and returns complete decision trace."
)
async def plan_context_selection(payload: PlanRequest) -> PlanResponse:
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query question cannot be empty or whitespace only."
        )

    trace = pipeline.run(
        question=payload.question,
        config=payload.config,
    )

    return PlanResponse(decision_trace=trace)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health and component status",
    description="Reports the operational status of the backend, local intelligence modules, and source registry."
)
async def health_check() -> HealthResponse:
    all_sources = SourceRegistry.list_sources()
    active_count = sum(1 for s in all_sources if s.availability)

    return HealthResponse(
        status="operational",
        query_analyzer="ready (deterministic_rule_based)",
        source_registry=f"ready ({len(all_sources)} sources registered)",
        source_selector="ready (multi_factor_explainable)",
        external_llm_integration="not configured (local-first Phase 1)",
        active_sources_count=active_count,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/sources",
    response_model=List[SourceMetadata],
    summary="List all registered sources",
    description="Inspect all candidate knowledge sources and their current metadata/availability."
)
async def list_sources() -> List[SourceMetadata]:
    return SourceRegistry.list_sources()


# ==============================================================
# PHASE 2 ENDPOINTS: INGESTION, RETRIEVAL & EVIDENCE SCORING
# ==============================================================

@router.post(
    "/ingest",
    response_model=IngestionReport,
    summary="Trigger local data ingestion",
    description="Scans data/ directories, chunks markdown documents, transcripts, and tickets into normalized passages."
)
async def trigger_ingestion() -> IngestionReport:
    global _last_ingestion_report
    report = ingestion_service.run_ingestion(clear_existing=True)
    _last_ingestion_report = report
    return report


@router.get(
    "/ingestion-status",
    summary="Get current chunk ingestion statistics",
    description="Returns current total stored chunks, records, and last ingestion metadata."
)
async def get_ingestion_status() -> Dict[str, Any]:
    return {
        "status": "ready" if ChunkStore.count() > 0 else "empty",
        "total_chunks_indexed": ChunkStore.count(),
        "last_report": _last_ingestion_report.model_dump() if _last_ingestion_report else None,
    }


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    summary="End-to-end Context Selection, Retrieval & Evidence Scoring",
    description="Executes Phase 1 source selection, retrieves passages exclusively from selected sources, and scores evidence."
)
async def retrieve_evidence(payload: RetrieveRequest) -> RetrieveResponse:
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query question cannot be empty or whitespace only."
        )

    # Ensure repository is populated
    if ChunkStore.count() == 0:
        ensure_initial_ingestion()

    trace = retrieval_pipeline.run(
        question=payload.question,
        top_k=payload.top_k,
        selection_config=payload.selection_config,
        retrieval_config=payload.retrieval_config,
    )

    return RetrieveResponse(
        query=payload.question,
        query_analysis=trace.analysis,
        selected_sources=trace.selected_source_ids,
        skipped_sources=trace.skipped_source_ids,
        retrieval_mode=trace.retrieval_mode,
        retrieved_evidence=trace.retrieved_evidence,
        decision_trace=trace,
        conflicts=trace.conflicts,
        sufficiency=trace.sufficiency,
        pruned_context=trace.pruned_context,
        answer_readiness=trace.answer_readiness,
    )


@router.get(
    "/retrieval-health",
    response_model=RetrievalHealthResponse,
    summary="Retrieval and Evidence Scoring Health Check",
    description="Reports diagnostic status of Ingestion, BM25, Semantic Provider, and Evidence Scorer."
)
async def retrieval_health() -> RetrievalHealthResponse:
    emb_status = EmbeddingProvider.get_status()
    chunk_count = ChunkStore.count()

    return RetrievalHealthResponse(
        status="operational",
        ingestion_status={
            "total_chunks_indexed": chunk_count,
            "status": "indexed" if chunk_count > 0 else "pending_ingestion",
        },
        bm25_status="ready (rank_bm25 / fallback)",
        semantic_model_status=emb_status,
        active_retrieval_mode="hybrid" if emb_status.get("is_enabled") else "lexical_only",
        evidence_scorer_status="ready (4-dimension explainable scoring)",
    )


# ==============================================================
# PHASE 3 ENDPOINTS: CONFLICTS, SUFFICIENCY & PRUNING
# ==============================================================

@router.post(
    "/detect-conflicts",
    response_model=ConflictDetectionResult,
    summary="Factual Conflict and Divergence Detection",
    description="Detects direct contradictions, temporal updates, version divergences, and status changes across evidence."
)
async def detect_conflicts_endpoint(payload: DetectConflictsRequest) -> ConflictDetectionResult:
    if payload.passages is not None:
        passages = payload.passages
    elif payload.question and payload.question.strip():
        if ChunkStore.count() == 0:
            ensure_initial_ingestion()
        trace = retrieval_pipeline.run(question=payload.question)
        passages = trace.retrieved_evidence
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'passages' list or a non-empty 'question' must be provided."
        )
    return conflict_detector.detect_conflicts(passages)


@router.post(
    "/evaluate-evidence",
    response_model=EvaluateEvidenceResponse,
    summary="Evidence Sufficiency and Readiness Evaluation",
    description="Evaluates whether retrieved evidence suffices to answer the question, detects conflicts, and determines answer readiness."
)
async def evaluate_evidence_endpoint(payload: EvaluateEvidenceRequest) -> EvaluateEvidenceResponse:
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query question cannot be empty or whitespace only."
        )

    if ChunkStore.count() == 0:
        ensure_initial_ingestion()

    if payload.passages is not None:
        analysis = analyzer.analyze(payload.question)
        passages = payload.passages
        conflicts_res = conflict_detector.detect_conflicts(passages)
        sufficiency_res = sufficiency_evaluator.evaluate_sufficiency(
            query=payload.question,
            analysis=analysis,
            passages=passages,
            conflicts=conflicts_res.conflicts,
        )
        pruned_res = context_pruner.prune_context(
            passages=passages,
            conflicts=conflicts_res.conflicts,
        )
        readiness_res = readiness_evaluator.evaluate_readiness(
            sufficiency=sufficiency_res,
            conflict_result=conflicts_res,
            pruning_result=pruned_res,
        )
        return EvaluateEvidenceResponse(
            question=payload.question,
            sufficiency=sufficiency_res,
            readiness=readiness_res,
            conflicts=conflicts_res.conflicts,
            pruned_context=pruned_res,
        )

    # Full retrieval pipeline execution
    trace = retrieval_pipeline.run(question=payload.question, top_k=payload.top_k)
    return EvaluateEvidenceResponse(
        question=payload.question,
        sufficiency=trace.sufficiency,
        readiness=trace.answer_readiness,
        conflicts=trace.conflicts,
        pruned_context=trace.pruned_context,
    )


@router.post(
    "/prune-context",
    response_model=PrunedContextResult,
    summary="Budget-Aware Context Pruning",
    description="Deduplicates redundant sentences and compresses context while strictly preserving citations and conflict evidence."
)
async def prune_context_endpoint(payload: PruneContextRequest) -> PrunedContextResult:
    return context_pruner.prune_context(
        passages=payload.passages,
        conflicts=payload.conflicts,
        max_context_chars=payload.max_context_chars,
    )

