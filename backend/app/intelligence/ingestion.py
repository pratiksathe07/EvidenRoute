"""
EvidenRoute - Knowledge Ingestion Service
Discovers, parses, and ingests enterprise data from local repositories
into normalized passages stored in BaseChunkStore.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .chunker import DocumentChunker
from .models import ChunkData, IngestionReport, SourceType
from .source_registry import BaseSourceRegistry, SourceRegistry
from .storage import BaseChunkStore, ChunkStore


# Mapping from standard filenames to registered source IDs in SourceRegistry
DEFAULT_FILE_SOURCE_MAPPING: Dict[str, str] = {
    # Documents
    "payment_api_spec.md": "doc-api-gateway",
    "db_troubleshooting_guide.md": "doc-db-architecture",
    "employee_leave_handbook.md": "doc-hr-policies",
    # Conversations
    "planning_meeting_transcript.json": "conv-product-planning",
    "incident_war_room_chat.json": "conv-incident-war-room",
    # Tickets
    "jira_bug_payment_failure.json": "tkt-jira-bugs",
    "jira_bug_db_timeout.json": "tkt-jira-bugs",
}


class IngestionService:
    """
    Ingests local enterprise data files into the chunk repository.
    """

    def __init__(
        self,
        chunk_store: Optional[BaseChunkStore] = None,
        source_registry: Optional[BaseSourceRegistry] = None,
        chunker: Optional[DocumentChunker] = None,
        data_root: Optional[Path] = None,
    ):
        self.chunk_store = chunk_store or ChunkStore
        self.source_registry = source_registry or SourceRegistry
        self.chunker = chunker or DocumentChunker()
        
        # Default data directory: project root / data
        if data_root is not None:
            self.data_root = Path(data_root)
        else:
            # Infer relative to backend location
            backend_app_dir = Path(__file__).resolve().parent.parent.parent
            self.data_root = backend_app_dir.parent / "data"

    def run_ingestion(self, clear_existing: bool = True) -> IngestionReport:
        """
        Scan data directories, parse documents, and save chunks to storage.
        """
        if clear_existing:
            self.chunk_store.clear()

        total_discovered = 0
        total_processed = 0
        total_skipped = 0
        total_records = 0
        total_chunks = 0
        errors: List[str] = []
        warnings: List[str] = []

        if not self.data_root.exists():
            return IngestionReport(
                total_files_discovered=0,
                files_successfully_processed=0,
                files_skipped=0,
                total_records=0,
                total_chunks=0,
                errors=[f"Data directory '{self.data_root}' does not exist."],
                warnings=[],
                ingested_at=datetime.now(timezone.utc).isoformat(),
            )

        # 1. Discover all candidate files
        candidate_files: List[Path] = []
        for root, _, files in os.walk(self.data_root):
            for f in files:
                if f.endswith((".md", ".json", ".txt")):
                    candidate_files.append(Path(root) / f)

        total_discovered = len(candidate_files)

        # 2. Process each file
        all_new_chunks: List[ChunkData] = []

        for file_path in candidate_files:
            try:
                # Check empty file
                if file_path.stat().st_size == 0:
                    total_skipped += 1
                    warnings.append(f"Skipped empty file: {file_path.name}")
                    continue

                source_id = self._resolve_source_id(file_path)
                source_meta = self.source_registry.get_source(source_id)
                authority = source_meta.authority_level if source_meta else 0.80

                # Read content
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                if not raw_content.strip():
                    total_skipped += 1
                    warnings.append(f"Skipped whitespace-only file: {file_path.name}")
                    continue

                # Determine parser by extension and directory
                chunks: List[ChunkData] = []
                record_id = file_path.stem

                if file_path.suffix == ".md":
                    # Markdown document
                    created_at = (
                        source_meta.metadata.get("last_updated")
                        if source_meta and source_meta.metadata
                        else None
                    )
                    chunks = self.chunker.chunk_markdown(
                        raw_text=raw_content,
                        source_id=source_id,
                        source_type=SourceType.DOCUMENTS.value,
                        record_id=record_id,
                        authority_level=authority,
                        file_path=str(file_path.relative_to(self.data_root.parent) if self.data_root.parent in file_path.parents else file_path),
                        created_at=created_at,
                    )
                elif file_path.suffix == ".json":
                    # Parse JSON safely
                    try:
                        data_json = json.loads(raw_content)
                    except json.JSONDecodeError as jde:
                        total_skipped += 1
                        errors.append(f"Malformed JSON in {file_path.name}: {str(jde)}")
                        continue

                    # Decide if conversation or ticket based on directory or schema
                    if "conversation" in str(file_path).lower() or "transcript" in data_json or "messages" in data_json:
                        chunks = self.chunker.chunk_conversation(
                            conversation_dict=data_json,
                            source_id=source_id,
                            record_id=record_id,
                            authority_level=authority,
                            file_path=str(file_path.relative_to(self.data_root.parent) if self.data_root.parent in file_path.parents else file_path),
                        )
                    else:
                        # Ticket record
                        chunks = self.chunker.chunk_ticket(
                            ticket_dict=data_json,
                            source_id=source_id,
                            record_id=record_id,
                            authority_level=authority,
                            file_path=str(file_path.relative_to(self.data_root.parent) if self.data_root.parent in file_path.parents else file_path),
                        )

                if chunks:
                    all_new_chunks.extend(chunks)
                    total_records += 1
                    total_chunks += len(chunks)
                    total_processed += 1
                else:
                    total_skipped += 1
                    warnings.append(f"No valid passages generated from {file_path.name}")

            except Exception as ex:
                total_skipped += 1
                errors.append(f"Error processing {file_path.name}: {str(ex)}")

        # 3. Save into chunk store
        self.chunk_store.save_chunks(all_new_chunks)

        return IngestionReport(
            total_files_discovered=total_discovered,
            files_successfully_processed=total_processed,
            files_skipped=total_skipped,
            total_records=total_records,
            total_chunks=total_chunks,
            errors=errors,
            warnings=warnings,
            ingested_at=datetime.now(timezone.utc).isoformat(),
        )

    def _resolve_source_id(self, file_path: Path) -> str:
        """Resolve parent source_id using predefined map or directory category."""
        fname = file_path.name
        if fname in DEFAULT_FILE_SOURCE_MAPPING:
            return DEFAULT_FILE_SOURCE_MAPPING[fname]

        # Fallback heuristic based on folder
        parent_folder = file_path.parent.name.lower()
        if "document" in parent_folder:
            return f"doc-{file_path.stem}"
        elif "conversation" in parent_folder:
            return f"conv-{file_path.stem}"
        elif "ticket" in parent_folder:
            return f"tkt-{file_path.stem}"
        return f"src-{file_path.stem}"
