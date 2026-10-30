from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    TICKET = "ticket"
    WEB = "web"
    DATABASE = "database"


class NormalizedEvidence(BaseModel):
    """
    Standardized schema for all evidence items retrieved from any source adapter.
    Preserves source provenance and metadata.
    """
    evidence_id: str = Field(..., description="Unique ID for this evidence chunk")
    source_id: str = Field(..., description="Identifier of the origin source")
    source_type: SourceType = Field(..., description="Category of the source")
    title: str = Field(..., description="Title or header of the record")
    content: str = Field(..., description="Extracted text content used as evidence")
    uri: Optional[str] = Field(None, description="Direct URI or path to the source item")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last updated timestamp")
    author: Optional[str] = Field(None, description="Originating author or team")
    authority_score: float = Field(0.5, ge=0.0, le=1.0, description="Inherent source authority (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary source metadata")


class EvidenceScore(BaseModel):
    """
    Multi-dimensional evaluation scores for an individual evidence item.
    """
    evidence_id: str
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to the query topic and entities")
    authority_score: float = Field(..., ge=0.0, le=1.0, description="Source reliability and authority")
    freshness_score: float = Field(..., ge=0.0, le=1.0, description="Temporal currency relative to query context")
    directness_score: float = Field(..., ge=0.0, le=1.0, description="Direct answer vs tangential mention")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite score")
    correctness_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Verification measure using supporting corroboration and conflict checks")
    correctness_status: Optional[str] = Field("consistent", description="cross_verified, consistent, unverified_single_source, or contradicted")
    correctness_explanation: Optional[str] = Field(None, description="Explanation of factual consistency or verification")
    evaluation_notes: Optional[str] = Field(None, description="Human-readable explanation of the score")
