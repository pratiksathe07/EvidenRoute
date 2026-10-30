from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.database.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class SourceModel(Base):
    """
    Persistent registry of information sources configured in the system.
    """
    __tablename__ = "sources"

    source_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False)  # document, conversation, ticket, etc.
    description = Column(Text, nullable=False)
    default_authority = Column(Float, default=0.5, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    records = relationship("RecordModel", back_populates="source", cascade="all, delete-orphan")


class RecordModel(Base):
    """
    Ingested evidence records or chunks belonging to a registered source.
    """
    __tablename__ = "records"

    record_id = Column(String(128), primary_key=True, index=True)
    source_id = Column(String(64), ForeignKey("sources.source_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    uri = Column(String(512), nullable=True)
    author = Column(String(128), nullable=True)
    authority_score = Column(Float, default=0.5, nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("SourceModel", back_populates="records")


class QueryRunModel(Base):
    """
    Audit log of executed query runs, recording decisions, budget consumed, and outcome.
    """
    __tablename__ = "query_runs"

    query_id = Column(String(64), primary_key=True, index=True)
    question = Column(Text, nullable=False)
    outcome = Column(String(32), nullable=False)  # ANSWER, RETRIEVE_MORE, ABSTAIN
    final_answer = Column(Text, nullable=True)
    abstention_reason = Column(Text, nullable=True)

    # Budget tracking
    budget_calls_max = Column(Integer, nullable=False)
    budget_calls_consumed = Column(Integer, nullable=False)
    budget_candidates_max = Column(Integer, nullable=False)
    budget_candidates_consumed = Column(Integer, nullable=False)
    budget_tokens_max = Column(Integer, nullable=False)
    budget_tokens_consumed = Column(Integer, nullable=False)

    # Evidence Stress Test result
    stress_test_executed = Column(Boolean, default=False, nullable=False)
    stress_test_impact = Column(String(64), default="none", nullable=False)
    stress_test_summary = Column(Text, nullable=True)

    # Full execution trace serialized as JSON
    trace_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    retrieval_logs = relationship("RetrievalLogModel", back_populates="query_run", cascade="all, delete-orphan")
    evidence_results = relationship("EvidenceResultModel", back_populates="query_run", cascade="all, delete-orphan")
    contradictions = relationship("ContradictionModel", back_populates="query_run", cascade="all, delete-orphan")


class RetrievalLogModel(Base):
    """
    Logs source selection choices (selected vs rejected) per query run.
    """
    __tablename__ = "retrieval_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(64), ForeignKey("query_runs.query_id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(64), nullable=False)
    selected = Column(Boolean, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    reason = Column(Text, nullable=False)
    candidates_retrieved = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    query_run = relationship("QueryRunModel", back_populates="retrieval_logs")


class EvidenceResultModel(Base):
    """
    Evaluated evidence chunks associated with a query run.
    """
    __tablename__ = "evidence_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(64), ForeignKey("query_runs.query_id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(128), nullable=False)
    source_id = Column(String(64), nullable=False)
    relevance_score = Column(Float, nullable=False)
    authority_score = Column(Float, nullable=False)
    freshness_score = Column(Float, nullable=False)
    directness_score = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    cited = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    query_run = relationship("QueryRunModel", back_populates="evidence_results")


class ContradictionModel(Base):
    """
    Records conflicts detected between evidence chunks during a query run.
    """
    __tablename__ = "contradictions"

    conflict_id = Column(String(64), primary_key=True, index=True)
    query_id = Column(String(64), ForeignKey("query_runs.query_id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_a_id = Column(String(128), nullable=False)
    evidence_b_id = Column(String(128), nullable=False)
    contradiction_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), default="medium", nullable=False)
    resolution_status = Column(String(32), default="unresolved", nullable=False)

    query_run = relationship("QueryRunModel", back_populates="contradictions")
