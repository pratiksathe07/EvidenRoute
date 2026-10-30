"""
EvidenRoute - Document Chunker
Splits markdown documents, conversation transcripts, and tickets into
normalized, sentence-aware passages with deterministic chunk IDs.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional
from .models import ChunkData, SourceType


def generate_deterministic_chunk_id(
    source_id: str, record_id: str, chunk_index: int, content: str
) -> str:
    """Generate stable, reproducible SHA-256 hash for a passage chunk."""
    seed = f"{source_id}::{record_id}::{chunk_index}::{content[:80].strip()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


class DocumentChunker:
    """
    Sentence-aware, structure-preserving chunker for heterogeneous enterprise data formats.
    """

    def __init__(self, max_chunk_chars: int = 600, overlap_chars: int = 100):
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_markdown(
        self,
        raw_text: str,
        source_id: str,
        source_type: str = SourceType.DOCUMENTS.value,
        record_id: str = "doc",
        authority_level: float = 0.90,
        file_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> List[ChunkData]:
        """
        Split markdown by structural headers (## ) and paragraphs, preserving section headers.
        """
        if not raw_text or not raw_text.strip():
            return []

        meta = metadata or {}
        # Extract document title from first # Header if available
        doc_title = record_id
        first_header_match = re.search(r"^#\s+(.+)$", raw_text, re.MULTILINE)
        if first_header_match:
            doc_title = first_header_match.group(1).strip()

        # Split by markdown headers
        sections = re.split(r"(?m)^(?=##\s+)", raw_text)
        chunks: List[ChunkData] = []
        chunk_idx = 0

        for section in sections:
            sec_clean = section.strip()
            if not sec_clean:
                continue

            # Determine section subtitle
            sec_title = doc_title
            sec_header_match = re.search(r"^##\s+(.+)$", sec_clean, re.MULTILINE)
            if sec_header_match:
                sec_title = f"{doc_title} — {sec_header_match.group(1).strip()}"

            # If section fits within max_chunk_chars, keep as single chunk
            if len(sec_clean) <= self.max_chunk_chars:
                chunk_id = generate_deterministic_chunk_id(source_id, record_id, chunk_idx, sec_clean)
                chunks.append(
                    ChunkData(
                        chunk_id=chunk_id,
                        source_id=source_id,
                        source_type=source_type,
                        record_id=record_id,
                        title=sec_title,
                        content=sec_clean,
                        created_at=created_at,
                        updated_at=updated_at,
                        authority_level=authority_level,
                        original_file_path=file_path,
                        chunk_index=chunk_idx,
                        metadata=meta,
                    )
                )
                chunk_idx += 1
            else:
                # Split section across paragraph / sentence boundaries
                sub_passages = self._split_text_into_passages(sec_clean)
                for passage in sub_passages:
                    if not passage.strip():
                        continue
                    chunk_id = generate_deterministic_chunk_id(source_id, record_id, chunk_idx, passage)
                    chunks.append(
                        ChunkData(
                            chunk_id=chunk_id,
                            source_id=source_id,
                            source_type=source_type,
                            record_id=record_id,
                            title=sec_title,
                            content=passage.strip(),
                            created_at=created_at,
                            updated_at=updated_at,
                            authority_level=authority_level,
                            original_file_path=file_path,
                            chunk_index=chunk_idx,
                            metadata=meta,
                        )
                    )
                    chunk_idx += 1

        return chunks

    def chunk_conversation(
        self,
        conversation_dict: Dict[str, Any],
        source_id: str,
        record_id: str,
        authority_level: float = 0.82,
        file_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkData]:
        """
        Group dialogue turns into coherent conversational passages.
        """
        title = conversation_dict.get("title", conversation_dict.get("channel", record_id))
        created_at = conversation_dict.get("date", conversation_dict.get("started_at"))
        raw_turns = conversation_dict.get("transcript") or conversation_dict.get("messages") or []

        if not raw_turns:
            return []

        # Group conversation by 2-3 dialogue turns
        chunks: List[ChunkData] = []
        turn_window_size = 2
        chunk_idx = 0

        for i in range(0, len(raw_turns), turn_window_size):
            window = raw_turns[i : i + turn_window_size]
            lines = [f"[{title}]"]
            if "attendees" in conversation_dict:
                lines.append(f"Attendees: {', '.join(conversation_dict['attendees'])}")

            for item in window:
                speaker = item.get("speaker") or item.get("user") or "Unknown"
                text = item.get("text") or ""
                lines.append(f"{speaker}: {text}")

            passage = "\n".join(lines).strip()
            chunk_id = generate_deterministic_chunk_id(source_id, record_id, chunk_idx, passage)

            chunks.append(
                ChunkData(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    source_type=SourceType.CONVERSATIONS.value,
                    record_id=record_id,
                    title=f"{title} (Part {chunk_idx + 1})",
                    content=passage,
                    created_at=created_at,
                    updated_at=None,
                    authority_level=authority_level,
                    original_file_path=file_path,
                    chunk_index=chunk_idx,
                    metadata=metadata or {},
                )
            )
            chunk_idx += 1

        return chunks

    def chunk_ticket(
        self,
        ticket_dict: Dict[str, Any],
        source_id: str,
        record_id: str,
        authority_level: float = 0.86,
        file_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkData]:
        """
        Format ticket record (title, priority, description, resolution) into coherent passages.
        """
        ticket_id = ticket_dict.get("ticket_id", record_id)
        title = ticket_dict.get("title", f"Ticket {ticket_id}")
        t_type = ticket_dict.get("type", "Issue")
        priority = ticket_dict.get("priority", "Normal")
        status = ticket_dict.get("status", "Open")
        desc = ticket_dict.get("description", "")
        resolution = ticket_dict.get("resolution", "Unresolved")
        labels = ticket_dict.get("labels", [])
        created_at = ticket_dict.get("created_at")
        updated_at = ticket_dict.get("updated_at")

        # Assemble unified ticket passage
        content_lines = [
            f"Ticket ID: {ticket_id} ({t_type}) - Priority: {priority} - Status: {status}",
            f"Title: {title}",
            f"Description: {desc}",
        ]
        if resolution:
            content_lines.append(f"Resolution / Fix: {resolution}")
        if labels:
            content_lines.append(f"Labels: {', '.join(labels)}")

        full_content = "\n".join(content_lines).strip()
        chunk_id = generate_deterministic_chunk_id(source_id, ticket_id, 0, full_content)

        return [
            ChunkData(
                chunk_id=chunk_id,
                source_id=source_id,
                source_type=SourceType.TICKETS.value,
                record_id=ticket_id,
                title=f"{ticket_id}: {title}",
                content=full_content,
                created_at=created_at,
                updated_at=updated_at,
                authority_level=authority_level,
                original_file_path=file_path,
                chunk_index=0,
                metadata={
                    **(metadata or {}),
                    "priority": priority,
                    "status": status,
                    "labels": labels,
                },
            )
        ]

    def _split_text_into_passages(self, text: str) -> List[str]:
        """Split text along paragraph or sentence boundaries with overlap."""
        paragraphs = text.split("\n\n")
        passages: List[str] = []
        current = ""

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            if not current:
                current = p_clean
            elif len(current) + len(p_clean) + 2 <= self.max_chunk_chars:
                current += "\n\n" + p_clean
            else:
                passages.append(current)
                # Overlap tail of current if helpful
                current = p_clean

        if current:
            passages.append(current)

        return passages
