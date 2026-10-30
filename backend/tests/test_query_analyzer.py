"""
Unit tests for EvidenRoute Query Analyzer (Step 1A)
Validates deterministic intent recognition, keyword extraction, entity extraction,
category classification, and source suitability.
"""

import pytest
from app.intelligence.models import (
    InformationCategory,
    IntentType,
    QueryAnalysisResult,
    SourceType,
)
from app.intelligence.query_analyzer import QueryAnalyzer


@pytest.fixture
def analyzer():
    return QueryAnalyzer()


def test_payment_api_failure_example(analyzer):
    """
    Test Step 1A exact example from requirements:
    'Why did the payment API start failing after the latest deployment?'
    """
    q = "Why did the payment API start failing after the latest deployment?"
    result: QueryAnalysisResult = analyzer.analyze(q)

    assert result.intent == IntentType.TECHNICAL_TROUBLESHOOTING.value
    assert result.confidence >= 0.85

    # Check extracted keywords
    assert "payment" in result.keywords
    assert "API" in result.keywords or "api" in [k.lower() for k in result.keywords]
    assert "failing" in result.keywords
    assert "deployment" in result.keywords

    # Check entities
    assert any("payment" in e.lower() and "api" in e.lower() for e in result.entities)

    # Check category and expected info
    assert result.information_category == InformationCategory.TECHNICAL.value
    assert "error reports" in result.expected_information
    assert "deployment records" in result.expected_information
    assert "technical documentation" in result.expected_information

    # Check likely source types
    assert SourceType.DOCUMENTS.value in result.likely_source_types
    assert SourceType.TICKETS.value in result.likely_source_types
    assert SourceType.CONVERSATIONS.value in result.likely_source_types


def test_product_planning_decision(analyzer):
    """
    Test TEST 2:
    'What was decided during the last product planning meeting?'
    """
    q = "What was decided during the last product planning meeting?"
    result = analyzer.analyze(q)

    assert result.intent == IntentType.DECISION_DISCOVERY.value
    assert any("decided" in k for k in result.keywords)
    assert any("product" in e.lower() and "meeting" in e.lower() for e in result.entities)
    assert SourceType.CONVERSATIONS.value in result.likely_source_types


def test_employee_leave_policy(analyzer):
    """
    Test TEST 3:
    'What is the employee leave policy?'
    """
    q = "What is the employee leave policy?"
    result = analyzer.analyze(q)

    assert result.intent == IntentType.POLICY_LOOKUP.value
    assert "leave" in result.keywords
    assert "policy" in result.keywords
    assert any("leave policy" in e.lower() for e in result.entities)
    assert result.information_category == InformationCategory.GOVERNANCE.value
    assert result.likely_source_types == [SourceType.DOCUMENTS.value]


def test_database_connection_timeout(analyzer):
    """
    Test TEST 4:
    'How do I resolve a database connection timeout?'
    """
    q = "How do I resolve a database connection timeout?"
    result = analyzer.analyze(q)

    assert result.intent == IntentType.TECHNICAL_TROUBLESHOOTING.value
    assert "database" in [k.lower() for k in result.keywords]
    assert "timeout" in [k.lower() for k in result.keywords]
    assert any("database" in t.lower() for t in result.technical_terms)
    assert any("timeout" in t.lower() for t in result.technical_terms)


def test_unrelated_topic_query(analyzer):
    """
    Test TEST 5:
    'Tell me about an unrelated topic not covered by the available sources.'
    """
    q = "Tell me about an unrelated topic not covered by the available sources."
    result = analyzer.analyze(q)

    assert result.intent == IntentType.GENERAL_INFORMATION_LOOKUP.value
    assert result.information_category == InformationCategory.GENERAL.value
    assert "unrelated" in result.keywords


def test_empty_and_whitespace_query(analyzer):
    """Test handling of empty or blank query strings."""
    res_empty = analyzer.analyze("")
    assert res_empty.intent == IntentType.UNCLEAR_QUERY.value
    assert res_empty.confidence == 0.0
    assert len(res_empty.keywords) == 0

    res_spaces = analyzer.analyze("    \t \n   ")
    assert res_spaces.intent == IntentType.UNCLEAR_QUERY.value
    assert len(res_spaces.keywords) == 0


def test_special_characters_query(analyzer):
    """Test query containing punctuation and special symbols."""
    q = "!!! ??? $$$"
    result = analyzer.analyze(q)
    assert result.intent == IntentType.UNCLEAR_QUERY.value
