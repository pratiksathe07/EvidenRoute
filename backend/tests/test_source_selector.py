"""
Unit tests for EvidenRoute Source Selector and Ranking Engine (Step 1C & Step 9)
Tests multi-factor scoring, missing data weight normalization, threshold filtering,
and the 5 mandatory benchmark questions.
"""

import pytest
from app.intelligence.models import (
    QueryAnalysisResult,
    SelectionConfig,
    SelectionStatus,
    SourceMetadata,
    SourceRankResult,
    SourceType,
)
from app.intelligence.query_analyzer import QueryAnalyzer
from app.intelligence.source_registry import SEED_SOURCES, InMemorySourceRegistry
from app.intelligence.source_selector import SourceSelector


@pytest.fixture
def analyzer():
    return QueryAnalyzer()


@pytest.fixture
def selector():
    return SourceSelector()


@pytest.fixture
def registry():
    return InMemorySourceRegistry()


# -------------------------------------------------------------
# BENCHMARK TESTS 1 - 5
# -------------------------------------------------------------

def test_benchmark_1_payment_api_failure(analyzer, selector, registry):
    """
    TEST 1:
    'Why did the payment API fail after deployment?'
    Expected:
    Technical documents, tickets and conversations rank highly.
    """
    q = "Why did the payment API fail after deployment?"
    analysis = analyzer.analyze(q)
    results = selector.rank_and_select(analysis, registry.list_sources())

    assert len(results) > 0

    # Get selected sources
    selected = [r for r in results if r.selection_status == SelectionStatus.SELECTED.value]
    selected_types = {r.source_type for r in selected}
    selected_ids = {r.source_id for r in selected}

    # Verify technical documents, tickets, and conversations are selected
    assert SourceType.DOCUMENTS.value in selected_types
    assert SourceType.TICKETS.value in selected_types
    assert SourceType.CONVERSATIONS.value in selected_types

    # Top sources should include the relevant payment API doc, bug tracker, and war room
    assert "doc-api-gateway" in selected_ids
    assert "tkt-jira-bugs" in selected_ids
    assert "conv-incident-war-room" in selected_ids

    # Policy documents should be skipped or ranked at the bottom
    hr_rank = next((r for r in results if r.source_id == "doc-hr-policies"), None)
    assert hr_rank is not None
    assert hr_rank.selection_status == SelectionStatus.SKIPPED.value


def test_benchmark_2_product_planning_meeting(analyzer, selector, registry):
    """
    TEST 2:
    'What was decided during the last product planning meeting?'
    Expected:
    Conversations rank highly.
    """
    q = "What was decided during the last product planning meeting?"
    analysis = analyzer.analyze(q)
    results = selector.rank_and_select(analysis, registry.list_sources())

    # Top ranked source must be the product planning conversation
    top_source = results[0]
    assert top_source.source_type == SourceType.CONVERSATIONS.value
    assert top_source.source_id == "conv-product-planning"
    assert top_source.selection_status == SelectionStatus.SELECTED.value
    assert top_source.final_score >= 0.60


def test_benchmark_3_employee_leave_policy(analyzer, selector, registry):
    """
    TEST 3:
    'What is the employee leave policy?'
    Expected:
    Policy documents rank highly.
    """
    q = "What is the employee leave policy?"
    analysis = analyzer.analyze(q)
    results = selector.rank_and_select(analysis, registry.list_sources())

    # Top ranked source must be the HR policy document
    top_source = results[0]
    assert top_source.source_type == SourceType.DOCUMENTS.value
    assert top_source.source_id == "doc-hr-policies"
    assert top_source.selection_status == SelectionStatus.SELECTED.value
    assert top_source.final_score >= 0.70

    # Irrelevant technical bug tracker and war room should be skipped
    war_room = next((r for r in results if r.source_id == "conv-incident-war-room"), None)
    assert war_room is not None
    assert war_room.selection_status == SelectionStatus.SKIPPED.value


def test_benchmark_4_database_connection_timeout(analyzer, selector, registry):
    """
    TEST 4:
    'How do I resolve a database connection timeout?'
    Expected:
    Technical documentation and relevant tickets rank highly.
    """
    q = "How do I resolve a database connection timeout?"
    analysis = analyzer.analyze(q)
    results = selector.rank_and_select(analysis, registry.list_sources())

    selected = [r for r in results if r.selection_status == SelectionStatus.SELECTED.value]
    selected_ids = {r.source_id for r in selected}

    # Technical doc and bug ticket should be selected
    assert "doc-db-architecture" in selected_ids
    assert "tkt-jira-bugs" in selected_ids

    # DB doc should be among the top 2
    db_doc = next(r for r in results if r.source_id == "doc-db-architecture")
    assert db_doc.ranking_position in [1, 2]
    assert db_doc.selection_status == SelectionStatus.SELECTED.value


def test_benchmark_5_unrelated_topic(analyzer, selector, registry):
    """
    TEST 5:
    'Tell me about an unrelated topic not covered by the available sources.'
    Expected:
    Low source relevance and an appropriate no-suitable-source result.
    """
    q = "Tell me about an unrelated topic not covered by the available sources."
    analysis = analyzer.analyze(q)
    results = selector.rank_and_select(analysis, registry.list_sources())

    # Every source should have low relevance (< 0.15 threshold) and be skipped
    selected = [r for r in results if r.selection_status == SelectionStatus.SELECTED.value]
    assert len(selected) == 0

    for r in results:
        assert r.selection_status == SelectionStatus.SKIPPED.value
        assert "Skipped:" in r.selection_reason


# -------------------------------------------------------------
# EDGE CASES & ROBUSTNESS TESTS
# -------------------------------------------------------------

def test_empty_registry(analyzer, selector):
    """Test behavior when the source registry has 0 candidate sources."""
    analysis = analyzer.analyze("Why did the payment API fail?")
    results = selector.rank_and_select(analysis, [])
    assert results == []


def test_unavailable_source_handling(analyzer, selector):
    """
    Test that unavailable sources (e.g. legacy archive with availability=False)
    are strictly marked skipped with an explicit offline explanation.
    """
    offline_src = SourceMetadata(
        source_id="src-offline",
        source_name="Offline Source",
        source_type="documents",
        description="Payment API documentation archived offline",
        authority_level=0.95,
        supported_topics=["payment", "api"],
        availability=False,  # Offline
        metadata={"historical_usefulness": 0.90}
    )
    analysis = analyzer.analyze("Why did the payment API fail?")
    results = selector.rank_and_select(analysis, [offline_src])

    assert len(results) == 1
    assert results[0].selection_status == SelectionStatus.SKIPPED.value
    assert "offline" in results[0].selection_reason.lower() or "unavailable" in results[0].selection_reason.lower()
    assert results[0].availability_score == 0.0


def test_missing_metadata_weight_normalization(analyzer, selector):
    """
    Test that sources without historical usefulness metadata do NOT crash,
    and dynamically normalize the remaining component weights.
    """
    no_meta_src = SourceMetadata(
        source_id="src-no-meta",
        source_name="New Source Without History",
        source_type="documents",
        description="Freshly registered payment API documentation",
        authority_level=0.90,
        supported_topics=["payment", "api"],
        availability=True,
        metadata={}  # Empty metadata
    )
    analysis = analyzer.analyze("Why did the payment API fail?")
    results = selector.rank_and_select(analysis, [no_meta_src])

    assert len(results) == 1
    res = results[0]
    assert res.historical_usefulness_score is None

    # Check breakdown and normalized weights
    assert res.score_breakdown is not None
    weights = res.score_breakdown.weights_applied
    assert "historical" not in weights
    # Sum of remaining weights must equal 1.0 (within float precision)
    assert abs(sum(weights.values()) - 1.0) < 1e-4
    assert 0.0 <= res.final_score <= 1.0


def test_configurable_thresholds(analyzer, selector, registry):
    """Test that custom selection thresholds alter the selection decision."""
    q = "Why did the payment API fail after deployment?"
    analysis = analyzer.analyze(q)

    # Ultra-strict threshold (0.95) should select very few or 0 sources
    strict_cfg = SelectionConfig(selection_threshold=0.95)
    strict_results = selector.rank_and_select(analysis, registry.list_sources(), config=strict_cfg)
    strict_selected = [r for r in strict_results if r.selection_status == SelectionStatus.SELECTED.value]
    assert len(strict_selected) <= 1

    # Permissive threshold (0.20) should select more sources
    permissive_cfg = SelectionConfig(selection_threshold=0.20, min_relevance_threshold=0.05)
    permissive_results = selector.rank_and_select(analysis, registry.list_sources(), config=permissive_cfg)
    permissive_selected = [r for r in permissive_results if r.selection_status == SelectionStatus.SELECTED.value]
    assert len(permissive_selected) > len(strict_selected)
