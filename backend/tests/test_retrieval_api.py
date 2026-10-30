"""
Integration tests for Phase 2 FastAPI Endpoints (Task 6 & Task 11)
Tests /ingest, /ingestion-status, /retrieve, and /retrieval-health.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_trigger_ingestion(client):
    """Test POST /api/intelligence/ingest re-indexes all files and returns report."""
    response = client.post("/api/intelligence/ingest")
    assert response.status_code == 200
    data = response.json()
    assert data["total_files_discovered"] >= 7
    assert data["files_successfully_processed"] >= 7
    assert data["total_chunks"] > 0
    assert "ingested_at" in data


def test_api_ingestion_status(client):
    """Test GET /api/intelligence/ingestion-status returns indexed chunk count."""
    response = client.get("/api/intelligence/ingestion-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["total_chunks_indexed"] > 0


def test_api_retrieve_endpoint(client):
    """Test POST /api/intelligence/retrieve executes full pipeline and returns evidence."""
    payload = {
        "question": "Why did the payment API fail after deployment?",
        "top_k": 5,
    }
    response = client.post("/api/intelligence/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == payload["question"]
    assert "query_analysis" in data
    assert "selected_sources" in data
    assert len(data["selected_sources"]) > 0
    assert "retrieved_evidence" in data
    assert len(data["retrieved_evidence"]) > 0
    assert len(data["retrieved_evidence"]) <= 5

    # Check top evidence passage structure
    top_ev = data["retrieved_evidence"][0]
    assert "content" in top_ev
    assert "citation" in top_ev
    assert "evidence_score" in top_ev
    assert top_ev["evidence_score"]["final_evidence_score"] > 0
    assert "scoring_explanation" in top_ev["evidence_score"]


def test_api_retrieve_empty_validation_error(client):
    """Test POST /api/intelligence/retrieve returns 422 on blank question."""
    response = client.post("/api/intelligence/retrieve", json={"question": "   "})
    assert response.status_code == 422


def test_api_retrieval_health(client):
    """Test GET /api/intelligence/retrieval-health reports component states."""
    response = client.get("/api/intelligence/retrieval-health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "operational"
    assert "ready" in data["bm25_status"]
    assert data["active_retrieval_mode"] in ["lexical_only", "hybrid"]
    assert "ready" in data["evidence_scorer_status"]
    assert data["ingestion_status"]["total_chunks_indexed"] > 0
