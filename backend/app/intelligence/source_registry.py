"""
EvidenRoute - Local Source Registry
In-memory knowledge source registry containing realistic fictional metadata
for Documents, Conversations, and Tickets.

Architecture Note:
Defines an abstract BaseSourceRegistry interface.
Phase 1 uses InMemorySourceRegistry.
This allows Member 1 to seamlessly implement a PostgreSQLSourceRegistry adapter
later without breaking the SourceSelector or Pipeline contracts.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from .models import SourceMetadata, SourceType


class BaseSourceRegistry(ABC):
    """Abstract interface for source metadata access."""

    @abstractmethod
    def list_sources(self) -> List[SourceMetadata]:
        """Return all registered source metadata entries."""
        pass

    @abstractmethod
    def get_source(self, source_id: str) -> Optional[SourceMetadata]:
        """Fetch a specific source by its identifier."""
        pass

    @abstractmethod
    def add_source(self, source: SourceMetadata) -> None:
        """Register a new source metadata entry."""
        pass

    @abstractmethod
    def update_availability(self, source_id: str, available: bool) -> bool:
        """Update availability status of a source."""
        pass


# Default realistic local sources
SEED_SOURCES: List[SourceMetadata] = [
    # -------------------------------------------------------------
    # Category 1: Documents
    # -------------------------------------------------------------
    SourceMetadata(
        source_id="doc-api-gateway",
        source_name="Payment & API Gateway Technical Specifications",
        source_type=SourceType.DOCUMENTS.value,
        description="Official technical documentation covering payment API endpoints, deployment configs, request limits, and error codes.",
        authority_level=0.95,
        supported_topics=[
            "payment", "api", "payment api", "deployment", "endpoints", "latency",
            "authentication", "webhooks", "gateway", "error codes"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.92,
            "format": "markdown",
            "doc_count": 48,
            "last_updated": "2026-10-25"
        }
    ),
    SourceMetadata(
        source_id="doc-db-architecture",
        source_name="PostgreSQL Database Architecture & Troubleshooting Manual",
        source_type=SourceType.DOCUMENTS.value,
        description="Detailed guide to cluster setup, connection pool limits, timeout handling, query tuning, and database failure recovery.",
        authority_level=0.90,
        supported_topics=[
            "database", "postgresql", "connection timeout", "timeout", "pool",
            "query", "replication", "cluster", "performance", "resolve"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.88,
            "format": "markdown",
            "doc_count": 32,
            "last_updated": "2026-09-18"
        }
    ),
    SourceMetadata(
        source_id="doc-hr-policies",
        source_name="Global Employee Handbook & HR Policies",
        source_type=SourceType.DOCUMENTS.value,
        description="Company policy repository covering employee leave policy, PTO, sick days, code of conduct, remote work, and benefits.",
        authority_level=0.98,
        supported_topics=[
            "employee leave policy", "leave policy", "policy", "pto", "vacation",
            "sick leave", "benefits", "conduct", "handbook", "hr"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.85,
            "format": "pdf_text",
            "doc_count": 14,
            "last_updated": "2026-08-01"
        }
    ),
    SourceMetadata(
        source_id="doc-product-arch",
        source_name="Core Product System Architecture & Service Topology",
        source_type=SourceType.DOCUMENTS.value,
        description="High-level architecture blueprints, microservice diagrams, deployment pipelines, and inter-service dependencies.",
        authority_level=0.88,
        supported_topics=[
            "architecture", "microservices", "deployment", "pipeline",
            "infrastructure", "overview", "product"
        ],
        availability=True,
        metadata={
            # Intentionally None to test missing historical usefulness normalization
            "historical_usefulness": None,
            "format": "markdown",
            "doc_count": 22,
            "last_updated": "2026-10-10"
        }
    ),

    # -------------------------------------------------------------
    # Category 2: Conversations
    # -------------------------------------------------------------
    SourceMetadata(
        source_id="conv-product-planning",
        source_name="Product Planning & Roadmap Strategy Transcripts",
        source_type=SourceType.CONVERSATIONS.value,
        description="Transcripts and action items from product planning meetings, quarterly reviews, feature prioritization, and stakeholder decisions.",
        authority_level=0.82,
        supported_topics=[
            "product planning meeting", "decided", "decision", "planning",
            "roadmap", "quarterly", "milestone", "features", "prioritization"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.86,
            "format": "transcript_json",
            "session_count": 45,
            "last_updated": "2026-10-28"
        }
    ),
    SourceMetadata(
        source_id="conv-incident-war-room",
        source_name="Production Incident & Deployment War Room Transcripts",
        source_type=SourceType.CONVERSATIONS.value,
        description="Live chat transcripts from engineering war rooms during recent deployments, payment API outages, and infrastructure incidents.",
        authority_level=0.80,
        supported_topics=[
            "deployment", "payment api", "failing", "api", "incident",
            "outage", "war room", "root cause", "debug", "production"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.89,
            "format": "chat_export",
            "session_count": 18,
            "last_updated": "2026-10-29"
        }
    ),
    SourceMetadata(
        source_id="conv-arch-decisions",
        source_name="Architecture Decision Records (ADR) & Technical Debates",
        source_type=SourceType.CONVERSATIONS.value,
        description="Formal recorded consensus on architecture design decisions, framework adoptions, database scaling, and API protocols.",
        authority_level=0.85,
        supported_topics=[
            "decision", "decided", "adr", "architecture", "database",
            "consensus", "technical decision", "rationale"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.91,
            "format": "markdown_rfc",
            "session_count": 30,
            "last_updated": "2026-09-30"
        }
    ),

    # -------------------------------------------------------------
    # Category 3: Tickets
    # -------------------------------------------------------------
    SourceMetadata(
        source_id="tkt-jira-bugs",
        source_name="Engineering Bug Tracker & Incident Reports",
        source_type=SourceType.TICKETS.value,
        description="Jira-style bug reports, error stack traces, reproduction steps, regression tickets, and patch deployment tracking.",
        authority_level=0.86,
        supported_topics=[
            "bug", "failing", "payment api", "payment", "deployment",
            "database connection timeout", "timeout", "regression", "error", "resolve"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.94,
            "format": "ticket_json",
            "ticket_count": 312,
            "last_updated": "2026-10-30"
        }
    ),
    SourceMetadata(
        source_id="tkt-zendesk-support",
        source_name="Customer Support Escalation & Helpdesk Tickets",
        source_type=SourceType.TICKETS.value,
        description="External customer support tickets, payment gateway error inquiries, service downtime tickets, and user feedback.",
        authority_level=0.74,
        supported_topics=[
            "support", "customer", "payment", "failing", "error", "timeout", "complaint"
        ],
        availability=True,
        metadata={
            "historical_usefulness": 0.70,
            "format": "ticket_json",
            "ticket_count": 520,
            "last_updated": "2026-10-30"
        }
    ),
    SourceMetadata(
        source_id="tkt-legacy-archive",
        source_name="Legacy Deprecated Bug Archive (Offline)",
        source_type=SourceType.TICKETS.value,
        description="Archived historical bug tickets from v1 system. Offline and retained for legal audit compliance only.",
        authority_level=0.60,
        supported_topics=["legacy", "v1", "archive", "old bugs"],
        availability=False,  # Intentionally offline to test unavailable handling!
        metadata={
            "historical_usefulness": 0.40,
            "format": "archive_cold",
            "ticket_count": 1200,
            "last_updated": "2024-01-01"
        }
    ),
]


class InMemorySourceRegistry(BaseSourceRegistry):
    """
    In-memory implementation of the Source Registry.
    Thread-safe dictionary store loaded with default seed sources.
    """

    def __init__(self, sources: Optional[List[SourceMetadata]] = None):
        self._sources: Dict[str, SourceMetadata] = {}
        items = sources if sources is not None else SEED_SOURCES
        for item in items:
            self._sources[item.source_id] = item

    def list_sources(self) -> List[SourceMetadata]:
        return list(self._sources.values())

    def get_source(self, source_id: str) -> Optional[SourceMetadata]:
        return self._sources.get(source_id)

    def add_source(self, source: SourceMetadata) -> None:
        self._sources[source.source_id] = source

    def update_availability(self, source_id: str, available: bool) -> bool:
        if source_id in self._sources:
            src = self._sources[source_id]
            self._sources[source_id] = src.model_copy(update={"availability": available})
            return True
        return False

    def clear(self) -> None:
        """Clear registry for testing empty scenarios."""
        self._sources.clear()

    def reset(self) -> None:
        """Reset registry back to initial seed sources."""
        self._sources = {s.source_id: s for s in SEED_SOURCES}


# Global default instance
SourceRegistry = InMemorySourceRegistry()
