from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.budget import BudgetConfig
from backend.app.schemas.query import DecisionOutcome


def test_query_answerable_from_single_source():
    """
    Test standard policy lookup question.
    Expected: ANSWER outcome citing refund policy.
    """
    with TestClient(app) as client:
        req = {
            "question": "What is the standard refund policy duration?",
            "budget": {
                "max_source_calls": 5,
                "max_candidates": 10,
                "max_tokens": 2000,
            },
            "enable_stress_test": False,
        }
        res = client.post("/api/query", json=req)
        assert res.status_code == 200
        data = res.json()

        assert data["outcome"] == DecisionOutcome.ANSWER.value
        assert data["final_answer"] is not None
        assert len(data["citations"]) > 0
        assert "doc_policy_refund_v3" in data["citations"]
        assert data["budget_status"]["consumed"]["calls_consumed"] > 0
        assert len(data["execution_trace"]) >= 4


def test_query_outdated_vs_updated_temporal_contradiction():
    """
    Test SLA outage credit question spanning 2024 vs 2025 SLA revisions.
    Expected: Temporal update contradiction detected and resolved by recency.
    """
    with TestClient(app) as client:
        req = {
            "question": "What is the outage credit percentage under the SLA?",
            "enable_stress_test": False,
        }
        res = client.post("/api/query", json=req)
        assert res.status_code == 200
        data = res.json()

        assert data["outcome"] == DecisionOutcome.ANSWER.value
        # Check that contradiction detection caught the SLA update (10% vs 15%)
        contradictions = data["contradictions"]
        assert len(contradictions) >= 1
        assert any(c["contradiction_type"] == "temporal_update" for c in contradictions)


def test_query_insufficient_evidence_abstains():
    """
    Test query on a topic with zero evidence in the database.
    Expected: ABSTAIN outcome, no hallucinated answer.
    """
    with TestClient(app) as client:
        req = {
            "question": "How do quantum teleportation warp drives operate on Mars?",
            "enable_stress_test": False,
        }
        res = client.post("/api/query", json=req)
        assert res.status_code == 200
        data = res.json()

        assert data["outcome"] == DecisionOutcome.ABSTAIN.value
        assert data["final_answer"] is None
        assert data["abstention_reason"] is not None
        assert "No sufficiently relevant" in data["abstention_reason"]


def test_evidence_stress_test_execution():
    """
    Test query with stress testing enabled.
    Expected: Stress test executes bounded search and reports impact.
    """
    with TestClient(app) as client:
        req = {
            "question": "Can customers get a refund for software license?",
            "enable_stress_test": True,
        }
        res = client.post("/api/query", json=req)
        assert res.status_code == 200
        data = res.json()

        assert data["outcome"] == DecisionOutcome.ANSWER.value
        assert data["stress_test"]["executed"] is True
        assert data["stress_test"]["budget_used_calls"] == 1
        # Trace should include stress test step
        trace_step_names = [t["step_name"] for t in data["execution_trace"]]
        assert "Evidence Stress Test" in trace_step_names


def test_query_persistence_and_trace_endpoints():
    """
    Verify GET /api/query/{id} and GET /api/query/{id}/trace return persisted data.
    """
    with TestClient(app) as client:
        # 1. Post query
        req = {
            "question": "Is CSV export supported in EvidenRoute?",
            "enable_stress_test": True,
        }
        res = client.post("/api/query", json=req)
        assert res.status_code == 200
        created = res.json()
        query_id = created["query_id"]

        # 2. Retrieve query details
        res_get = client.get(f"/api/query/{query_id}")
        assert res_get.status_code == 200
        details = res_get.json()
        assert details["query_id"] == query_id
        assert "CSV export" in details["question"]

        # 3. Retrieve trace
        res_trace = client.get(f"/api/query/{query_id}/trace")
        assert res_trace.status_code == 200
        trace = res_trace.json()
        assert len(trace) >= 5
