import re
from typing import List
from pydantic import BaseModel, Field
from backend.app.schemas.evidence import SourceType

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "can", "could", "should", "would", "what", "which",
    "who", "when", "where", "why", "how", "i", "you", "we", "they", "it", "my",
    "our", "your", "their", "this", "that", "these", "those", "about"
}


class QueryProfile(BaseModel):
    """
    Extracted semantic structure of the user question.
    """
    original_question: str
    clean_keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    topic: str = "general"
    intent: str = "general_inquiry"
    expected_source_types: List[SourceType] = Field(default_factory=list)
    requires_recent_info: bool = False
    requires_cross_verification: bool = False


class QueryUnderstandingService:
    """
    Analyzes user queries without relying on expensive external APIs.
    Identifies keywords, intent, candidate source categories, and verification needs.
    """

    @classmethod
    def analyze(cls, question: str) -> QueryProfile:
        q_lower = question.lower().strip()

        # Extract words & filter stopwords
        words = re.findall(r"[a-zA-Z0-9_\-\.]+", q_lower)
        keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]

        # Entity extraction heuristics (capitalized phrases or version numbers/codes)
        entities = []
        raw_words = re.findall(r"[A-Z][a-zA-Z0-9_\-\.]+|\b\d+(?:\.\d+)?%?|\bv\d+(?:\.\d+)?\b", question)
        for e in raw_words:
            if e.lower() not in STOP_WORDS:
                entities.append(e)

        # Detect temporal sensitivity
        temporal_cues = ["new", "recent", "updated", "latest", "2025", "current", "deprecated", "removed", "change"]
        requires_recent = any(cue in q_lower for cue in temporal_cues)

        # Detect cross-verification / dispute intent
        cross_cues = ["conflict", "contradict", "difference", "compare", "verify", "true or false", "claim", "exception"]
        requires_cross_check = any(cue in q_lower for cue in cross_cues)

        # Detect topic & intent
        topic = "general"
        intent = "general_inquiry"
        expected_types = [SourceType.DOCUMENT]

        if any(w in q_lower for w in ["refund", "billing", "credit", "price", "payment", "invoice", "cost"]):
            topic = "billing_policy"
            intent = "policy_lookup"
            expected_types = [SourceType.DOCUMENT, SourceType.TICKET]
        elif any(w in q_lower for w in ["sla", "uptime", "outage", "downtime", "incident"]):
            topic = "sla_service"
            intent = "policy_lookup"
            expected_types = [SourceType.DOCUMENT, SourceType.TICKET, SourceType.CONVERSATION]
        elif any(w in q_lower for w in ["error", "bug", "broken", "fail", "issue", "crash", "ticket"]):
            topic = "troubleshooting"
            intent = "issue_resolution"
            expected_types = [SourceType.TICKET, SourceType.CONVERSATION]
        elif any(w in q_lower for w in ["export", "csv", "feature", "api", "support", "config", "kafka"]):
            topic = "product_capabilities"
            intent = "feature_check"
            expected_types = [SourceType.DOCUMENT, SourceType.CONVERSATION]

        return QueryProfile(
            original_question=question,
            clean_keywords=keywords,
            entities=list(dict.fromkeys(entities)),
            topic=topic,
            intent=intent,
            expected_source_types=expected_types,
            requires_recent_info=requires_recent,
            requires_cross_verification=requires_cross_check,
        )
