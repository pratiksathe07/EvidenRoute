import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.db import get_db, SessionLocal
from backend.app.database.models import RecordModel, SourceModel
from backend.app.schemas.evidence import SourceType
from backend.app.schemas.source import SourceInfo, SourceRegistration

router = APIRouter(prefix="/api/sources", tags=["sources"])


class IngestRecordRequest(BaseModel):
    record_id: str
    title: str
    content: str
    uri: Optional[str] = None
    author: Optional[str] = None
    authority_score: float = Field(0.5, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestBatchRequest(BaseModel):
    source_id: str
    records: List[IngestRecordRequest]


@router.get("", response_model=List[SourceInfo])
def list_sources(db: Session = Depends(get_db)):
    """
    Returns all registered information sources with their health and record counts.
    """
    sources = db.query(SourceModel).all()
    results = []
    for src in sources:
        count = db.query(RecordModel).filter(RecordModel.source_id == src.source_id).count()
        metadata = {}
        if src.metadata_json:
            try:
                metadata = json.loads(src.metadata_json)
            except Exception:
                pass

        results.append(
            SourceInfo(
                source_id=src.source_id,
                name=src.name,
                source_type=SourceType(src.source_type) if src.source_type in [e.value for e in SourceType] else SourceType.DOCUMENT,
                description=src.description,
                default_authority=src.default_authority,
                enabled=src.enabled,
                record_count=count,
                last_ingested_at=src.updated_at,
                status="healthy" if src.enabled else "disabled",
                metadata=metadata,
            )
        )
    return results


@router.post("", response_model=SourceInfo, status_code=status.HTTP_201_CREATED)
def register_source(payload: SourceRegistration, db: Session = Depends(get_db)):
    """
    Registers a new source in EvidenRoute.
    """
    existing = db.query(SourceModel).filter(SourceModel.source_id == payload.source_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with ID '{payload.source_id}' already exists."
        )

    new_source = SourceModel(
        source_id=payload.source_id,
        name=payload.name,
        source_type=payload.source_type.value,
        description=payload.description,
        default_authority=payload.default_authority,
        enabled=payload.enabled,
        metadata_json=json.dumps(payload.metadata),
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return SourceInfo(
        source_id=new_source.source_id,
        name=new_source.name,
        source_type=payload.source_type,
        description=new_source.description,
        default_authority=new_source.default_authority,
        enabled=new_source.enabled,
        record_count=0,
        last_ingested_at=new_source.created_at,
        status="healthy" if new_source.enabled else "disabled",
        metadata=payload.metadata,
    )


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_records(payload: IngestBatchRequest, db: Session = Depends(get_db)):
    """
    Ingests or updates records for an existing source.
    """
    src = db.query(SourceModel).filter(SourceModel.source_id == payload.source_id).first()
    if not src:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{payload.source_id}' does not exist. Register it first."
        )

    ingested_count = 0
    now = datetime.now(timezone.utc)
    for rec in payload.records:
        existing = db.query(RecordModel).filter(RecordModel.record_id == rec.record_id).first()
        if existing:
            existing.title = rec.title
            existing.content = rec.content
            existing.uri = rec.uri
            existing.author = rec.author
            existing.authority_score = rec.authority_score
            existing.metadata_json = json.dumps(rec.metadata)
            existing.updated_at = rec.updated_at or now
        else:
            new_rec = RecordModel(
                record_id=rec.record_id,
                source_id=payload.source_id,
                title=rec.title,
                content=rec.content,
                uri=rec.uri,
                author=rec.author,
                authority_score=rec.authority_score,
                metadata_json=json.dumps(rec.metadata),
                created_at=rec.created_at or now,
                updated_at=rec.updated_at or now,
            )
            db.add(new_rec)
        ingested_count += 1

    src.updated_at = now
    db.commit()

    total_count = db.query(RecordModel).filter(RecordModel.source_id == payload.source_id).count()
    return {
        "status": "success",
        "source_id": payload.source_id,
        "ingested_in_batch": ingested_count,
        "total_source_records": total_count,
    }


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_sample_sources(db: Session = Depends(get_db)):
    """
    Seeds three standard default sources with realistic test data:
    1. Knowledge Base (Official Docs)
    2. Customer Support Tickets
    3. Team Chat / Conversations
    """
    seed_sources_and_records(db)
    return {"status": "success", "message": "Sample sources seeded successfully."}


def seed_sources_and_records(db: Session):
    """
    Helper function to populate benchmark sources and records.
    """
    sources_data = [
        {
            "source_id": "kb_official_docs",
            "name": "Knowledge Base (Official Docs)",
            "source_type": SourceType.DOCUMENT.value,
            "description": "Official company policies, SLA agreements, and formal user manuals. High authority.",
            "default_authority": 0.95,
        },
        {
            "source_id": "support_tickets",
            "name": "Customer Support Tickets",
            "source_type": SourceType.TICKET.value,
            "description": "Historical resolution logs, edge case troubleshooting, and customer dispute outcomes.",
            "default_authority": 0.75,
        },
        {
            "source_id": "slack_conversations",
            "name": "Internal Team Conversations",
            "source_type": SourceType.CONVERSATION.value,
            "description": "Internal developer & operations Slack threads discussing ongoing updates and workarounds.",
            "default_authority": 0.50,
        },
    ]

    for s_info in sources_data:
        src = db.query(SourceModel).filter(SourceModel.source_id == s_info["source_id"]).first()
        if not src:
            src = SourceModel(**s_info)
            db.add(src)

    db.commit()

    # Records: intentionally includes some scenarios with clear answers, some with outdated data, and some contradictions
    records_data = [
        # Scenario 1: Refund Policy
        {
            "record_id": "doc_policy_refund_v3",
            "source_id": "kb_official_docs",
            "title": "Refund and Cancellation Policy v3.0",
            "content": "All standard software license subscriptions are eligible for a 100% refund within 14 calendar days of initial purchase. Beyond 14 days, no refunds are granted.",
            "uri": "/docs/policies/refunds-v3.md",
            "author": "Billing Policy Team",
            "authority_score": 0.95,
            "created_at": datetime(2025, 1, 10, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 10, tzinfo=timezone.utc),
        },
        {
            "record_id": "ticket_billing_9482",
            "source_id": "support_tickets",
            "title": "Ticket #9482 - Refund requested on day 12",
            "content": "Customer requested full refund on day 12 after purchase. Processed successfully as per standard 14-day policy window.",
            "uri": "/tickets/9482",
            "author": "Support Agent Sarah",
            "authority_score": 0.75,
            "created_at": datetime(2025, 2, 14, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 2, 14, tzinfo=timezone.utc),
        },
        {
            "record_id": "slack_thread_billing_refunds",
            "source_id": "slack_conversations",
            "title": "#billing-general discussion on enterprise exceptions",
            "content": "Dev Dave: Reminder that enterprise SLA accounts get 30 days for evaluation refund, not the standard 14 days listed on the consumer portal.",
            "uri": "slack://billing/p1708000000",
            "author": "Dave (Billing Dev)",
            "authority_score": 0.55,
            "created_at": datetime(2025, 2, 20, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 2, 20, tzinfo=timezone.utc),
        },

        # Scenario 2: Service SLA & Outage Credits
        {
            "record_id": "doc_sla_agreement_2024",
            "source_id": "kb_official_docs",
            "title": "Service Level Agreement (SLA) 2024",
            "content": "EvidenRoute Cloud guarantees 99.9% uptime. If monthly uptime drops below 99.9%, customers receive a 10% billing credit upon submitting a claim within 30 days.",
            "uri": "/docs/sla/sla-2024.md",
            "author": "Legal & Operations",
            "authority_score": 0.90,
            "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        },
        {
            "record_id": "doc_sla_agreement_2025_updated",
            "source_id": "kb_official_docs",
            "title": "Service Level Agreement (SLA) 2025 Revision",
            "content": "Effective Jan 1 2025, EvidenRoute Cloud guarantees 99.95% uptime. For outages breaching 99.95%, credit is 15% and is automatically applied without requiring a manual claim.",
            "uri": "/docs/sla/sla-2025.md",
            "author": "Legal & Operations",
            "authority_score": 0.98,
            "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        },
        {
            "record_id": "ticket_sla_claim_1102",
            "source_id": "support_tickets",
            "title": "Ticket #1102 - Outage credit inquiry Jan 2025",
            "content": "Customer asked why their Jan outage credit was 15% instead of 10%. Explained that under the new 2025 SLA policy, credit was upgraded to 15% automatic.",
            "uri": "/tickets/1102",
            "author": "Support Agent Mike",
            "authority_score": 0.80,
            "created_at": datetime(2025, 1, 20, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 20, tzinfo=timezone.utc),
        },

        # Scenario 3: Contradictory Data / Conflict Demo (Feature deprecation)
        {
            "record_id": "doc_feature_export_csv",
            "source_id": "kb_official_docs",
            "title": "Data Export Capabilities Guide",
            "content": "CSV export is fully supported across all query history tables directly from the analytics screen.",
            "uri": "/docs/features/export.md",
            "author": "Product Docs",
            "authority_score": 0.85,
            "created_at": datetime(2024, 8, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 8, 1, tzinfo=timezone.utc),
        },
        {
            "record_id": "slack_thread_export_deprecation",
            "source_id": "slack_conversations",
            "title": "#product-announcements: CSV export removal",
            "content": "Warning: CSV export was deprecated and removed in release v2.4 due to security compliance. Only JSON and Parquet exports are supported now.",
            "uri": "slack://product/p1712000000",
            "author": "VP Engineering",
            "authority_score": 0.70,
            "created_at": datetime(2025, 3, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 3, 1, tzinfo=timezone.utc),
        },
    ]

    for r_info in records_data:
        existing = db.query(RecordModel).filter(RecordModel.record_id == r_info["record_id"]).first()
        if not existing:
            rec = RecordModel(
                record_id=r_info["record_id"],
                source_id=r_info["source_id"],
                title=r_info["title"],
                content=r_info["content"],
                uri=r_info["uri"],
                author=r_info["author"],
                authority_score=r_info["authority_score"],
                created_at=r_info["created_at"],
                updated_at=r_info["updated_at"],
            )
            db.add(rec)

    db.commit()
