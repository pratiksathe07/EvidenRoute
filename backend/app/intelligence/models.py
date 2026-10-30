"""
EvidenRoute - Intelligence Data Models
Pydantic models for structured validation across query analysis,
source registry, scoring breakdown, ranking, and decision traces.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Categorization for information sources."""
    DOCUMENTS = "documents"
    CONVERSATIONS = "conversations"
    TICKETS = "tickets"


class IntentType(str, Enum):
    """Identified purpose of user query."""
    TECHNICAL_TROUBLESHOOTING = "technical_troubleshooting"
    POLICY_LOOKUP = "policy_lookup"
    DECISION_DISCOVERY = "decision_discovery"
    PROJECT_STATUS = "project_status"
    BUG_INVESTIGATION = "bug_investigation"
    GENERAL_INFORMATION_LOOKUP = "general_information_lookup"
    UNCLEAR_QUERY = "unclear_query"


class InformationCategory(str, Enum):
    """Broad domain classification of query context."""
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    GOVERNANCE = "governance"
    PRODUCT = "product"
    OPERATIONAL = "operational"
    GENERAL = "general"


class SelectionStatus(str, Enum):
    """Decision status for whether a source should be searched."""
    SELECTED = "selected"
    SKIPPED = "skipped"


class QueryAnalysisResult(BaseModel):
    """Structured output from QueryAnalyzer."""
    intent: str = Field(..., description="Categorized user intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of classification")
    keywords: List[str] = Field(default_factory=list, description="Extracted key topical words")
    entities: List[str] = Field(default_factory=list, description="Recognized named concepts, systems or entities")
    technical_terms: List[str] = Field(default_factory=list, description="Extracted domain-specific technical jargon")
    information_category: str = Field(..., description="Broad information category (technical, organizational, etc.)")
    expected_information: List[str] = Field(default_factory=list, description="Types of information expected to answer the query")
    likely_source_types: List[str] = Field(default_factory=list, description="Source types likely to contain answers")
    analyzer_type: str = Field(
        default="deterministic_rule_based",
        description="Engine used for analysis. Swappable with Gemini in future phases."
    )
    limitations_note: Optional[str] = Field(
        default="Heuristic/deterministic rule-based extraction. Designed for local execution without cloud API dependencies.",
        description="Transparency statement on model capabilities."
    )


class SourceMetadata(BaseModel):
    """Schema representing an available knowledge source."""
    source_id: str = Field(..., description="Unique alphanumeric identifier")
    source_name: str = Field(..., description="Human-readable source name")
    source_type: str = Field(..., description="Source category (documents, conversations, tickets)")
    description: str = Field(..., description="Detailed description of content and scope")
    authority_level: float = Field(..., ge=0.0, le=1.0, description="Normalized trust/authority score [0.0, 1.0]")
    supported_topics: List[str] = Field(default_factory=list, description="List of topics or domains covered")
    availability: bool = Field(default=True, description="Whether source is online and accessible")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional attributes (e.g. historical_usefulness, freshness, format)"
    )

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_types = {t.value for t in SourceType}
        normalized = v.lower().strip()
        if normalized not in valid_types:
            # Allow custom string but standardize
            return normalized
        return normalized


class SelectionConfig(BaseModel):
    """Configurable scoring weights and selection thresholds."""
    relevance_weight: float = Field(0.35, ge=0.0, le=1.0, description="Weight for topical/lexical relevance")
    suitability_weight: float = Field(0.25, ge=0.0, le=1.0, description="Weight for intent-to-source-type alignment")
    authority_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for source authority/trust level")
    historical_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for historical usefulness score")
    availability_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for source accessibility")
    selection_threshold: float = Field(0.40, ge=0.0, le=1.0, description="Minimum final score required for selection")
    min_relevance_threshold: float = Field(
        0.15,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score required. High authority cannot bypass zero relevance."
    )


class SourceScoreBreakdown(BaseModel):
    """Detailed trace of normalized scores and weights for a source."""
    relevance_score: float
    type_suitability_score: float
    authority_score: float
    historical_usefulness_score: Optional[float]
    availability_score: float
    weights_applied: Dict[str, float]
    calculation_notes: List[str] = Field(default_factory=list)


class SourceRankResult(BaseModel):
    """Explainable ranking and selection verdict for an individual source."""
    source_id: str
    source_name: str
    source_type: str
    relevance_score: float
    type_suitability_score: float
    authority_score: float
    historical_usefulness_score: Optional[float]
    availability_score: float
    final_score: float
    selection_status: str  # "selected" or "skipped"
    selection_reason: str
    ranking_position: int
    score_breakdown: Optional[SourceScoreBreakdown] = None


class PipelineDecisionTrace(BaseModel):
    """Complete end-to-end audit trace of the context selection decision."""
    query: str
    analysis: QueryAnalysisResult
    available_sources_count: int
    evaluated_sources_count: int
    selected_sources_count: int
    skipped_sources_count: int
    ranked_sources: List[SourceRankResult]
    execution_time_ms: float
    config_used: SelectionConfig
    notes: List[str] = Field(default_factory=list)


# --- API Request and Response Models ---

class AnalyzeQueryRequest(BaseModel):
    """Request payload for query analysis."""
    question: str = Field(..., min_length=1, description="User's query string", examples=["Why did the payment API fail?"])


class SelectSourcesRequest(BaseModel):
    """Request payload for source selection given a question."""
    question: str = Field(..., min_length=1, description="User's query string")
    config: Optional[SelectionConfig] = Field(None, description="Optional custom scoring weights and thresholds")
    sources: Optional[List[SourceMetadata]] = Field(None, description="Optional custom source metadata list to evaluate")


class SelectSourcesResponse(BaseModel):
    """Response payload for source selection."""
    question: str
    selected_sources_count: int
    skipped_sources_count: int
    ranked_sources: List[SourceRankResult]


class PlanRequest(BaseModel):
    """Request payload for full pipeline execution (analyze + select)."""
    question: str = Field(..., min_length=1, description="User's query string")
    config: Optional[SelectionConfig] = Field(None, description="Optional custom scoring configuration")


class PlanResponse(BaseModel):
    """Response payload containing full decision trace."""
    decision_trace: PipelineDecisionTrace


class HealthResponse(BaseModel):
    """Health check status response."""
    status: str
    query_analyzer: str
    source_registry: str
    source_selector: str
    external_llm_integration: str
    active_sources_count: int
    environment: str


# ==============================================================
# PHASE 2: CHUNKING, RETRIEVAL & EVIDENCE SCORING MODELS
# ==============================================================

class ChunkData(BaseModel):
    """Normalized representation of an ingested content passage."""
    chunk_id: str = Field(..., description="Deterministic unique SHA-256 hash")
    source_id: str = Field(..., description="Parent source identifier (e.g., doc-api-gateway)")
    source_type: str = Field(..., description="Category: documents, conversations, tickets")
    record_id: str = Field(..., description="Identifier from original record or file")
    title: str = Field(..., description="Human-readable section or record title")
    content: str = Field(..., description="Extracted textual passage")
    created_at: Optional[str] = Field(None, description="ISO timestamp or date string if available")
    updated_at: Optional[str] = Field(None, description="ISO timestamp or date string if available")
    authority_level: float = Field(0.80, ge=0.0, le=1.0, description="Inherited or record-level authority")
    original_file_path: str = Field(..., description="File path or relative record location")
    chunk_index: int = Field(0, ge=0, description="0-indexed position within record")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom attributes, labels, speakers, etc.")


class IngestionReport(BaseModel):
    """Execution report returned after parsing local knowledge directories."""
    total_files_discovered: int
    files_successfully_processed: int
    files_skipped: int
    total_records: int
    total_chunks: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ingested_at: str


class EvidenceScoringConfig(BaseModel):
    """Configurable weights and half-life for evidence scoring."""
    relevance_weight: float = Field(0.35, ge=0.0, le=1.0, description="Weight for retrieval relevance")
    authority_weight: float = Field(0.25, ge=0.0, le=1.0, description="Weight for source trust/authority")
    freshness_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for temporal freshness")
    directness_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for direct question answering")
    freshness_half_life_days: float = Field(180.0, gt=0.0, description="Half-life decay in days for freshness")


class EvidenceScore(BaseModel):
    """Multi-dimensional evidence evaluation breakdown."""
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    authority_score: float = Field(..., ge=0.0, le=1.0)
    freshness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    freshness_status: str = Field(..., description="fresh, decayed, stale, or unknown")
    directness_score: float = Field(..., ge=0.0, le=1.0)
    directness_label: str = Field(..., description="direct, supporting, indirect, or tangential")
    final_evidence_score: float = Field(..., ge=0.0, le=1.0)
    scoring_explanation: str
    weights_applied: Dict[str, float] = Field(default_factory=dict)
    correctness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    correctness_status: Optional[str] = Field("consistent", description="cross_verified, consistent, unverified_single_source, or contradicted")
    correctness_explanation: Optional[str] = Field(None)


class EvidencePassage(BaseModel):
    """Ranked evidence passage returned to downstream synthesis modules."""
    chunk_id: str
    source_id: str
    source_name: str
    source_type: str
    record_id: str
    title: str
    content: str
    authority_level: float
    created_at: Optional[str] = None
    original_file_path: str
    chunk_index: int
    retrieval_score: float
    bm25_score: float
    semantic_score: Optional[float] = None
    retrieval_mode: str  # "lexical_only" or "hybrid"
    evidence_score: EvidenceScore
    citation: str
    ranking_position: int


class RetrievalConfig(BaseModel):
    """Configuration for candidate retrieval and hybrid weighting."""
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of evidence chunks to retrieve")
    bm25_weight: float = Field(0.45, ge=0.0, le=1.0, description="Provisional weight for BM25 lexical score")
    semantic_weight: float = Field(0.55, ge=0.0, le=1.0, description="Provisional weight for semantic cosine similarity")
    enable_semantic: bool = Field(False, description="Whether to attempt semantic embedding similarity")
    evidence_config: EvidenceScoringConfig = Field(default_factory=EvidenceScoringConfig)


# ==============================================================
# PHASE 3: CONFLICT DETECTION, SUFFICIENCY & CONTEXT PRUNING
# ==============================================================

class ConflictType(str, Enum):
    """Categorization of detected evidence divergence or conflict."""
    DIRECT_CONTRADICTION = "direct_contradiction"
    TEMPORAL_SUPERSEDENCE = "temporal_supersedence"
    VERSION_DIVERGENCE = "version_divergence"
    STATUS_PROGRESSION = "status_progression"
    CONTEXTUAL_DIFFERENCE = "contextual_difference"


class ConflictSeverity(str, Enum):
    """Impact severity of detected conflict."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class RecommendedAction(str, Enum):
    """Verdict on next action for downstream answer generation."""
    ANSWER = "answer"
    RETRIEVE_MORE = "retrieve_more"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class SufficiencyStatus(str, Enum):
    """Categorized sufficiency standing."""
    SUFFICIENT = "sufficient"
    PARTIALLY_SUFFICIENT = "partially_sufficient"
    INSUFFICIENT = "insufficient"
    CONFLICTED = "conflicted"


class ConflictingPassageRef(BaseModel):
    """Reference to an individual passage involved in a conflict."""
    chunk_id: str
    source_id: str
    source_name: str
    citation: str
    statement: str
    timestamp: Optional[str] = None


class ConflictReport(BaseModel):
    """Explainable conflict report between two or more evidence passages."""
    conflict_id: str
    conflict_type: str
    topic: str
    is_direct_contradiction: bool
    severity: str
    conflicting_passages: List[ConflictingPassageRef]
    explanation: str
    resolution_hint: Optional[str] = None


class ConflictDetectionResult(BaseModel):
    """Summary output of the conflict detection engine."""
    total_passages_evaluated: int
    conflicts_detected_count: int
    direct_contradictions_count: int
    conflicts: List[ConflictReport] = Field(default_factory=list)
    has_unresolved_contradictions: bool


class EvidenceSufficiencyResult(BaseModel):
    """Structured evaluation of whether retrieved evidence suffices to answer query."""
    is_sufficient: bool
    sufficiency_score: float = Field(..., ge=0.0, le=1.0)
    sufficiency_status: str
    supporting_evidence: List[EvidencePassage] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    conflicts_detected: List[ConflictReport] = Field(default_factory=list)
    explanation: str
    recommended_action: str
    dimension_scores: Dict[str, float] = Field(default_factory=dict)


class PruningDetail(BaseModel):
    """Accounting record for an individual pruned sentence or passage."""
    chunk_id: str
    original_file_path: str
    sentence: str
    reason: str


class PrunedContextResult(BaseModel):
    """Output of budget-aware context deduplication and compression."""
    original_passages_count: int
    retained_passages_count: int
    original_sentence_count: int
    retained_sentence_count: int
    pruned_sentence_count: int
    pruned_details: List[PruningDetail] = Field(default_factory=list)
    retained_evidence: List[EvidencePassage] = Field(default_factory=list)
    conflict_passages_preserved_count: int
    compression_ratio: float


# ==============================================================
# STEP 4: EVIDENCE STRESS TESTING & COUNTER-EVIDENCE MODELS
# ==============================================================

class CounterEvidenceResult(BaseModel):
    """Details of targeted counter-evidence search executed within remaining budget."""
    executed: bool = False
    challenge_query: Optional[str] = None
    counter_evidence_found: bool = False
    supporting_evidence_found: bool = False
    evidence_examined_count: int = 0
    new_passages_retrieved_count: int = 0
    budget_used_calls: int = 0
    budget_exhausted: bool = False
    impact_on_decision: str = Field("none", description="confirmed_answer, weakened_confidence, overturned_answer, none")
    summary: str = Field("Counter-evidence search was not executed or not requested.")
    discovered_passages: List[EvidencePassage] = Field(default_factory=list)


class EvidenceReliabilityStatus(str, Enum):
    """Categorization of overall evidence set reliability."""
    HIGH = "high_reliability"
    MODERATE = "moderate_reliability"
    UNRELIABLE = "unreliable"
    CONTRADICTED = "contradicted"
    INSUFFICIENT = "insufficient"


class EvidenceReliabilityResult(BaseModel):
    """Comprehensive reliability assessment of the combined evidence set."""
    status: str = Field(EvidenceReliabilityStatus.MODERATE.value, description="high_reliability, moderate_reliability, unreliable, contradicted, insufficient")
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    supporting_evidence_count: int = 0
    contradictory_evidence_count: int = 0
    independent_sources_count: int = 0
    independent_source_ids: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence_limitations: List[str] = Field(default_factory=list)
    recommended_action: str = Field("answer", description="answer, retrieve_more, clarify, abstain")
    explanation: str


class StressTestScenarioResult(BaseModel):
    """Structured audit of an individual stress-testing scenario."""
    scenario_id: int
    scenario_name: str
    query: str
    expected_behavior: str
    actual_verdict: str
    decision_outcome: str
    reliability_status: str
    conflicts_detected: int
    counter_evidence_found: bool
    passed: bool
    details: Dict[str, Any] = Field(default_factory=dict)


class StressTestSuiteReport(BaseModel):
    """Aggregated results across all 14 evidence stress-test scenarios."""
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate_pct: float
    results: List[StressTestScenarioResult]
    execution_time_ms: float


class BaselineComparisonMetrics(BaseModel):
    """Measured performance metrics for either Baseline or EvidenRoute."""
    mode: str
    total_queries: int
    average_precision: float
    average_recall: float
    average_relevance: float
    source_selection_accuracy: float
    contradiction_accuracy: float
    sufficiency_accuracy: float
    average_passages_retrieved: float
    average_latency_ms: float
    budget_calls_consumed: int
    budget_tokens_consumed: int
    irrelevant_evidence_reduction_pct: float


class BaselineComparisonReport(BaseModel):
    """Direct comparison between naive full-source retrieval and EvidenRoute engine."""
    baseline_metrics: BaselineComparisonMetrics
    evidenroute_metrics: BaselineComparisonMetrics
    improvements: Dict[str, Any] = Field(default_factory=dict)
    evaluation_timestamp: str


class AnswerReadinessResult(BaseModel):
    """Final answer-readiness determination synthesized across sufficiency, conflicts, and pruning."""
    is_ready_to_answer: bool
    readiness_verdict: str
    recommended_action: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    primary_justification: str
    conflicts_summary: Dict[str, Any] = Field(default_factory=dict)
    sufficiency_summary: Dict[str, Any] = Field(default_factory=dict)
    pruning_summary: Dict[str, Any] = Field(default_factory=dict)
    reliability_summary: Dict[str, Any] = Field(default_factory=dict)


class RetrievalDecisionTrace(BaseModel):
    """Complete audit trace of the retrieval and evidence scoring stage."""
    query: str
    analysis: QueryAnalysisResult
    selected_source_ids: List[str]
    skipped_source_ids: List[str]
    retrieval_mode: str  # "lexical_only" or "hybrid"
    total_candidate_chunks_evaluated: int
    retrieved_evidence_count: int
    retrieved_evidence: List[EvidencePassage]
    execution_time_ms: float
    budget_info: Dict[str, Any] = Field(default_factory=dict)
    trace_stages: List[str] = Field(default_factory=list)
    # Phase 3 Enhancements
    conflicts: List[ConflictReport] = Field(default_factory=list)
    sufficiency: Optional[EvidenceSufficiencyResult] = None
    pruned_context: Optional[PrunedContextResult] = None
    answer_readiness: Optional[AnswerReadinessResult] = None
    # Step 4 Additions
    counter_evidence: Optional[CounterEvidenceResult] = None
    evidence_reliability: Optional[EvidenceReliabilityResult] = None


# --- Phase 2 & 3 API Models ---

class RetrieveRequest(BaseModel):
    """Request payload for Phase 1 + Phase 2 + Phase 3 + Step 4 integrated retrieval."""
    question: str = Field(..., min_length=1, description="User's query string")
    top_k: int = Field(10, ge=1, le=50, description="Maximum evidence passages to return")
    selection_config: Optional[SelectionConfig] = Field(None, description="Optional custom source selection weights")
    retrieval_config: Optional[RetrievalConfig] = Field(None, description="Optional custom retrieval and evidence weights")
    enable_stress_test: bool = Field(False, description="Whether to execute counter-evidence search and reliability evaluation")
    max_budget_calls: Optional[int] = Field(None, description="Optional custom max source calls override")
    max_budget_candidates: Optional[int] = Field(None, description="Optional custom max candidate quota override")


class RetrieveResponse(BaseModel):
    """End-to-end response for query understanding, source selection, and ranked evidence."""
    query: str
    query_analysis: QueryAnalysisResult
    selected_sources: List[str]
    skipped_sources: List[str]
    retrieval_mode: str
    retrieved_evidence: List[EvidencePassage]
    decision_trace: RetrievalDecisionTrace
    # Phase 3 Additions
    conflicts: List[ConflictReport] = Field(default_factory=list)
    sufficiency: Optional[EvidenceSufficiencyResult] = None
    pruned_context: Optional[PrunedContextResult] = None
    answer_readiness: Optional[AnswerReadinessResult] = None
    # Step 4 Additions
    counter_evidence: Optional[CounterEvidenceResult] = None
    evidence_reliability: Optional[EvidenceReliabilityResult] = None


class RetrievalHealthResponse(BaseModel):
    """Detailed health check for ingestion, BM25, and semantic components."""
    status: str
    ingestion_status: Dict[str, Any]
    bm25_status: str
    semantic_model_status: Dict[str, Any]
    active_retrieval_mode: str
    evidence_scorer_status: str


class DetectConflictsRequest(BaseModel):
    """Request payload for standalone conflict detection."""
    passages: Optional[List[EvidencePassage]] = Field(None, description="Optional custom list of passages to evaluate")
    question: Optional[str] = Field(None, description="Optional query string to retrieve and evaluate passages")


class EvaluateEvidenceRequest(BaseModel):
    """Request payload for evidence sufficiency and readiness evaluation."""
    question: str = Field(..., min_length=1, description="User's query string")
    passages: Optional[List[EvidencePassage]] = Field(None, description="Optional pre-retrieved passages")
    top_k: int = Field(10, ge=1, le=50, description="Number of passages if retrieval is performed")


class EvaluateEvidenceResponse(BaseModel):
    """Response payload containing evidence sufficiency, conflicts, pruning, and readiness."""
    question: str
    sufficiency: EvidenceSufficiencyResult
    readiness: AnswerReadinessResult
    conflicts: List[ConflictReport]
    pruned_context: PrunedContextResult


class PruneContextRequest(BaseModel):
    """Request payload for budget-aware context pruning."""
    passages: List[EvidencePassage] = Field(..., description="Passages to deduplicate and prune")
    max_context_chars: Optional[int] = Field(None, ge=100, description="Optional character budget limit")
    conflicts: Optional[List[ConflictReport]] = Field(None, description="Optional detected conflicts to protect from pruning")


