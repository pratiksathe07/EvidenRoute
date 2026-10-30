"""
EvidenRoute Intelligence Package
Core modules for query understanding, source registry, explainable source selection,
passage chunking, hybrid retrieval, and multi-dimensional evidence scoring.
"""

from .models import (
    ChunkData,
    EvidencePassage,
    EvidenceScore,
    EvidenceScoringConfig,
    IngestionReport,
    PipelineDecisionTrace,
    QueryAnalysisResult,
    RetrievalConfig,
    RetrievalDecisionTrace,
    SelectionConfig,
    SourceMetadata,
    SourceRankResult,
    AnswerReadinessResult,
    ConflictDetectionResult,
    ConflictReport,
    ConflictSeverity,
    ConflictType,
    ConflictingPassageRef,
    DetectConflictsRequest,
    EvaluateEvidenceRequest,
    EvaluateEvidenceResponse,
    EvidenceSufficiencyResult,
    PrunedContextResult,
    PruningDetail,
    PruneContextRequest,
    RecommendedAction,
    SufficiencyStatus,
)
from .query_analyzer import QueryAnalyzer
from .source_registry import SourceRegistry, InMemorySourceRegistry, BaseSourceRegistry
from .source_selector import SourceSelector
from .pipeline import IntelligencePipeline
from .storage import ChunkStore, InMemoryChunkStore, BaseChunkStore
from .chunker import DocumentChunker
from .ingestion import IngestionService
from .retriever import BM25Retriever
from .embedding_provider import EmbeddingProvider, SentenceTransformerEmbeddingProvider, BaseEmbeddingProvider
from .evidence_scorer import EvidenceScorer
from .conflict_detector import ConflictDetector
from .sufficiency_evaluator import SufficiencyEvaluator
from .context_pruner import ContextPruner
from .answer_readiness import AnswerReadinessEvaluator
from .retrieval_pipeline import RetrievalPipeline

__all__ = [
    # Models
    "ChunkData",
    "EvidencePassage",
    "EvidenceScore",
    "EvidenceScoringConfig",
    "IngestionReport",
    "PipelineDecisionTrace",
    "QueryAnalysisResult",
    "RetrievalConfig",
    "RetrievalDecisionTrace",
    "SelectionConfig",
    "SourceMetadata",
    "SourceRankResult",
    "SourceScoreBreakdown",
    "AnswerReadinessResult",
    "ConflictDetectionResult",
    "ConflictReport",
    "ConflictSeverity",
    "ConflictType",
    "ConflictingPassageRef",
    "DetectConflictsRequest",
    "EvaluateEvidenceRequest",
    "EvaluateEvidenceResponse",
    "EvidenceSufficiencyResult",
    "PrunedContextResult",
    "PruningDetail",
    "PruneContextRequest",
    "RecommendedAction",
    "SufficiencyStatus",
    # Engines & Services
    "QueryAnalyzer",
    "SourceRegistry",
    "InMemorySourceRegistry",
    "BaseSourceRegistry",
    "SourceSelector",
    "IntelligencePipeline",
    "ChunkStore",
    "InMemoryChunkStore",
    "BaseChunkStore",
    "DocumentChunker",
    "IngestionService",
    "BM25Retriever",
    "EmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "BaseEmbeddingProvider",
    "EvidenceScorer",
    "ConflictDetector",
    "SufficiencyEvaluator",
    "ContextPruner",
    "AnswerReadinessEvaluator",
    "RetrievalPipeline",
]

