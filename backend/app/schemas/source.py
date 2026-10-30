from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.evidence import SourceType


class SourceRegistration(BaseModel):
    """
    Metadata for registering or configuring an information source.
    """
    source_id: str = Field(..., description="Unique alphanumeric identifier")
    name: str = Field(..., description="Human-readable name")
    source_type: SourceType = Field(..., description="Category of the source")
    description: str = Field(..., description="Detailed description of coverage and contents")
    default_authority: float = Field(0.5, ge=0.0, le=1.0, description="Base trust / authority score")
    enabled: bool = Field(True, description="Whether this source is currently active")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceInfo(SourceRegistration):
    """
    Runtime operational status of a registered source.
    """
    record_count: int = Field(0, description="Number of ingested records/chunks")
    last_ingested_at: Optional[datetime] = None
    status: str = Field("healthy", description="Health status (healthy, degraded, offline)")


class SourceSelectionDecision(BaseModel):
    """
    Transparent record of whether a source was queried or rejected, and why.
    """
    source_id: str
    selected: bool
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., description="Explanation for selection or rejection")
    allocated_limit: int = Field(0, description="Max candidate chunks allocated to this source")
