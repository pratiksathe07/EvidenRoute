"""
Integration and API tests for EvidenRoute Intelligence Endpoints (Step 1E & Step 9)
Uses FastAPI TestClient to test all REST routes, error handling, and CORS.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns API metadata and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "EvidenRoute"
    assert "health_check" in data


def test_health_check_endpoint(client):
    """Test health check reports local component status and unconfigured external LLM."""
    response = client.get("/api/intelligence/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "ready" in data["query_analyzer"]
    assert "ready" in data["source_registry"]
    assert "ready" in data["source_selector"]
    assert "not configured" in data["external_llm_integration"]
    assert data["active_sources_count"] > 0


def test_sources_list_endpoint(client):
    """Test listing of all available sources in the registry."""
    response = client.get("/api/intelligence/sources")
    assert response.status_code == 200
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) >= 5
    assert any(s["source_type"] == "documents" for s in sources)
    assert any(s["source_type"] == "conversations" for s in sources)
    assert any(s["source_type"] == "tickets" for s in sources)


def test_analyze_query_endpoint(client):
    """Test /analyze-query endpoint with payment API question."""
    payload = {"question": "Why did the payment API fail?"}
    response = client.post("/api/intelligence/analyze-query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "technical_troubleshooting"
    assert "payment" in data["keywords"]
    assert len(data["likely_source_types"]) > 0


def test_analyze_query_empty_error(client):
    """Test /analyze-query returns 422 for empty query string."""
    response = client.post("/api/intelligence/analyze-query", json={"question": "   "})
    assert response.status_code == 422


def test_select_sources_endpoint(client):
    """Test /select-sources endpoint produces ranked sources and explanations."""
    payload = {"question": "What was decided during the last product planning meeting?"}
    response = client.post("/api/intelligence/select-sources", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ranked_sources" in data
    assert data["selected_sources_count"] >= 1
    # Check top source
    top = data["ranked_sources"][0]
    assert top["source_type"] == "conversations"
    assert top["selection_status"] == "selected"
    assert len(top["selection_reason"]) > 0


def test_plan_endpoint_complete_decision_trace(client):
    """Test /plan endpoint executes full pipeline and returns decision trace."""
    payload = {"question": "How do I resolve a database connection timeout?"}
    response = client.post("/api/intelligence/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "decision_trace" in data
    trace = data["decision_trace"]
    assert trace["query"] == payload["question"]
    assert trace["analysis"]["intent"] == "technical_troubleshooting"
    assert trace["available_sources_count"] > 0
    assert trace["evaluated_sources_count"] > 0
    assert len(trace["ranked_sources"]) > 0
    assert trace["execution_time_ms"] >= 0.0


def test_plan_endpoint_unrelated_query(client):
    """Test /plan endpoint on unrelated query selects 0 sources."""
    payload = {"question": "Tell me about an unrelated topic not covered by the available sources."}
    response = client.post("/api/intelligence/plan", json=payload)
    assert response.status_code == 200
    trace = response.json()["decision_trace"]
    assert trace["selected_sources_count"] == 0
    assert trace["skipped_sources_count"] == trace["evaluated_sources_count"]
    for r in trace["ranked_sources"]:
        assert r["selection_status"] == "skipped"


def test_cors_headers(client):
    """Test that CORS headers are appropriately emitted."""
    response = client.options(
        "/api/intelligence/plan",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
