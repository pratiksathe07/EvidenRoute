import re
import uuid
from typing import List, Optional
from backend.app.schemas.evidence import NormalizedEvidence
from backend.app.schemas.query import ContradictionItem, ContradictionType


class ContradictionDetectorService:
    """
    Detects semantic, numerical, and status conflicts between evidence items.
    Distinguishes temporal policy updates from genuine factual disputes.
    """

    @classmethod
    def detect_contradictions(
        cls,
        evidence_items: List[NormalizedEvidence]
    ) -> List[ContradictionItem]:
        contradictions: List[ContradictionItem] = []
        n = len(evidence_items)
        if n < 2:
            return contradictions

        # Pairwise cross-inspection
        for i in range(n):
            for j in range(i + 1, n):
                ev_a = evidence_items[i]
                ev_b = evidence_items[j]

                conflict = cls._compare_pair(ev_a, ev_b)
                if conflict:
                    contradictions.append(conflict)

        return contradictions

    @classmethod
    def _compare_pair(
        cls,
        ev_a: NormalizedEvidence,
        ev_b: NormalizedEvidence
    ) -> Optional[ContradictionItem]:
        text_a = f"{ev_a.title} {ev_a.content}".lower()
        text_b = f"{ev_b.title} {ev_b.content}".lower()

        # Check shared subject domains
        shared_subjects = []
        for term in ["sla", "uptime", "refund", "credit", "export", "csv", "kafka"]:
            if term in text_a and term in text_b:
                shared_subjects.append(term)

        if not shared_subjects:
            return None

        # 1. Feature deprecation / status disagreement (e.g. CSV export supported vs deprecated/removed)
        has_positive = any(w in text_a for w in ["supported", "guarantees", "available"]) or any(w in text_b for w in ["supported", "guarantees", "available"])
        has_negative = any(w in text_a for w in ["deprecated", "removed", "no longer", "discontinued"]) or any(w in text_b for w in ["deprecated", "removed", "no longer", "discontinued"])

        if has_positive and has_negative:
            # Check temporal ordering
            date_a = ev_a.updated_at or ev_a.created_at
            date_b = ev_b.updated_at or ev_b.created_at

            if date_a and date_b and date_a != date_b:
                newer_ev = ev_a if date_a > date_b else ev_b
                older_ev = ev_b if date_a > date_b else ev_a
                return ContradictionItem(
                    conflict_id=f"conf_{uuid.uuid4().hex[:8]}",
                    evidence_a_id=ev_a.evidence_id,
                    evidence_b_id=ev_b.evidence_id,
                    contradiction_type=ContradictionType.TEMPORAL_UPDATE,
                    description=f"Status update detected on subject '{shared_subjects[0]}'. Older record indicated feature availability while newer record indicates removal/deprecation.",
                    severity="high",
                    resolution_status="resolved_by_recency",
                    resolution_reasoning=f"Newer record '{newer_ev.evidence_id}' supersedes older record '{older_ev.evidence_id}'.",
                )
            else:
                return ContradictionItem(
                    conflict_id=f"conf_{uuid.uuid4().hex[:8]}",
                    evidence_a_id=ev_a.evidence_id,
                    evidence_b_id=ev_b.evidence_id,
                    contradiction_type=ContradictionType.STATUS_DISAGREEMENT,
                    description=f"Disagreement on status of '{shared_subjects[0]}': one source claims supported while another indicates deprecated.",
                    severity="critical",
                    resolution_status="unresolved",
                    resolution_reasoning="Sources present conflicting operational status without unambiguous date supersession.",
                )

        # 2. Numerical / Value disagreement (e.g. 10% credit vs 15% credit, or 99.9% vs 99.95%)
        nums_a = set(re.findall(r"\b\d+(?:\.\d+)?%?", text_a))
        nums_b = set(re.findall(r"\b\d+(?:\.\d+)?%?", text_b))

        # Check if they have divergent numbers in the same context
        differing_metrics = (nums_a ^ nums_b) - {"0", "1", "2"}
        if differing_metrics and len(nums_a) > 0 and len(nums_b) > 0:
            # Check if one is a newer policy revision
            date_a = ev_a.updated_at or ev_a.created_at
            date_b = ev_b.updated_at or ev_b.created_at

            if date_a and date_b and abs((date_a - date_b).days) > 60:
                newer = ev_a if date_a > date_b else ev_b
                older = ev_b if date_a > date_b else ev_a
                return ContradictionItem(
                    conflict_id=f"conf_{uuid.uuid4().hex[:8]}",
                    evidence_a_id=ev_a.evidence_id,
                    evidence_b_id=ev_b.evidence_id,
                    contradiction_type=ContradictionType.TEMPORAL_UPDATE,
                    description=f"Numerical parameter updated over time for '{shared_subjects[0]}': {nums_a} vs {nums_b}.",
                    severity="medium",
                    resolution_status="resolved_by_recency",
                    resolution_reasoning=f"Revision '{newer.evidence_id}' ({newer.updated_at.year if newer.updated_at else ''}) updates previous specification in '{older.evidence_id}'.",
                )
            elif "exception" in text_a or "exception" in text_b or "enterprise" in text_a or "enterprise" in text_b:
                return ContradictionItem(
                    conflict_id=f"conf_{uuid.uuid4().hex[:8]}",
                    evidence_a_id=ev_a.evidence_id,
                    evidence_b_id=ev_b.evidence_id,
                    contradiction_type=ContradictionType.PARTIAL_OVERLAP,
                    description=f"Scope difference on '{shared_subjects[0]}': standard customer policy differs from enterprise exception.",
                    severity="low",
                    resolution_status="resolved_by_authority",
                    resolution_reasoning="Discrepancy is attributable to distinct customer tiers (standard vs enterprise).",
                )

        return None
