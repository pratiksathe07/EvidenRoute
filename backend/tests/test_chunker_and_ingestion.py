"""
Tests for Document Chunking and Local Ingestion Engine (Phase 2 Task 1 & Task 11)
Validates markdown, conversation, ticket parsing, deterministic hashing,
malformed JSON error resilience, and ingestion reporting.
"""

from pathlib import Path
import tempfile
import pytest
from app.intelligence.chunker import DocumentChunker, generate_deterministic_chunk_id
from app.intelligence.ingestion import IngestionService
from app.intelligence.models import ChunkData, SourceType
from app.intelligence.storage import InMemoryChunkStore


@pytest.fixture
def chunker():
    return DocumentChunker(max_chunk_chars=300, overlap_chars=50)


def test_markdown_chunking_and_headers(chunker):
    """Test that markdown is split cleanly across section headers."""
    sample_md = """# Payment API Guide

## Overview
The payment gateway handles credit cards and tokens.

## Endpoints
POST /v1/charge initiates an immediate charge transaction.
GET /v1/charge/{id} retrieves charge details.

## Error Codes
500 Internal Error occurs when database pool is exhausted.
504 Gateway Timeout occurs when bank does not respond.
"""
    chunks = chunker.chunk_markdown(
        raw_text=sample_md,
        source_id="doc-api-gateway",
        record_id="payment_api_spec",
        authority_level=0.95,
        file_path="data/documents/payment_api_spec.md",
    )

    assert len(chunks) >= 3
    # Verify titles inherit document header + section header
    assert any("Overview" in c.title for c in chunks)
    assert any("Endpoints" in c.title for c in chunks)
    assert any("Error Codes" in c.title for c in chunks)
    # Check authority and source_id
    for c in chunks:
        assert c.source_id == "doc-api-gateway"
        assert c.source_type == SourceType.DOCUMENTS.value
        assert c.authority_level == 0.95
        assert len(c.chunk_id) >= 16


def test_deterministic_chunk_ids():
    """Verify chunk IDs are strictly deterministic and reproducible."""
    id1 = generate_deterministic_chunk_id("doc-1", "rec-1", 0, "Some sample content")
    id2 = generate_deterministic_chunk_id("doc-1", "rec-1", 0, "Some sample content")
    id3 = generate_deterministic_chunk_id("doc-1", "rec-1", 1, "Some different content")

    assert id1 == id2
    assert id1 != id3


def test_conversation_chunking(chunker):
    """Test grouping of transcript dialogue turns."""
    sample_conv = {
        "title": "Incident War Room",
        "started_at": "2026-10-28T14:15:00Z",
        "messages": [
            {"user": "bot", "text": "ALERT: error rate spike"},
            {"user": "dev", "text": "Investigating payment API timeout"},
            {"user": "lead", "text": "DB pool max size fixed to 50"},
            {"user": "dev", "text": "Hotfix deployed. Error back to normal."},
        ],
    }

    chunks = chunker.chunk_conversation(
        conversation_dict=sample_conv,
        source_id="conv-incident-war-room",
        record_id="INC-88912",
        authority_level=0.80,
        file_path="data/conversations/incident_war_room_chat.json",
    )

    assert len(chunks) == 2  # 4 messages grouped by pairs of 2
    assert "Incident War Room" in chunks[0].title
    assert "bot" in chunks[0].content
    assert "dev" in chunks[0].content
    assert chunks[0].created_at == "2026-10-28T14:15:00Z"
    assert chunks[0].source_type == SourceType.CONVERSATIONS.value


def test_ticket_chunking(chunker):
    """Test structured formatting of bug and support tickets."""
    sample_ticket = {
        "ticket_id": "ENG-4029",
        "type": "Bug",
        "title": "Payment API connection timeout",
        "status": "Closed",
        "priority": "P0 - Critical",
        "description": "Payments failing with 504 gateway timeout post deployment.",
        "resolution": "Increased pool limit to 50.",
        "labels": ["payment", "api", "timeout"],
        "created_at": "2026-10-29T10:00:00Z",
    }

    chunks = chunker.chunk_ticket(
        ticket_dict=sample_ticket,
        source_id="tkt-jira-bugs",
        record_id="ENG-4029",
        authority_level=0.86,
    )

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.record_id == "ENG-4029"
    assert "P0 - Critical" in chunk.content
    assert "Increased pool limit to 50" in chunk.content
    assert chunk.metadata.get("priority") == "P0 - Critical"


def test_ingestion_service_real_files():
    """Test running ingestion across the project's actual local data files."""
    store = InMemoryChunkStore()
    service = IngestionService(chunk_store=store)
    report = service.run_ingestion(clear_existing=True)

    assert report.total_files_discovered >= 7
    assert report.files_successfully_processed >= 7
    assert report.total_chunks > 0
    assert len(report.errors) == 0
    assert store.count() == report.total_chunks

    # Check that chunks from all three source categories exist
    all_chunks = store.get_all_chunks()
    types = {c.source_type for c in all_chunks}
    assert SourceType.DOCUMENTS.value in types
    assert SourceType.CONVERSATIONS.value in types
    assert SourceType.TICKETS.value in types


def test_ingestion_malformed_and_empty_file_resilience():
    """Verify ingestion gracefully handles corrupt or empty files without crashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        docs_dir = tmp_path / "documents"
        docs_dir.mkdir()

        # 1. Valid markdown
        (docs_dir / "valid.md").write_text("# Valid\n\nContent here.", encoding="utf-8")

        # 2. Empty file
        (docs_dir / "empty.md").write_text("", encoding="utf-8")

        # 3. Malformed JSON
        (docs_dir / "corrupt.json").write_text("{ unclosed json: ", encoding="utf-8")

        store = InMemoryChunkStore()
        service = IngestionService(chunk_store=store, data_root=tmp_path)
        report = service.run_ingestion(clear_existing=True)

        assert report.total_files_discovered == 3
        assert report.files_successfully_processed == 1
        assert report.files_skipped == 2
        assert any("corrupt.json" in err for err in report.errors)
        assert any("empty.md" in warn for warn in report.warnings)
        assert store.count() > 0


def test_duplicate_reingestion_idempotence():
    """Verify re-ingesting twice clears duplicates and produces consistent state."""
    store = InMemoryChunkStore()
    service = IngestionService(chunk_store=store)

    rep1 = service.run_ingestion(clear_existing=True)
    count1 = store.count()

    rep2 = service.run_ingestion(clear_existing=True)
    count2 = store.count()

    assert count1 == count2
    assert rep1.total_chunks == rep2.total_chunks
