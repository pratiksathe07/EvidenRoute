"""
EvidenRoute - Phase 3 Test Suite
Comprehensive tests for:
1. Conflict Detection Engine (direct contradictions vs temporal/version differences vs consistent facts).
2. Evidence Sufficiency Evaluation (high relevance but insufficient, missing evidence, conflicts).
3. Context Pruning Engine (sentence deduplication, citation preservation, conflict shielding, budget limits).
4. End-to-End Pipeline Integration and API Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.intelligence import (
    AnswerReadinessEvaluator,
    ConflictDetector,
    ContextPruner,
    EvidencePassage,
    EvidenceScore,
    QueryAnalysisResult,
    QueryAnalyzer,
    RecommendedAction,
    RetrievalPipeline,
    SufficiencyEvaluator,
    SufficiencyStatus,
)


def _make_dummy_passage(
    chunk_id: str,
    source_id: str,
    source_name: str,
    title: str,
    content: str,
    authority: float = 0.85,
    relevance: float = 0.80,
    directness: str = "direct",
    created_at: str = "2026-10-28T14:00:00Z",
) -> EvidencePassage:
    """Helper to instantiate valid EvidencePassage objects for testing."""
    dir_score = 1.0 if directness == "direct" else (0.75 if directness == "supporting" else 0.20)
    ev_score = EvidenceScore(
        relevance_score=relevance,
        authority_score=authority,
        freshness_score=0.90,
        freshness_status="fresh",
        directness_score=dir_score,
        directness_label=directness,
        final_evidence_score=round((relevance + authority + dir_score) / 3.0, 4),
        scoring_explanation="Test dummy score",
        weights_applied={"relevance": 0.35, "authority": 0.25, "freshness": 0.20, "directness": 0.20},
    )
    return EvidencePassage(
        chunk_id=chunk_id,
        source_id=source_id,
        source_name=source_name,
        source_type="documents",
        record_id=f"rec-{chunk_id}",
        title=title,
        content=content,
        authority_level=authority,
        created_at=created_at,
        original_file_path=f"data/documents/{chunk_id}.md",
        chunk_index=0,
        retrieval_score=relevance,
        bm25_score=12.5,
        semantic_score=None,
        retrieval_mode="lexical_only",
        evidence_score=ev_score,
        citation=f"[{source_name} ({source_id}) § Chunk 0, File: {chunk_id}.md, Record: rec-{chunk_id}]",
        ranking_position=1,
    )


# ==============================================================
# 1. CONFLICT DETECTION TESTS
# ==============================================================

def test_two_passages_containing_contradictory_facts():
    """Test that mutually exclusive quantitative statements on the same metric are detected as direct contradiction."""
    detector = ConflictDetector()

    p1 = _make_dummy_passage(
        chunk_id="chk-timeout-1",
        source_id="doc-api",
        source_name="API Gateway Spec",
        title="Gateway Settings",
        content="The payment gateway timeout is set to 5 seconds for upstream banking requests.",
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-timeout-2",
        source_id="tkt-jira",
        source_name="Incident Ticket",
        title="Timeout Investigation",
        content="Configuration error: The payment gateway timeout is set to 30 seconds for banking requests.",
    )

    result = detector.detect_conflicts([p1, p2])

    assert result.conflicts_detected_count == 1
    assert result.direct_contradictions_count == 1
    assert result.has_unresolved_contradictions is True

    conf = result.conflicts[0]
    assert conf.conflict_type == "direct_contradiction"
    assert conf.is_direct_contradiction is True
    assert conf.severity == "critical"
    assert len(conf.conflicting_passages) == 2
    assert conf.conflicting_passages[0].chunk_id == "chk-timeout-1"
    assert conf.conflicting_passages[1].chunk_id == "chk-timeout-2"
    assert "timeout" in conf.topic.lower()


def test_two_passages_containing_consistent_facts():
    """Test that passages corroborating the same factual findings are not flagged as contradictions."""
    detector = ConflictDetector()

    p1 = _make_dummy_passage(
        chunk_id="chk-postmortem",
        source_id="doc-postmortem",
        source_name="Postmortem Doc",
        title="Deployment Failure",
        content="Root cause was database connection pool exhaustion under load after rolling deployment.",
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-ticket",
        source_id="tkt-jira-bugs",
        source_name="Jira Bug Report",
        title="Pool Exhaustion Fix",
        content="Resolution: Increased pool limit to 50 connections to resolve database connection pool exhaustion.",
    )

    result = detector.detect_conflicts([p1, p2])

    assert result.conflicts_detected_count == 0
    assert result.direct_contradictions_count == 0
    assert result.has_unresolved_contradictions is False


def test_different_dates_or_versions_not_treated_as_contradictions():
    """Test that version divergence (v1 vs v2) and temporal updates are distinguished from direct contradictions."""
    detector = ConflictDetector()

    # Case A: Version divergence
    p_v1 = _make_dummy_passage(
        chunk_id="chk-v1",
        source_id="doc-api-v1",
        source_name="API Spec v1",
        title="v1 Auth",
        content="In API v1, authentication is optional for public status endpoints.",
    )
    p_v2 = _make_dummy_passage(
        chunk_id="chk-v2",
        source_id="doc-api-v2",
        source_name="API Spec v2",
        title="v2 Auth",
        content="In API v2, authentication is required for all status endpoints.",
    )

    res_v = detector.detect_conflicts([p_v1, p_v2])
    assert res_v.conflicts_detected_count >= 1
    assert res_v.direct_contradictions_count == 0  # NOT a direct contradiction!
    assert res_v.has_unresolved_contradictions is False
    assert res_v.conflicts[0].conflict_type == "version_divergence"

    # Case B: Temporal supersedence (different dates with update language)
    p_old = _make_dummy_passage(
        chunk_id="chk-old-policy",
        source_id="doc-hr-2024",
        source_name="HR Handbook 2024",
        title="Leave 2024",
        content="Employees receive 20 days annual paid leave per calendar year.",
        created_at="2024-01-01T00:00:00Z",
    )
    p_new = _make_dummy_passage(
        chunk_id="chk-new-policy",
        source_id="doc-hr-2026",
        source_name="HR Handbook 2026",
        title="Leave 2026",
        content="Updated leave policy as of August 2026: Employees receive 25 days annual paid leave.",
        created_at="2026-08-01T00:00:00Z",
    )

    res_t = detector.detect_conflicts([p_old, p_new])
    assert res_t.conflicts_detected_count >= 1
    assert res_t.direct_contradictions_count == 0  # NOT a direct contradiction!
    assert res_t.has_unresolved_contradictions is False
    assert res_t.conflicts[0].conflict_type == "temporal_supersedence"


def test_unrelated_statements_not_flagged_as_contradictions():
    """Test that statements on unrelated domains (e.g. leave vs database) are never falsely compared."""
    detector = ConflictDetector()

    p_hr = _make_dummy_passage(
        chunk_id="chk-hr",
        source_id="doc-hr",
        source_name="HR",
        title="Leave",
        content="Emergency sick leave must be logged within 24 hours of absence.",
    )
    p_db = _make_dummy_passage(
        chunk_id="chk-db",
        source_id="doc-db",
        source_name="DB",
        title="Database",
        content="Ensure MAX_DB_POOL_SIZE is configured to at least 50 connections.",
    )

    result = detector.detect_conflicts([p_hr, p_db])
    assert result.conflicts_detected_count == 0
    assert result.direct_contradictions_count == 0


# ==============================================================
# 2. EVIDENCE SUFFICIENCY EVALUATION TESTS
# ==============================================================

def test_high_relevance_but_insufficient_evidence():
    """Test that high lexical/semantic retrieval score alone does not grant sufficiency if key information is missing."""
    evaluator = SufficiencyEvaluator()
    analyzer = QueryAnalyzer()

    # Query requires reproduction steps and incident ticket
    query = "What are the exact reproduction steps and error stack trace for the payment API timeout?"
    analysis = analyzer.analyze(query)

    # Passage has high relevance to 'payment API timeout' but is only tangential documentation
    tangential_passage = _make_dummy_passage(
        chunk_id="chk-tangential",
        source_id="doc-spec",
        source_name="API Spec",
        title="Payment API Spec",
        content="The payment API supports credit card charges. Timeouts may occur on bank gateway.",
        relevance=0.92,  # High relevance score
        directness="tangential",  # Only tangential mentions, no reproduction steps
    )

    result = evaluator.evaluate_sufficiency(
        query=query,
        analysis=analysis,
        passages=[tangential_passage],
        conflicts=[],
    )

    assert result.is_sufficient is False
    assert result.sufficiency_status == SufficiencyStatus.PARTIALLY_SUFFICIENT.value
    assert result.recommended_action == RecommendedAction.RETRIEVE_MORE.value
    assert len(result.missing_information) > 0


def test_missing_evidence_results_in_abstain():
    """Test that zero or irrelevant evidence results in an abstain verdict."""
    evaluator = SufficiencyEvaluator()
    analyzer = QueryAnalyzer()

    query = "Explain quantum cryptography state verification in our distributed ledger."
    analysis = analyzer.analyze(query)

    result = evaluator.evaluate_sufficiency(
        query=query,
        analysis=analysis,
        passages=[],
        conflicts=[],
    )

    assert result.is_sufficient is False
    assert result.sufficiency_status == SufficiencyStatus.INSUFFICIENT.value
    assert result.recommended_action == RecommendedAction.ABSTAIN.value
    assert result.sufficiency_score == 0.0


def test_conflicting_evidence_results_in_clarify_or_abstain():
    """Test that an unresolved direct contradiction forces sufficiency status to 'conflicted' and recommends clarification."""
    evaluator = SufficiencyEvaluator()
    detector = ConflictDetector()
    analyzer = QueryAnalyzer()

    query = "What is the timeout duration for the payment API gateway?"
    analysis = analyzer.analyze(query)

    p1 = _make_dummy_passage(
        chunk_id="chk-p1",
        source_id="doc-api",
        source_name="API Docs",
        title="Config 1",
        content="The payment gateway timeout is set to 5 seconds.",
        relevance=0.95,
        directness="direct",
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-p2",
        source_id="tkt-bug",
        source_name="Bug Report",
        title="Config 2",
        content="The payment gateway timeout is set to 30 seconds.",
        relevance=0.95,
        directness="direct",
    )

    conflict_res = detector.detect_conflicts([p1, p2])
    assert conflict_res.direct_contradictions_count == 1

    suff = evaluator.evaluate_sufficiency(
        query=query,
        analysis=analysis,
        passages=[p1, p2],
        conflicts=conflict_res.conflicts,
    )

    assert suff.is_sufficient is False
    assert suff.sufficiency_status == SufficiencyStatus.CONFLICTED.value
    assert suff.recommended_action == RecommendedAction.CLARIFY.value
    assert "conflicting evidence detected" in suff.explanation.lower()

    # Also test readiness evaluation
    readiness_eval = AnswerReadinessEvaluator()
    pruner = ContextPruner()
    pruned = pruner.prune_context([p1, p2], conflicts=conflict_res.conflicts)
    readiness = readiness_eval.evaluate_readiness(suff, conflict_res, pruned)

    assert readiness.is_ready_to_answer is False
    assert readiness.readiness_verdict == "NEEDS_CLARIFICATION"


# ==============================================================
# 3. CONTEXT PRUNING TESTS
# ==============================================================

def test_duplicate_sentence_removal():
    """Test that identical redundant sentences across passages are pruned while keeping unique sentences."""
    pruner = ContextPruner()

    p1 = _make_dummy_passage(
        chunk_id="chk-p1",
        source_id="doc-spec",
        source_name="API Spec",
        title="Spec",
        content="Payment API deployment release-2026.10-rc2 occurred at 14:00.\nThis is a standard deployment procedure.",
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-p2",
        source_id="tkt-bug",
        source_name="Bug Report",
        title="Bug",
        content="Payment API deployment release-2026.10-rc2 occurred at 14:00.\nIncident triage team joined at 14:15.",
    )

    result = pruner.prune_context([p1, p2])

    assert result.original_sentence_count == 4
    # The redundant sentence "This is a standard deployment procedure" is unique, but the first sentence is repeated
    assert result.pruned_sentence_count >= 1
    assert any(d.reason == "redundant_duplicate_sentence" for d in result.pruned_details)
    assert len(result.retained_evidence) == 2


def test_citation_preservation_during_pruning():
    """Test that context pruning NEVER modifies or strips citations, source names, or file paths."""
    pruner = ContextPruner()

    p1 = _make_dummy_passage(
        chunk_id="chk-cit-1",
        source_id="doc-api-gateway",
        source_name="API Gateway Technical Specifications",
        title="Gateway Spec",
        content="Ensure MAX_DB_POOL_SIZE is configured to at least 50 connections.",
    )

    result = pruner.prune_context([p1])

    assert len(result.retained_evidence) == 1
    retained = result.retained_evidence[0]

    assert retained.citation == p1.citation
    assert retained.chunk_id == p1.chunk_id
    assert retained.source_id == p1.source_id
    assert retained.source_name == p1.source_name
    assert retained.original_file_path == p1.original_file_path


def test_conflicting_evidence_shielded_from_pruning():
    """Test that sentences involved in factual conflicts are explicitly protected and never silently removed."""
    pruner = ContextPruner()
    detector = ConflictDetector()

    p1 = _make_dummy_passage(
        chunk_id="chk-c1",
        source_id="doc-a",
        source_name="Doc A",
        title="A",
        content="The payment gateway timeout is set to 5 seconds.",
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-c2",
        source_id="doc-b",
        source_name="Doc B",
        title="B",
        content="The payment gateway timeout is set to 30 seconds.",
    )

    conf_res = detector.detect_conflicts([p1, p2])
    assert conf_res.conflicts_detected_count == 1

    pruned = pruner.prune_context([p1, p2], conflicts=conf_res.conflicts)

    assert pruned.conflict_passages_preserved_count == 2
    assert len(pruned.retained_evidence) == 2
    # Verify both conflicting statements are present in retained evidence
    assert "5 seconds" in pruned.retained_evidence[0].content or "5 seconds" in pruned.retained_evidence[1].content
    assert "30 seconds" in pruned.retained_evidence[0].content or "30 seconds" in pruned.retained_evidence[1].content


def test_budget_limit_compliance():
    """Test that context pruner adheres to character budget limits without exceeding max_context_chars."""
    pruner = ContextPruner()

    p1 = _make_dummy_passage(
        chunk_id="chk-long-1",
        source_id="doc-1",
        source_name="Doc 1",
        title="Doc 1",
        content="A" * 150,
        authority=0.95,
        relevance=0.90,
    )
    p2 = _make_dummy_passage(
        chunk_id="chk-long-2",
        source_id="doc-2",
        source_name="Doc 2",
        title="Doc 2",
        content="B" * 150,
        authority=0.70,
        relevance=0.60,
    )

    # Set strict budget to 180 chars (can only fit p1, p2 should be pruned)
    result = pruner.prune_context([p1, p2], max_context_chars=180)

    assert len(result.retained_evidence) == 1
    assert result.retained_evidence[0].chunk_id == "chk-long-1"
    assert any(d.reason == "exceeded_context_budget_limit" for d in result.pruned_details)


# ==============================================================
# 4. END-TO-END PIPELINE & API TESTS
# ==============================================================

def test_end_to_end_pipeline_integration():
    """Test that RetrievalPipeline runs all Phase 1, Phase 2, and Phase 3 stages successfully."""
    client = TestClient(app)

    # Run query on real indexed seed data
    res = client.post("/api/intelligence/retrieve", json={"question": "Why did the payment API fail after deployment?"})
    assert res.status_code == 200
    data = res.json()

    # Check Phase 1 & 2 fields
    assert "query" in data
    assert "selected_sources" in data
    assert len(data["selected_sources"]) > 0
    assert len(data["retrieved_evidence"]) > 0

    # Check Phase 3 fields in root response
    assert "conflicts" in data
    assert "sufficiency" in data
    assert "pruned_context" in data
    assert "answer_readiness" in data

    # Check Decision Trace
    trace = data["decision_trace"]
    assert "conflicts" in trace
    assert "sufficiency" in trace
    assert "pruned_context" in trace
    assert "answer_readiness" in trace

    # Check trace stages includes Phase 3 stages
    stage_text = " ".join(trace["trace_stages"])
    assert "Stage 6: Evaluated" in stage_text
    assert "Stage 7: Evaluated evidence sufficiency" in stage_text
    assert "Stage 8: Context pruning" in stage_text
    assert "Stage 9: Answer readiness verdict" in stage_text

    # Real data has corroborating postmortem/bug info -> ready to answer
    assert data["answer_readiness"]["is_ready_to_answer"] is True
    assert data["answer_readiness"]["recommended_action"] == "answer"


def test_api_detect_conflicts_endpoint():
    """Test the POST /api/intelligence/detect-conflicts endpoint."""
    client = TestClient(app)

    # Test with question
    res = client.post("/api/intelligence/detect-conflicts", json={"question": "Why did the payment API fail after deployment?"})
    assert res.status_code == 200
    data = res.json()
    assert "total_passages_evaluated" in data
    assert "conflicts" in data


def test_api_evaluate_evidence_endpoint():
    """Test the POST /api/intelligence/evaluate-evidence endpoint."""
    client = TestClient(app)

    res = client.post("/api/intelligence/evaluate-evidence", json={"question": "Why did the payment API fail after deployment?"})
    assert res.status_code == 200
    data = res.json()

    assert data["question"] == "Why did the payment API fail after deployment?"
    assert "sufficiency" in data
    assert "readiness" in data
    assert "conflicts" in data
    assert "pruned_context" in data
    assert data["sufficiency"]["is_sufficient"] is True


def test_api_prune_context_endpoint():
    """Test the POST /api/intelligence/prune-context endpoint."""
    client = TestClient(app)

    p1 = _make_dummy_passage(
        chunk_id="chk-1",
        source_id="doc-1",
        source_name="Doc 1",
        title="Title 1",
        content="Sent 1. Sent 2.",
    )

    res = client.post("/api/intelligence/prune-context", json={"passages": [p1.model_dump()]})
    assert res.status_code == 200
    data = res.json()
    assert data["original_passages_count"] == 1
    assert data["retained_passages_count"] == 1
