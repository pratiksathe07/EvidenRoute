from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.db import SessionLocal
from backend.app.adapters.sqlite_source import SQLiteSourceAdapter


def test_health_check_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "sqlite"


def test_list_sources_and_seed_data():
    with TestClient(app) as client:
        response = client.get("/api/sources")
        assert response.status_code == 200
        sources = response.json()
        assert len(sources) >= 3

        source_ids = [s["source_id"] for s in sources]
        assert "kb_official_docs" in source_ids
        assert "support_tickets" in source_ids
        assert "slack_conversations" in source_ids


import uuid


def test_register_and_ingest_source():
    with TestClient(app) as client:
        unique_id = f"test_wiki_{uuid.uuid4().hex[:6]}"
        record_id = f"rec_{uuid.uuid4().hex[:6]}"

        # Register new source
        new_source = {
            "source_id": unique_id,
            "name": "Engineering Wiki",
            "source_type": "document",
            "description": "Internal architectural designs and runbooks.",
            "default_authority": 0.88,
            "enabled": True,
            "metadata": {"team": "infrastructure"},
        }
        res = client.post("/api/sources", json=new_source)
        assert res.status_code == 201
        created = res.json()
        assert created["source_id"] == unique_id

        # Ingest records
        batch = {
            "source_id": unique_id,
            "records": [
                {
                    "record_id": record_id,
                    "title": "Kafka Deployment Guide",
                    "content": "Kafka clusters must be provisioned with at least 3 broker nodes across distinct AZs.",
                    "authority_score": 0.9,
                    "metadata": {"tags": ["kafka", "infrastructure"]},
                }
            ],
        }
        res_ingest = client.post("/api/sources/ingest", json=batch)
        assert res_ingest.status_code == 200
        data = res_ingest.json()
        assert data["ingested_in_batch"] == 1

        # Query using the SQLiteSourceAdapter
        adapter = SQLiteSourceAdapter(unique_id, SessionLocal)
        results = adapter.search("kafka broker nodes", limit=5)
        assert len(results) == 1
        assert results[0].evidence_id == record_id
        assert "Kafka clusters" in results[0].content
