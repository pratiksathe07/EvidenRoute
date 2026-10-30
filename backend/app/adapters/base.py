from abc import ABC, abstractmethod
from typing import List
from backend.app.schemas.evidence import NormalizedEvidence
from backend.app.schemas.source import SourceInfo


class BaseSourceAdapter(ABC):
    """
    Abstract interface that all information source adapters (documents, tickets,
    conversations, external APIs) must implement.
    """

    @abstractmethod
    def describe(self) -> SourceInfo:
        """
        Returns runtime metadata and status of the source.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verifies connectivity and readiness of the underlying source.
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[NormalizedEvidence]:
        """
        Executes a bounded search query against this source, returning normalized evidence chunks.
        """
        pass
