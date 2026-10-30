"""
EvidenRoute - Deterministic Query Analyzer
Extracts intent, keywords, entities, technical terms, domain categories,
and anticipated source types from raw user questions without requiring external APIs.

Note on Architecture:
This module uses a deterministic rule-based and linguistic pattern-matching approach.
It is completely local, fast, testable, and dependency-free.
It implements the QueryAnalyzerInterface so that a Google Gemini API analyzer
can replace or augment it in later phases without altering the pipeline or API contract.
"""

import re
from typing import List, Set, Tuple
from .models import (
    InformationCategory,
    IntentType,
    QueryAnalysisResult,
    SourceType,
)


# Standard English stopwords to filter out during keyword extraction
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "just", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "should", "shouldn't", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "were", "weren't", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "won't", "would",
    "wouldn't", "you", "your", "yours", "yourself", "yourselves", "tell", "start",
    "latest", "last", "show", "give", "please", "can", "find", "get", "look"
}

# Recognized technical dictionary
TECHNICAL_TERMS: Set[str] = {
    "api", "apis", "deployment", "deploy", "deployed", "failing", "fail", "failed",
    "failure", "timeout", "timeouts", "database", "databases", "db", "postgres",
    "postgresql", "mysql", "redis", "mongodb", "cluster", "kubernetes", "k8s",
    "docker", "container", "microservice", "microservices", "endpoint", "endpoints",
    "connection", "connections", "latency", "exception", "exceptions", "crash",
    "crashed", "bug", "bugs", "patch", "git", "ci/cd", "pipeline", "cache", "caching",
    "query", "queries", "index", "backend", "frontend", "server", "servers", "node",
    "nodes", "cpu", "memory", "schema", "migration", "migrations", "http", "https",
    "rest", "graphql", "grpc", "token", "auth", "authentication", "authorization",
    "gateway", "loadbalancer", "webhook", "webhooks", "kafka", "queue", "worker"
}

# Domain Entity Multi-word Phrases
KNOWN_ENTITY_PATTERNS = [
    r"\bpayment\s+api\b",
    r"\bauth\s+service\b",
    r"\bdatabase\s+connection\s+timeout\b",
    r"\bdatabase\s+connection\b",
    r"\bpostgres(?:ql)?\s+database\b",
    r"\bproduct\s+planning\s+meeting\b",
    r"\bemployee\s+leave\s+policy\b",
    r"\barchitecture\s+decision\s+record\b",
    r"\bapi\s+gateway\b",
    r"\bci/cd\s+pipeline\b",
    r"\bremote\s+work\s+policy\b",
    r"\bcode\s+of\s+conduct\b",
    r"\bquarterly\s+planning\b",
    r"\bengineering\s+all-hands\b",
]


class QueryAnalyzer:
    """
    Deterministic rule-based query analyzer.
    Extracts structured intent, keywords, entities, and source suitability.
    """

    def analyze(self, question: str) -> QueryAnalysisResult:
        """
        Analyze a query string and return structured validation metadata.
        """
        cleaned_question = question.strip() if question else ""
        if not cleaned_question or not re.search(r"\w+", cleaned_question):
            return self._build_empty_result()

        intent, confidence = self._detect_intent(cleaned_question)
        keywords = self._extract_keywords(cleaned_question)
        entities = self._extract_entities(cleaned_question)
        tech_terms = self._extract_technical_terms(cleaned_question)
        category = self._determine_category(intent, tech_terms, cleaned_question)
        expected_info = self._determine_expected_information(intent, category)
        likely_sources = self._determine_likely_sources(intent, category)

        return QueryAnalysisResult(
            intent=intent,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            technical_terms=tech_terms,
            information_category=category,
            expected_information=expected_info,
            likely_source_types=likely_sources,
            analyzer_type="deterministic_rule_based",
            limitations_note=(
                "Heuristic rule-based parsing. Recognizes domain triggers, entities, and keywords. "
                "Interface is designed to be plug-and-play compatible with Google Gemini API in Phase 2."
            ),
        )

    def _detect_intent(self, q: str) -> Tuple[str, float]:
        """Detect intent using regex pattern matches and linguistic cues."""
        q_lower = q.lower()

        # 1. Technical Troubleshooting
        troubleshoot_patterns = [
            r"why did .+ fail",
            r"start(?:ed)? failing",
            r"resolve .+ timeout",
            r"connection timeout",
            r"error\b",
            r"exception\b",
            r"crash(?:ed)?\b",
            r"how do i (?:resolve|fix|debug)",
            r"why is .+ down",
            r"500\s+error",
        ]
        for p in troubleshoot_patterns:
            if re.search(p, q_lower):
                return IntentType.TECHNICAL_TROUBLESHOOTING.value, 0.92

        # 2. Bug Investigation
        bug_patterns = [
            r"bug\b",
            r"reproduce\b",
            r"incident report",
            r"ticket\b",
            r"regression\b",
            r"defect\b",
            r"flaky\b",
        ]
        for p in bug_patterns:
            if re.search(p, q_lower):
                return IntentType.BUG_INVESTIGATION.value, 0.88

        # 3. Policy Lookup
        policy_patterns = [
            r"\bpolicy\b",
            r"\bleave policy\b",
            r"\bpto\b",
            r"\bvacation\b",
            r"\bholiday\b",
            r"\bcode of conduct\b",
            r"\brules for\b",
            r"\bguidelines on\b",
            r"\breimbursement\b",
            r"\bsick leave\b",
            r"\bhandbook\b",
        ]
        for p in policy_patterns:
            if re.search(p, q_lower):
                return IntentType.POLICY_LOOKUP.value, 0.95

        # 4. Decision Discovery
        decision_patterns = [
            r"what was decided",
            r"decision\b",
            r"decided during",
            r"why did we choose",
            r"adr\b",
            r"architecture decision",
            r"meeting outcome",
            r"agreed upon",
            r"consensus\b",
            r"rationale for choosing",
        ]
        for p in decision_patterns:
            if re.search(p, q_lower):
                return IntentType.DECISION_DISCOVERY.value, 0.90

        # 5. Project Status
        status_patterns = [
            r"project status",
            r"sprint progress",
            r"roadmap\b",
            r"milestone\b",
            r"deadline\b",
            r"release date",
            r"quarterly goal",
        ]
        for p in status_patterns:
            if re.search(p, q_lower):
                return IntentType.PROJECT_STATUS.value, 0.85

        # 6. Fallback General Information
        if len(q.split()) < 3 and not re.search(r"\w+", q):
            return IntentType.UNCLEAR_QUERY.value, 0.20

        return IntentType.GENERAL_INFORMATION_LOOKUP.value, 0.65

    def _extract_keywords(self, q: str) -> List[str]:
        """Extract important topical keywords by removing stopwords and punctuation."""
        # Normalize punctuation while retaining words and acronyms
        raw_tokens = re.findall(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*", q)
        seen = set()
        keywords = []

        for token in raw_tokens:
            token_clean = token.strip()
            token_lower = token_clean.lower()
            if len(token_clean) > 1 and token_lower not in STOPWORDS and token_lower not in seen:
                seen.add(token_lower)
                # Keep original casing if acronym or capitalized, else lowercase
                if token_clean.isupper() and len(token_clean) <= 5:
                    keywords.append(token_clean)
                elif token_clean[0].isupper() and not token_lower in TECHNICAL_TERMS:
                    keywords.append(token_clean)
                else:
                    keywords.append(token_clean.lower())

        return keywords

    def _extract_entities(self, q: str) -> List[str]:
        """Extract multi-word domain entities and named concepts."""
        entities: List[str] = []
        q_lower = q.lower()

        # Match known multi-word patterns
        for pattern in KNOWN_ENTITY_PATTERNS:
            match = re.search(pattern, q_lower)
            if match:
                matched_text = match.group(0)
                # Find corresponding original slice if possible
                start, end = match.span()
                original_slice = q[start:end]
                # Capitalize nicely if acronym is present
                formatted = re.sub(r"\bapi\b", "API", original_slice, flags=re.IGNORECASE)
                if formatted not in entities:
                    entities.append(formatted)

        # Fallback heuristic: check if any uppercase acronym pairs exist
        acronym_matches = re.findall(r"\b[A-Za-z]+\s+[A-Z]{2,}\b|\b[A-Z]{2,}\s+[A-Za-z]+\b", q)
        for am in acronym_matches:
            if am not in entities and am.lower() not in [e.lower() for e in entities]:
                entities.append(am)

        return entities

    def _extract_technical_terms(self, q: str) -> List[str]:
        """Identify technical terminology present in query."""
        tokens = re.findall(r"[A-Za-z0-9_]+", q.lower())
        found = []
        for t in tokens:
            if t in TECHNICAL_TERMS and t not in found:
                found.append(t.upper() if t in {"api", "db", "http", "grpc"} else t)
        return found

    def _determine_category(self, intent: str, tech_terms: List[str], q: str) -> str:
        """Classify information category."""
        q_lower = q.lower()
        if intent in {IntentType.TECHNICAL_TROUBLESHOOTING.value, IntentType.BUG_INVESTIGATION.value} or len(tech_terms) >= 2:
            return InformationCategory.TECHNICAL.value
        if intent == IntentType.POLICY_LOOKUP.value or any(w in q_lower for w in ["leave", "hr", "conduct", "handbook"]):
            return InformationCategory.GOVERNANCE.value
        if intent == IntentType.DECISION_DISCOVERY.value:
            if "product" in q_lower:
                return InformationCategory.PRODUCT.value
            return InformationCategory.ORGANIZATIONAL.value
        if intent == IntentType.PROJECT_STATUS.value:
            return InformationCategory.OPERATIONAL.value
        return InformationCategory.GENERAL.value

    def _determine_expected_information(self, intent: str, category: str) -> List[str]:
        """Determine anticipated information artifacts expected to answer this query."""
        if intent == IntentType.TECHNICAL_TROUBLESHOOTING.value:
            return ["error reports", "deployment records", "technical documentation"]
        elif intent == IntentType.BUG_INVESTIGATION.value:
            return ["bug reports", "reproduction steps", "incident tickets", "system logs"]
        elif intent == IntentType.POLICY_LOOKUP.value:
            return ["company policy handbook", "HR guidelines", "compliance documents"]
        elif intent == IntentType.DECISION_DISCOVERY.value:
            return ["meeting transcripts", "technical decision records", "architecture RFCs"]
        elif intent == IntentType.PROJECT_STATUS.value:
            return ["project roadmap", "sprint status reports", "team updates"]
        else:
            return ["general reference documents", "knowledge base articles"]

    def _determine_likely_sources(self, intent: str, category: str) -> List[str]:
        """Determine likely source categories matching this query."""
        if intent == IntentType.TECHNICAL_TROUBLESHOOTING.value:
            return [SourceType.DOCUMENTS.value, SourceType.TICKETS.value, SourceType.CONVERSATIONS.value]
        elif intent == IntentType.BUG_INVESTIGATION.value:
            return [SourceType.TICKETS.value, SourceType.DOCUMENTS.value, SourceType.CONVERSATIONS.value]
        elif intent == IntentType.POLICY_LOOKUP.value:
            return [SourceType.DOCUMENTS.value]
        elif intent == IntentType.DECISION_DISCOVERY.value:
            return [SourceType.CONVERSATIONS.value, SourceType.DOCUMENTS.value]
        elif intent == IntentType.PROJECT_STATUS.value:
            return [SourceType.CONVERSATIONS.value, SourceType.TICKETS.value, SourceType.DOCUMENTS.value]
        else:
            return [SourceType.DOCUMENTS.value]

    def _build_empty_result(self) -> QueryAnalysisResult:
        """Fallback for empty or whitespace query."""
        return QueryAnalysisResult(
            intent=IntentType.UNCLEAR_QUERY.value,
            confidence=0.0,
            keywords=[],
            entities=[],
            technical_terms=[],
            information_category=InformationCategory.GENERAL.value,
            expected_information=["unspecified query input"],
            likely_source_types=[],
            analyzer_type="deterministic_rule_based",
            limitations_note="Query was empty or contained only whitespace.",
        )
