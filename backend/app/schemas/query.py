from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.budget import BudgetConfig, BudgetStatus
from backend.app.schemas.evidence import EvidenceScore, NormalizedEvidence
from backend.app.schemas.source import SourceSelectionDecision


class DecisionOutcome(str, Enum):
    ANSWER = "ANSWER"
    RETRIEVE_MORE = "RETRIEVE_MORE"
    ABSTAIN = "ABSTAIN"


class ContradictionType(str, Enum):
    FACTUAL_DISAGREEMENT = "factual_disagreement"
    TEMPORAL_UPDATE = "temporal_update"
    STATUS_DISAGREEMENT = "status_disagreement"
    PARTIAL_OVERLAP = "partial_overlap"


class ContradictionItem(BaseModel):
    """
    Structured conflict detected between two or more evidence items.
    """
    conflict_id: str
    evidence_a_id: str
    evidence_b_id: str
    contradiction_type: ContradictionType
    description: str = Field(..., description="Details of the discrepancy")
    severity: str = Field("medium", description="critical, high, medium, low")
    resolution_status: str = Field("unresolved", description="unresolved, resolved_by_authority, resolved_by_recency")
    resolution_reasoning: Optional[str] = None


class StressTestResult(BaseModel):
    """
    Details of the bounded counterevidence search executed using remaining budget.
    """
    executed: bool = False
    hypothesis_tested: Optional[str] = None
    verification_query: Optional[str] = None
    counterevidence_found: bool = False
    supporting_evidence_found: bool = False
    evidence_examined_count: int = 0
    budget_used_calls: int = 0
    impact_on_decision: str = Field("none", description="none, overturned_answer, weakened_confidence, confirmed_answer")
    summary: str = Field("Stress test was not requested or budget was exhausted.")


class TraceStep(BaseModel):
    """
    Audit log of each pipeline phase for transparent UI visualization.
    """
    step_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "completed"
    duration_ms: float = 0.0
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    """
    Inbound query payload sent by user or frontend client.
    """
    question: str = Field(..., min_length=3, description="The user query or claim to verify")
    budget: Optional[BudgetConfig] = Field(default_factory=BudgetConfig, description="Optional custom retrieval budget")
    enable_stress_test: bool = Field(True, description="Whether to perform bounded counterevidence check")


class QueryResponse(BaseModel):
    """
    Comprehensive response payload returned by EvidenRoute engine.
    """
    query_id: str
    question: str
    outcome: DecisionOutcome
    final_answer: Optional[str] = Field(None, description="The synthesized answer with citations if ANSWER")
    abstention_reason: Optional[str] = Field(None, description="Explicit justification if ABSTAIN")
    citations: List[str] = Field(default_factory=list, description="IDs of evidence chunks cited")
    selected_sources: List[SourceSelectionDecision] = Field(default_factory=list)
    retrieved_evidence: List[NormalizedEvidence] = Field(default_factory=list)
    evidence_scores: List[EvidenceScore] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    budget_status: BudgetStatus
    stress_test: StressTestResult
    execution_trace: List[TraceStep]
