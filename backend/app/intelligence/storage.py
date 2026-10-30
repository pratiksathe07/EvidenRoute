"""
EvidenRoute - Chunk Storage & Evidence Repository Interface
Decouples retrieval and ingestion from underlying database storage.

Member 1 Compatibility Note:
Defines BaseChunkStore interface.
Phase 2 provides InMemoryChunkStore for local-first execution.
Member 1 can later drop in a PostgreSQLChunkStore / pgvector adapter
implementing the same contract without changing the retriever or evidence scorer.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from .models import ChunkData


class BaseChunkStore(ABC):
    """Abstract interface for knowledge chunk storage and retrieval."""

    @abstractmethod
    def save_chunks(self, chunks: List[ChunkData]) -> None:
        """Store or update chunks in the repository."""
        pass

    @abstractmethod
    def get_chunks_by_source_ids(self, source_ids: List[str]) -> List[ChunkData]:
        """Fetch chunks strictly belonging to the given source IDs."""
        pass

    @abstractmethod
    def get_all_chunks(self) -> List[ChunkData]:
        """Return all stored chunks."""
        pass

    @abstractmethod
    def get_chunk_by_id(self, chunk_id: str) -> Optional[ChunkData]:
        """Fetch a single chunk by its deterministic chunk_id."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored chunks."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the store (useful for tests or re-ingestion)."""
        pass


class InMemoryChunkStore(BaseChunkStore):
    """
    In-memory chunk repository with fast source_id indexing.
    Thread-safe dictionary implementation for local-first Phase 2.
    """

    def __init__(self):
        self._chunks_by_id: Dict[str, ChunkData] = {}
        self._source_index: Dict[str, List[str]] = {}

    def save_chunks(self, chunks: List[ChunkData]) -> None:
        for chunk in chunks:
            self._chunks_by_id[chunk.chunk_id] = chunk
            if chunk.source_id not in self._source_index:
                self._source_index[chunk.source_id] = []
            if chunk.chunk_id not in self._source_index[chunk.source_id]:
                self._source_index[chunk.source_id].append(chunk.chunk_id)

    def get_chunks_by_source_ids(self, source_ids: List[str]) -> List[ChunkData]:
        target_ids = set(source_ids)
        result: List[ChunkData] = []
        for s_id in target_ids:
            chunk_ids = self._source_index.get(s_id, [])
            for c_id in chunk_ids:
                if c_id in self._chunks_by_id:
                    result.append(self._chunks_by_id[c_id])
        return result

    def get_all_chunks(self) -> List[ChunkData]:
        return list(self._chunks_by_id.values())

    def get_chunk_by_id(self, chunk_id: str) -> Optional[ChunkData]:
        return self._chunks_by_id.get(chunk_id)

    def count(self) -> int:
        return len(self._chunks_by_id)

    def clear(self) -> None:
        self._chunks_by_id.clear()
        self._source_index.clear()


# Global in-memory instance
ChunkStore = InMemoryChunkStore()
