import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.adapters.base import BaseSourceAdapter
from backend.app.database.models import RecordModel, SourceModel
from backend.app.schemas.evidence import NormalizedEvidence, SourceType
from backend.app.schemas.source import SourceInfo


class SQLiteSourceAdapter(BaseSourceAdapter):
    """
    Adapter for querying records ingested into local SQLite storage.
    Supports keyword matching across title and content with authority weighting.
    """

    def __init__(self, source_id: str, db_session_factory):
        self.source_id = source_id
        self.db_session_factory = db_session_factory

    def describe(self) -> SourceInfo:
        with self.db_session_factory() as session:
            src = session.query(SourceModel).filter(SourceModel.source_id == self.source_id).first()
            if not src:
                return SourceInfo(
                    source_id=self.source_id,
                    name=f"Unknown Source ({self.source_id})",
                    source_type=SourceType.DOCUMENT,
                    description="Source not yet registered in database.",
                    default_authority=0.5,
                    enabled=False,
                    record_count=0,
                    status="offline",
                )

            count = session.query(RecordModel).filter(RecordModel.source_id == self.source_id).count()
            metadata = {}
            if src.metadata_json:
                try:
                    metadata = json.loads(src.metadata_json)
                except Exception:
                    pass

            return SourceInfo(
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

    def health_check(self) -> bool:
        try:
            with self.db_session_factory() as session:
                src = session.query(SourceModel).filter(SourceModel.source_id == self.source_id).first()
                return src is not None and src.enabled
        except Exception:
            return False

    def search(self, query: str, limit: int = 5) -> List[NormalizedEvidence]:
        """
        Tokenizes search query and retrieves matching records ordered by frequency and authority.
        """
        tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]
        if not tokens:
            tokens = [query.strip().lower()]

        with self.db_session_factory() as session:
            # Match records containing any of the query terms
            filters = [
                or_(
                    RecordModel.title.ilike(f"%{token}%"),
                    RecordModel.content.ilike(f"%{token}%")
                )
                for token in tokens
            ]

            query_builder = session.query(RecordModel).filter(
                RecordModel.source_id == self.source_id,
                or_(*filters) if filters else True
            )

            records = query_builder.limit(limit * 2).all()

            # Rank by keyword hit count + authority score
            scored_records = []
            for r in records:
                text_lower = (r.title + " " + r.content).lower()
                hits = sum(text_lower.count(token) for token in tokens)
                score = (hits * 1.5) + (r.authority_score * 2.0)
                scored_records.append((score, r))

            scored_records.sort(key=lambda x: x[0], reverse=True)
            top_records = [r for _, r in scored_records[:limit]]

            evidence_items = []
            for r in top_records:
                metadata = {}
                if r.metadata_json:
                    try:
                        metadata = json.loads(r.metadata_json)
                    except Exception:
                        pass

                evidence_items.append(
                    NormalizedEvidence(
                        evidence_id=r.record_id,
                        source_id=r.source_id,
                        source_type=SourceType.DOCUMENT,
                        title=r.title,
                        content=r.content,
                        uri=r.uri,
                        created_at=r.created_at,
                        updated_at=r.updated_at,
                        author=r.author,
                        authority_score=r.authority_score,
                        metadata=metadata,
                    )
                )

            return evidence_items
