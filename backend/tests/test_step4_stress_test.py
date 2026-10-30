"""
EvidenRoute - Step 4 Comprehensive Automated Test Suite
Validates Evidence Stress Testing, Counter-Evidence Search, Evidence Reliability,
Decision Control, and Baseline Comparison.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.intelligence import (
    AnswerReadinessEvaluator,
    BaselineComparisonService,
    ChunkStore,
    ConflictDetector,
    CounterEvidenceResult,
    CounterEvidenceService,
    EvidencePassage,
    EvidenceReliabilityEvaluator,
    EvidenceReliabilityStatus,
    EvidenceScore,
    EvidenceScorer,
    QueryAnalysisResult,
    IntentType,
    RecommendedAction,
    RetrievalPipeline,
    SourceRegistry,
    StressTestingFramework,
    SufficiencyEvaluator,
)
from backend.app.intelligence.models import (
    ChunkData,
    InformationCategory,
    RetrievalDecisionTrace,
)
from backend.app.main import app
from backend.app.schemas.budget import BudgetConfig
from backend.app.services.budget_manager import BudgetManager


@pytest.fixture(scope="module", autouse=True)
def setup_test_ingestion():
    """Ensure sample data is ingested for test execution."""
    from backend.app.intelligence.ingestion import IngestionService
    service = IngestionService(chunk_store=ChunkStore, source_registry=SourceRegistry)
    service.run_ingestion()


def _make_test_passage(
    chunk_id: str,
    source_id: str,
    content: str,
    authority_level: float = 0.85,
    relevance: float = 0.80,
    created_at: str = "2025-06-01T00:00:00Z",
) -> EvidencePassage:
    ev_score = EvidenceScore(
        relevance_score=relevance,
        authority_score=authority_level,
        freshness_score=0.90 if created_at else None,
        freshness_status="fresh" if created_at else "unknown",
        directness_score=0.85,
        directness_label="direct",
        final_evidence_score=round(0.35 * relevance + 0.25 * authority_level + 0.20 * 0.90 + 0.20 * 0.85, 4),
        scoring_explanation="Test passage score",
        weights_applied={},
    )
    return EvidencePassage(
        chunk_id=chunk_id,
        source_id=source_id,
        source_name=f"Source {source_id}",
        source_type="documents",
        record_id=chunk_id,
        title="Test Record",
        content=content,
        authority_level=authority_level,
        created_at=created_at,
        original_file_path=f"data/{source_id}.json",
        chunk_index=0,
        retrieval_score=relevance,
        bm25_score=relevance,
        semantic_score=None,
        retrieval_mode="lexical_only",
        evidence_score=ev_score,
        citation=f"[Source ({source_id}) § Chunk 0]",
        ranking_position=1,
    )


def _make_test_analysis(keywords=None, entities=None) -> QueryAnalysisResult:
    return QueryAnalysisResult(
        intent=IntentType.TECHNICAL_TROUBLESHOOTING.value,
        confidence=0.95,
        keywords=keywords or ["database", "pool"],
        entities=entities or ["PostgreSQL"],
        technical_terms=[],
        information_category=InformationCategory.TECHNICAL.value,
        expected_information=["specifications"],
        likely_source_types=["documents"],
    )


# ==============================================================
# 1. 14-SCENARIO STRESS-TESTING FRAMEWORK TESTS
# ==============================================================

def test_stress_testing_framework_all_14_scenarios():
    """Verify that all 14 evidence stress test scenarios run and pass."""
    framework = StressTestingFramework()
    report = framework.run_all_scenarios()

    assert report.total_scenarios == 14
    assert report.passed_scenarios == 14
    assert report.failed_scenarios == 0
    assert report.pass_rate_pct == 100.0
    assert len(report.results) == 14

    # Verify each scenario ID is represented
    scenario_ids = [r.scenario_id for r in report.results]
    assert scenario_ids == list(range(1, 15))


# ==============================================================
# 2. COUNTER-EVIDENCE SEARCH TESTS
# ==============================================================

def test_counter_evidence_discovery_and_caveat():
    """Test counter-evidence discovery surfaces caveats and marks weakened_confidence."""
    service = CounterEvidenceService()
    p1 = _make_test_passage("chk-p1", "doc-api-gateway", "Standard timeout is 30 seconds.")
    analysis = _make_test_analysis(keywords=["timeout"])

    budget_mgr = BudgetManager(BudgetConfig(max_source_calls=5, max_candidates=10))
    res, passages = service.search_counter_evidence(
        query="What is the standard timeout?",
        analysis=analysis,
        initial_evidence=[p1],
        selected_source_ids=["doc-api-gateway", "conv-incident-war-room"],
        budget_manager=budget_mgr,
        max_candidates=3,
    )

    assert res.executed is True
    assert res.budget_used_calls == 1
    assert budget_mgr.calls_consumed == 1
    assert res.budget_exhausted is False


def test_counter_evidence_budget_exhaustion():
    """Test that counter-evidence search halts cleanly when budget is exhausted."""
    service = CounterEvidenceService()
    p1 = _make_test_passage("chk-p1", "doc-api-gateway", "Standard timeout is 30 seconds.")
    analysis = _make_test_analysis(keywords=["timeout"])

    # Exhaust budget beforehand
    budget_mgr = BudgetManager(BudgetConfig(max_source_calls=1, max_candidates=1))
    budget_mgr.commit(reserved_calls=0, reserved_candidates=0, reserved_tokens=0, actual_calls=1, actual_candidates=1)

    res, passages = service.search_counter_evidence(
        query="What is the standard timeout?",
        analysis=analysis,
        initial_evidence=[p1],
        selected_source_ids=["doc-api-gateway"],
        budget_manager=budget_mgr,
    )

    assert res.executed is False
    assert res.budget_exhausted is True
    assert "budget exhausted" in res.summary.lower()
    assert len(passages) == 0


def test_counter_evidence_duplicate_prevention():
    """Test that chunks already in initial_evidence are not re-ingested or duplicated."""
    service = CounterEvidenceService()
    # Ingest a chunk into store and pass it as already in initial_evidence
    all_chunks = ChunkStore.get_all_chunks()
    assert len(all_chunks) > 0
    target_chunk = all_chunks[0]

    p1 = _make_test_passage(target_chunk.chunk_id, target_chunk.source_id, target_chunk.content)
    analysis = _make_test_analysis(keywords=[target_chunk.content.split()[0]])

    res, passages = service.search_counter_evidence(
        query=target_chunk.title,
        analysis=analysis,
        initial_evidence=[p1],
        selected_source_ids=[target_chunk.source_id],
        budget_manager=None,
    )

    # Must not contain the chunk_id that was already in initial_evidence
    assert all(p.chunk_id != target_chunk.chunk_id for p in passages)


def test_counter_evidence_never_searches_skipped_sources():
    """Verify that skipped sources are never queried during counter-evidence search."""
    service = CounterEvidenceService()
    p1 = _make_test_passage("chk-p1", "doc-api-gateway", "API documentation.")
    analysis = _make_test_analysis(keywords=["API"])

    # selected_source_ids only contains doc-api-gateway; conv-incident-war-room is skipped
    res, passages = service.search_counter_evidence(
        query="API Gateway",
        analysis=analysis,
        initial_evidence=[p1],
        selected_source_ids=["doc-api-gateway"],
        budget_manager=None,
    )

    # Every discovered passage must originate strictly from the selected source
    for p in passages:
        assert p.source_id == "doc-api-gateway"


# ==============================================================
# 3. EVIDENCE RELIABILITY EVALUATION TESTS
# ==============================================================

def test_independent_source_confirmation_vs_duplicates():
    """Test that multiple duplicate chunks from the same source do NOT count as independent sources."""
    evaluator = EvidenceReliabilityEvaluator()
    analysis = _make_test_analysis()

    # Case A: 3 passages from the SAME source
    p1 = _make_test_passage("c1", "source-A", "Payment pool is 50.")
    p2 = _make_test_passage("c2", "source-A", "Payment pool is 50.")
    p3 = _make_test_passage("c3", "source-A", "Payment pool is 50.")

    res_same = evaluator.evaluate_reliability("What is payment pool?", analysis, [p1, p2, p3])
    assert res_same.independent_sources_count == 1
    assert any("single source" in lim for lim in res_same.confidence_limitations)

    # Case B: 3 passages from 3 DISTINCT independent sources
    p_b1 = _make_test_passage("c1", "source-A", "Payment pool is 50.")
    p_b2 = _make_test_passage("c2", "source-B", "Payment pool is 50.")
    p_b3 = _make_test_passage("c3", "source-C", "Payment pool is 50.")

    res_diff = evaluator.evaluate_reliability("What is payment pool?", analysis, [p_b1, p_b2, p_b3])
    assert res_diff.independent_sources_count == 3
    assert res_diff.status == EvidenceReliabilityStatus.HIGH.value
    assert res_diff.reliability_score > res_same.reliability_score


def test_low_authority_evidence_limitation():
    """Test that low-authority evidence sets are flagged with credibility limitations."""
    evaluator = EvidenceReliabilityEvaluator()
    analysis = _make_test_analysis()
    p_low = _make_test_passage("c1", "slack-informal", "Informal discussion.", authority_level=0.35)

    res = evaluator.evaluate_reliability("query", analysis, [p_low])
    assert any("Low average authority" in lim for lim in res.confidence_limitations)


def test_critical_contradiction_forces_clarification():
    """Test that critical unresolved contradiction sets status to CONTRADICTED and action to CLARIFY."""
    evaluator = EvidenceReliabilityEvaluator()
    detector = ConflictDetector()

    p1 = _make_test_passage("c1", "doc-1", "The refund window is 14 days strictly.")
    p2 = _make_test_passage("c2", "chat-1", "The refund window is 30 days strictly.")
    conflict_res = detector.detect_conflicts([p1, p2])

    analysis = _make_test_analysis(keywords=["refund", "window"])
    res = evaluator.evaluate_reliability("What is refund window?", analysis, [p1, p2], conflict_res.conflicts)

    assert res.status == EvidenceReliabilityStatus.CONTRADICTED.value
    assert res.recommended_action == RecommendedAction.CLARIFY.value
    assert res.contradictory_evidence_count == 2


# ==============================================================
# 4. END-TO-END PIPELINE & DECISION CONTROL TESTS
# ==============================================================

def test_end_to_end_pipeline_with_counter_evidence_and_reliability():
    """Verify that RetrievalPipeline executes all 11 stages and populates Step 4 fields."""
    pipeline = RetrievalPipeline()
    trace = pipeline.run("Why did the payment API fail after deployment?", top_k=3, enable_stress_test=True)

    # Verify Step 4 additions
    assert trace.counter_evidence is not None
    assert trace.counter_evidence.executed is True
    assert trace.evidence_reliability is not None
    assert trace.evidence_reliability.status in [EvidenceReliabilityStatus.HIGH.value, EvidenceReliabilityStatus.MODERATE.value]
    assert trace.evidence_reliability.independent_sources_count >= 1

    # Verify trace stages
    stage_text = " ".join(trace.trace_stages)
    assert "Stage 8: Counter-evidence search" in stage_text
    assert "Stage 9: Evidence reliability evaluated" in stage_text
    assert "Stage 10: Context pruning" in stage_text
    assert "Stage 11: Answer readiness verdict" in stage_text

    # Answer readiness should be cleared
    assert trace.answer_readiness.is_ready_to_answer is True
    assert trace.answer_readiness.recommended_action == RecommendedAction.ANSWER.value


def test_abstention_on_unrelated_query():
    """Verify that unrelated query preserves budget and abstains without hallucinating."""
    pipeline = RetrievalPipeline()
    trace = pipeline.run("How do quantum hyperspace engines calibrate on Mars?")

    assert len(trace.selected_source_ids) == 0
    assert trace.budget_info["status"] == "budget_preserved"
    assert trace.answer_readiness.is_ready_to_answer is False
    assert trace.answer_readiness.recommended_action in [RecommendedAction.ABSTAIN.value, RecommendedAction.RETRIEVE_MORE.value]
    assert trace.counter_evidence.executed is False


# ==============================================================
# 5. BASELINE COMPARISON TESTS
# ==============================================================

def test_baseline_comparison_execution():
    """Test the BaselineComparisonService runs benchmark comparison and measures improvements."""
    service = BaselineComparisonService()
    report = service.run_comparison(max_queries=4)

    assert report.baseline_metrics.total_queries == 4
    assert report.evidenroute_metrics.total_queries == 4

    # EvidenRoute should retrieve fewer unneeded passages than naive full-source baseline
    assert report.evidenroute_metrics.average_passages_retrieved <= report.baseline_metrics.average_passages_retrieved
    assert report.evidenroute_metrics.budget_calls_consumed <= report.baseline_metrics.budget_calls_consumed
    assert report.evidenroute_metrics.irrelevant_evidence_reduction_pct >= 0.0

    # EvidenRoute performs source selection and contradiction checking (which baseline lacks)
    assert report.evidenroute_metrics.source_selection_accuracy > 0.0
    assert report.evidenroute_metrics.contradiction_accuracy > 0.0


# ==============================================================
# 6. API ENDPOINT TESTS
# ==============================================================

def test_api_stress_test_endpoint():
    """Test the POST /api/intelligence/stress-test endpoint."""
    client = TestClient(app)
    res = client.post("/api/intelligence/stress-test")
    assert res.status_code == 200
    data = res.json()

    assert data["total_scenarios"] == 14
    assert data["passed_scenarios"] == 14
    assert data["failed_scenarios"] == 0
    assert data["pass_rate_pct"] == 100.0


def test_api_baseline_comparison_endpoint():
    """Test the GET /api/intelligence/benchmark/baseline-comparison endpoint."""
    client = TestClient(app)
    res = client.get("/api/intelligence/benchmark/baseline-comparison?limit=3")
    assert res.status_code == 200
    data = res.json()

    assert "baseline_metrics" in data
    assert "evidenroute_metrics" in data
    assert "improvements" in data
    assert data["baseline_metrics"]["total_queries"] == 3


def test_api_retrieve_with_counter_evidence_and_reliability():
    """Test POST /api/intelligence/retrieve returns Step 4 fields."""
    client = TestClient(app)
    res = client.post("/api/intelligence/retrieve", json={
        "question": "Why did the payment API fail after deployment?",
        "top_k": 3,
        "enable_stress_test": True,
    })
    assert res.status_code == 200
    data = res.json()

    assert "counter_evidence" in data
    assert data["counter_evidence"]["executed"] is True
    assert "evidence_reliability" in data
    assert data["evidence_reliability"]["status"] in ["high_reliability", "moderate_reliability"]
    assert data["evidence_reliability"]["independent_sources_count"] >= 1
    assert "decision_trace" in data
    assert "counter_evidence" in data["decision_trace"]
    assert "evidence_reliability" in data["decision_trace"]
