"""
Unit tests for BM25 Retrieval, Semantic Provider, Evidence Scorer, and Pipeline (Phase 2 Tasks 2-5)
Validates source-constrained retrieval, four-dimensional evidence scoring,
temporal freshness decay, and end-to-end integration with Phase 1.
"""

from datetime import datetime, timezone
import pytest
from app.intelligence.embedding_provider import SentenceTransformerEmbeddingProvider
from app.intelligence.evidence_scorer import EvidenceScorer
from app.intelligence.ingestion import IngestionService
from app.intelligence.models import (
    ChunkData,
    EvidenceScoringConfig,
    QueryAnalysisResult,
    RetrievalConfig,
    SourceType,
)
from app.intelligence.query_analyzer import QueryAnalyzer
from app.intelligence.retrieval_pipeline import RetrievalPipeline
from app.intelligence.retriever import BM25Retriever
from app.intelligence.source_registry import InMemorySourceRegistry
from app.intelligence.storage import InMemoryChunkStore


@pytest.fixture
def chunk_store():
    store = InMemoryChunkStore()
    ingestion = IngestionService(chunk_store=store)
    ingestion.run_ingestion(clear_existing=True)
    return store


@pytest.fixture
def retriever(chunk_store):
    return BM25Retriever(chunk_store=chunk_store)


@pytest.fixture
def evidence_scorer():
    return EvidenceScorer()


# -------------------------------------------------------------
# TASK 2: BM25 RETRIEVAL TESTS
# -------------------------------------------------------------

def test_bm25_technical_query_matching(retriever):
    """Test BM25 finds relevant payment API passages within selected sources."""
    query = "payment API deployment failure timeout"
    selected_sources = ["doc-api-gateway", "tkt-jira-bugs", "conv-incident-war-room"]

    results = retriever.retrieve(query=query, selected_source_ids=selected_sources, top_k=5)
    assert len(results) > 0

    top_chunk, raw_score, norm_score = results[0]
    assert raw_score > 0
    assert 0.0 <= norm_score <= 1.0
    # Top chunk should belong to one of the selected payment sources
    assert top_chunk.source_id in selected_sources
    assert any(term in top_chunk.content.lower() for term in ["payment", "timeout", "deployment"])


def test_bm25_exact_identifier_matching(retriever):
    """Test exact ticket ID or incident ID matching."""
    query = "ENG-4029"
    selected_sources = ["tkt-jira-bugs"]

    results = retriever.retrieve(query=query, selected_source_ids=selected_sources, top_k=3)
    assert len(results) > 0
    top_chunk = results[0][0]
    assert top_chunk.record_id == "ENG-4029"
    assert "ENG-4029" in top_chunk.content


def test_bm25_selected_source_filtering_strictly_enforced(retriever):
    """
    CRITICAL TEST: Ensure BM25 NEVER searches or returns chunks from skipped/unselected sources.
    Only HR policy source is selected; payment API chunks must NOT appear.
    """
    query = "payment API timeout"
    # Select ONLY HR policies (unrelated to payment)
    selected_sources = ["doc-hr-policies"]

    results = retriever.retrieve(query=query, selected_source_ids=selected_sources, top_k=5)
    for chunk, _, _ in results:
        assert chunk.source_id == "doc-hr-policies"
        assert chunk.source_id != "doc-api-gateway"
        assert chunk.source_id != "tkt-jira-bugs"


def test_bm25_empty_query_and_empty_index():
    """Test handling of empty query or empty chunk store."""
    empty_store = InMemoryChunkStore()
    retriever_empty = BM25Retriever(chunk_store=empty_store)

    assert retriever_empty.retrieve("", ["doc-api-gateway"]) == []
    assert retriever_empty.retrieve("query", []) == []
    assert retriever_empty.retrieve("query", ["doc-nonexistent"]) == []


# -------------------------------------------------------------
# TASK 3: SEMANTIC PROVIDER TESTS
# -------------------------------------------------------------

def test_semantic_provider_lazy_loading_and_offline_safety():
    """
    Verify provider does not download weights and reports lexical_only mode when offline.
    """
    provider = SentenceTransformerEmbeddingProvider(enabled=False)
    status = provider.get_status()

    assert status["model_name"] == "all-MiniLM-L6-v2"
    assert status["is_enabled"] is False
    assert status["mode"] == "lexical_only"
    assert "local-first" in status["notes"]


# -------------------------------------------------------------
# TASK 4: EVIDENCE SCORER TESTS
# -------------------------------------------------------------

def test_evidence_scoring_dimensions(evidence_scorer):
    """Test the 4 independent dimensions: Relevance, Authority, Freshness, Directness."""
    chunk = ChunkData(
        chunk_id="chk-test-1",
        source_id="doc-api-gateway",
        source_type="documents",
        record_id="payment_api_spec",
        title="Payment API Spec",
        content="Root cause was connection pool exhaustion. Resolution: increased pool size to 50.",
        created_at="2026-10-28T12:00:00Z",
        authority_level=0.95,
        original_file_path="data/documents/payment_api_spec.md",
        chunk_index=0,
    )

    analyzer = QueryAnalyzer()
    q_analysis = analyzer.analyze("Why did the payment API start failing?")

    score = evidence_scorer.score_evidence(
        chunk=chunk,
        retrieval_score=0.90,
        query_analysis=q_analysis,
        reference_time=datetime(2026, 10, 30, tzinfo=timezone.utc),
    )

    assert score.relevance_score == 0.90
    assert score.authority_score == 0.95
    assert score.freshness_score is not None
    assert score.freshness_score > 0.90  # 2 days old with 180d half life is extremely fresh
    assert score.freshness_status == "fresh"
    assert score.directness_label == "direct"
    assert score.final_evidence_score >= 0.85


def test_freshness_decay_calculation(evidence_scorer):
    """Test exponential half-life decay formula: F = 2^(-AgeDays / HalfLifeDays)."""
    # 180 days old passage with 180d half life should score exactly 0.50
    old_chunk = ChunkData(
        chunk_id="chk-old",
        source_id="doc-archive",
        source_type="documents",
        record_id="old_doc",
        title="Old Doc",
        content="General background information",
        created_at="2026-05-03T00:00:00Z",  # ~180 days before Oct 30 2026
        authority_level=0.70,
        original_file_path="doc.md",
        chunk_index=0,
    )
    analyzer = QueryAnalyzer()
    q_analysis = analyzer.analyze("General information")

    cfg = EvidenceScoringConfig(freshness_half_life_days=180.0)
    score = evidence_scorer.score_evidence(
        chunk=old_chunk,
        retrieval_score=0.80,
        query_analysis=q_analysis,
        reference_time=datetime(2026, 10, 30, tzinfo=timezone.utc),
        config=cfg,
    )

    assert score.freshness_score is not None
    assert abs(score.freshness_score - 0.50) < 0.05
    assert score.freshness_status == "decayed"


def test_missing_timestamp_weight_normalization(evidence_scorer):
    """Test that missing timestamps do NOT crash and normalize remaining weights."""
    no_time_chunk = ChunkData(
        chunk_id="chk-notime",
        source_id="doc-test",
        source_type="documents",
        record_id="spec",
        title="Undated Spec",
        content="Technical specifications without timestamp.",
        created_at=None,
        updated_at=None,
        authority_level=0.85,
        original_file_path="spec.md",
        chunk_index=0,
    )
    analyzer = QueryAnalyzer()
    q_analysis = analyzer.analyze("technical specifications")

    score = evidence_scorer.score_evidence(
        chunk=no_time_chunk,
        retrieval_score=0.75,
        query_analysis=q_analysis,
    )

    assert score.freshness_score is None
    assert score.freshness_status == "unknown"
    assert "freshness" not in score.weights_applied
    # Sum of remaining weights must equal 1.0
    assert abs(sum(score.weights_applied.values()) - 1.0) < 1e-4
    assert 0.0 <= score.final_evidence_score <= 1.0


# -------------------------------------------------------------
# TASK 5: RETRIEVAL PIPELINE INTEGRATION TESTS
# -------------------------------------------------------------

def test_pipeline_payment_api_question(chunk_store):
    """
    Test end-to-end question from requirements:
    'Why did the payment API fail after deployment?'
    """
    pipeline = RetrievalPipeline(chunk_store=chunk_store)
    trace = pipeline.run(question="Why did the payment API fail after deployment?", top_k=5)

    assert trace.query == "Why did the payment API fail after deployment?"
    assert trace.retrieved_evidence_count > 0
    assert len(trace.retrieved_evidence) <= 5
    assert trace.retrieval_mode == "lexical_only"

    # Selected sources must be technical docs, tickets, and war room
    assert "doc-api-gateway" in trace.selected_source_ids
    assert "tkt-jira-bugs" in trace.selected_source_ids
    assert "conv-incident-war-room" in trace.selected_source_ids

    # Unrelated HR policies must be skipped and never searched
    assert "doc-hr-policies" in trace.skipped_source_ids
    for ev in trace.retrieved_evidence:
        assert ev.source_id != "doc-hr-policies"
        assert ev.evidence_score.final_evidence_score > 0
        assert len(ev.citation) > 0


def test_pipeline_unrelated_query_budget_preservation(chunk_store):
    """
    TEST 5 Integration:
    'Tell me about an unrelated topic not covered by the available sources.'
    Zero sources selected in Phase 1 -> 0 chunks scanned -> 0 evidence returned.
    """
    pipeline = RetrievalPipeline(chunk_store=chunk_store)
    trace = pipeline.run(
        question="Tell me about an unrelated topic not covered by the available sources.",
        top_k=5,
    )

    assert len(trace.selected_source_ids) == 0
    assert trace.retrieved_evidence_count == 0
    assert len(trace.retrieved_evidence) == 0
    assert trace.budget_info.get("status") == "budget_preserved"
