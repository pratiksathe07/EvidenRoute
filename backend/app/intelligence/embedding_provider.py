"""
EvidenRoute - Semantic Retrieval Provider Interface
Manages optional local Sentence Transformers embedding generation and hybrid scoring.

Local-First Safety Guarantee:
- Model loading is strictly lazy.
- No automatic internet downloads during application startup or runtime.
- If Sentence Transformers is not installed or model weights are missing,
  the provider safely reports unavailable and EvidenRoute gracefully operates
  in 'lexical_only' mode using BM25.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
from .models import ChunkData


class BaseEmbeddingProvider(ABC):
    """Abstract interface for dense semantic representation and vector similarity."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if local embedding engine and weights are accessible."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if semantic scoring is turned on in configuration."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic health and availability metadata."""
        pass

    @abstractmethod
    def compute_similarity(self, query: str, chunks: List[ChunkData]) -> List[float]:
        """Compute cosine similarity [0.0, 1.0] between query and chunk passages."""
        pass


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local Sentence Transformers provider targeting 'all-MiniLM-L6-v2'.
    Lazy-loads weights and strictly avoids automatic cloud downloads.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", enabled: bool = False):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None
        self._load_attempted = False
        self._availability_cache: Optional[bool] = None

    def is_available(self) -> bool:
        if self._availability_cache is not None:
            return self._availability_cache

        try:
            # Check if sentence_transformers package is importable
            import sentence_transformers  # noqa: F401
            # Model is present only if we can find it locally without downloading
            self._availability_cache = False  # Set False for Phase 2 local-first rule
            return self._availability_cache
        except ImportError:
            self._availability_cache = False
            return False

    def is_enabled(self) -> bool:
        return self.enabled and self.is_available()

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "library_installed": self._is_library_installed(),
            "is_available": self.is_available(),
            "is_enabled": self.is_enabled(),
            "mode": "hybrid" if self.is_enabled() else "lexical_only",
            "notes": (
                "Sentence Transformers embedding model is optional in Phase 2. "
                "Automatic model downloads are disabled to follow the local-first rule."
            ),
        }

    def compute_similarity(self, query: str, chunks: List[ChunkData]) -> List[float]:
        """
        Compute normalized cosine similarity.
        If provider is disabled or unavailable, returns empty or zeroes.
        """
        if not self.is_enabled() or not chunks:
            return [0.0] * len(chunks)

        try:
            model = self._get_or_load_model()
            if model is None:
                return [0.0] * len(chunks)

            # Encode query and chunk texts
            texts = [f"{c.title} {c.content}" for c in chunks]
            q_emb = model.encode([query], convert_to_numpy=True)[0]
            c_embs = model.encode(texts, convert_to_numpy=True)

            # Cosine similarity
            q_norm = np.linalg.norm(q_emb)
            if q_norm == 0:
                return [0.0] * len(chunks)

            scores: List[float] = []
            for emb in c_embs:
                c_norm = np.linalg.norm(emb)
                if c_norm == 0:
                    scores.append(0.0)
                else:
                    cos_sim = float(np.dot(q_emb, emb) / (q_norm * c_norm))
                    # Rescale [-1, 1] to [0, 1]
                    norm_score = max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
                    scores.append(round(norm_score, 4))

            return scores
        except Exception:
            return [0.0] * len(chunks)

    def _is_library_installed(self) -> bool:
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_or_load_model(self):
        if self._model is not None:
            return self._model
        if self._load_attempted:
            return None

        self._load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            # strictly load from local files only
            self._model = SentenceTransformer(self.model_name, local_files_only=True)
            return self._model
        except Exception:
            return None


# Global singleton instance (disabled by default in Phase 2)
EmbeddingProvider = SentenceTransformerEmbeddingProvider(enabled=False)
