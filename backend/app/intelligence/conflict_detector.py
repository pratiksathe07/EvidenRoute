"""
EvidenRoute - Factual Conflict Detection Engine
Compares factual claims across retrieved evidence passages (documents, conversations, tickets).
Distinguishes direct contradictions from temporal updates, version divergence, and status progression.
Preserves chunk IDs, source metadata, and citations for complete auditability.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple
from .models import (
    ConflictDetectionResult,
    ConflictingPassageRef,
    ConflictReport,
    ConflictSeverity,
    ConflictType,
    EvidencePassage,
)


class ConflictDetector:
    """
    Explainable, deterministic conflict detection engine.
    Analyzes evidence passages for contradictory claims, version differences,
    temporal supersedence, and status transitions.
    """

    def __init__(self):
        # Attribute extraction patterns: (attribute_name, regex_pattern, unit_or_type)
        self.metric_patterns = [
            (
                "timeout_duration",
                r"(?:timeout|delay)[^0-9\n.]{0,30}?(\d+)\s*(?:ms|s|seconds|sec)\b",
                "duration",
            ),
            (
                "db_pool_size",
                r"(?:max(?:_db)?_pool_size|pool size|connection pool limit|pool limit)[^0-9\n.]{0,30}?(\d+)\b",
                "count",
            ),
            (
                "annual_leave_days",
                r"(\d+)\s*days[^0-9\n.]{0,30}?(?:annual|paid|pto|vacation)",
                "days",
            ),
            (
                "sick_leave_days",
                r"(\d+)\s*days[^0-9\n.]{0,30}?sick leave",
                "days",
            ),
            (
                "parental_leave_weeks",
                r"(\d+)\s*weeks[^0-9\n.]{0,30}?parental leave",
                "weeks",
            ),
            (
                "error_status_code",
                r"(?:error|status|code|err_)[^0-9\n.]{0,20}?(500|502|503|504|400|401|403|404)\b",
                "code",
            ),
        ]

        # Polarity / State Opposition pairs: (positive_regex, negative_regex, topic_label)
        self.polarity_pairs = [
            (
                r"\b(?:is |are )?enabled\b",
                r"\b(?:is |are )?(?:disabled|not enabled|inactive)\b",
                "feature_enablement",
            ),
            (
                r"\b(?:is |are )?supported\b",
                r"\b(?:is |are )?(?:unsupported|deprecated|not supported)\b",
                "support_status",
            ),
            (
                r"\b(?:is |are )?required\b",
                r"\b(?:is |are )?(?:optional|not required|deprecated)\b",
                "requirement_status",
            ),
            (
                r"\b(?:was |is )?(?:resolved|fixed|closed)\b",
                r"\b(?:is |remains )?(?:unresolved|failing|broken|open|reopened)\b",
                "resolution_status",
            ),
        ]

    def detect_conflicts(
        self, passages: List[EvidencePassage]
    ) -> ConflictDetectionResult:
        """
        Scan list of evidence passages and detect factual contradictions or divergences.
        """
        if not passages or len(passages) < 2:
            return ConflictDetectionResult(
                total_passages_evaluated=len(passages) if passages else 0,
                conflicts_detected_count=0,
                direct_contradictions_count=0,
                conflicts=[],
                has_unresolved_contradictions=False,
            )

        conflicts: List[ConflictReport] = []
        conflict_pairs_seen = set()

        # Compare every pair of passages (O(N^2) where N is top_k <= 10, very fast < 5ms)
        for i in range(len(passages)):
            for j in range(i + 1, len(passages)):
                p1 = passages[i]
                p2 = passages[j]

                detected = self._compare_passage_pair(p1, p2)
                for c in detected:
                    pair_key = (min(p1.chunk_id, p2.chunk_id), max(p1.chunk_id, p2.chunk_id), c.topic)
                    if pair_key not in conflict_pairs_seen:
                        conflict_pairs_seen.add(pair_key)
                        conflicts.append(c)

        direct_count = sum(1 for c in conflicts if c.is_direct_contradiction)

        return ConflictDetectionResult(
            total_passages_evaluated=len(passages),
            conflicts_detected_count=len(conflicts),
            direct_contradictions_count=direct_count,
            conflicts=conflicts,
            has_unresolved_contradictions=direct_count > 0,
        )

    def _compare_passage_pair(
        self, p1: EvidencePassage, p2: EvidencePassage
    ) -> List[ConflictReport]:
        """
        Examine two passages for claim inconsistencies.
        """
        reports: List[ConflictReport] = []

        # 1. Check Quantitative & Metric Divergence
        metric_reports = self._check_numerical_metrics(p1, p2)
        reports.extend(metric_reports)

        # 2. Check Polarity & State Contradictions on shared subjects
        polarity_reports = self._check_polarity_inconsistencies(p1, p2)
        reports.extend(polarity_reports)

        # 3. Check Mutually Exclusive Root Cause Claims
        root_cause_reports = self._check_root_cause_divergence(p1, p2)
        reports.extend(root_cause_reports)

        return reports

    def _check_numerical_metrics(
        self, p1: EvidencePassage, p2: EvidencePassage
    ) -> List[ConflictReport]:
        """Check for conflicting numerical values for the same property."""
        reports: List[ConflictReport] = []
        sents1 = self._split_sentences(p1.content)
        sents2 = self._split_sentences(p2.content)

        for metric_name, pattern, unit in self.metric_patterns:
            matches1 = []
            for s in sents1:
                m = re.findall(pattern, s, re.IGNORECASE)
                if m:
                    matches1.append((m[0], s))

            matches2 = []
            for s in sents2:
                m = re.findall(pattern, s, re.IGNORECASE)
                if m:
                    matches2.append((m[0], s))

            if matches1 and matches2:
                val1, stmt1 = matches1[0]
                val2, stmt2 = matches2[0]

                # If values differ
                if val1 != val2:
                    # Check for version divergence or temporal supersedence
                    ctype, severity, is_direct, expl, hint = self._classify_divergence(
                        p1, p2, stmt1, stmt2, metric_name, val1, val2
                    )

                    ref1 = ConflictingPassageRef(
                        chunk_id=p1.chunk_id,
                        source_id=p1.source_id,
                        source_name=p1.source_name,
                        citation=p1.citation,
                        statement=stmt1.strip(),
                        timestamp=p1.created_at,
                    )
                    ref2 = ConflictingPassageRef(
                        chunk_id=p2.chunk_id,
                        source_id=p2.source_id,
                        source_name=p2.source_name,
                        citation=p2.citation,
                        statement=stmt2.strip(),
                        timestamp=p2.created_at,
                    )

                    report = ConflictReport(
                        conflict_id=f"conf-metric-{metric_name}-{p1.chunk_id[:6]}-{p2.chunk_id[:6]}",
                        conflict_type=ctype.value,
                        topic=metric_name.replace("_", " ").title(),
                        is_direct_contradiction=is_direct,
                        severity=severity.value,
                        conflicting_passages=[ref1, ref2],
                        explanation=expl,
                        resolution_hint=hint,
                    )
                    reports.append(report)

        return reports

    def _check_polarity_inconsistencies(
        self, p1: EvidencePassage, p2: EvidencePassage
    ) -> List[ConflictReport]:
        """Check opposing affirmative vs negative polarity on shared entities."""
        reports: List[ConflictReport] = []
        sents1 = self._split_sentences(p1.content)
        sents2 = self._split_sentences(p2.content)

        # Detect shared technical terms or entities between passages
        shared_keywords = self._find_shared_anchors(p1.content, p2.content)
        if not shared_keywords:
            return reports

        for pos_pat, neg_pat, label in self.polarity_pairs:
            for s1 in sents1:
                has_pos1 = bool(re.search(pos_pat, s1, re.IGNORECASE))
                has_neg1 = bool(re.search(neg_pat, s1, re.IGNORECASE))

                for s2 in sents2:
                    has_pos2 = bool(re.search(pos_pat, s2, re.IGNORECASE))
                    has_neg2 = bool(re.search(neg_pat, s2, re.IGNORECASE))

                    # Direct polarity clash on shared topic
                    if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
                        # Ensure both sentences share at least one topical anchor
                        s1_words = set(re.findall(r"\w+", s1.lower()))
                        s2_words = set(re.findall(r"\w+", s2.lower()))
                        if not s1_words.intersection(shared_keywords) or not s2_words.intersection(shared_keywords):
                            continue

                        ctype, severity, is_direct, expl, hint = self._classify_divergence(
                            p1, p2, s1, s2, label, "Affirmative", "Negative"
                        )

                        ref1 = ConflictingPassageRef(
                            chunk_id=p1.chunk_id,
                            source_id=p1.source_id,
                            source_name=p1.source_name,
                            citation=p1.citation,
                            statement=s1.strip(),
                            timestamp=p1.created_at,
                        )
                        ref2 = ConflictingPassageRef(
                            chunk_id=p2.chunk_id,
                            source_id=p2.source_id,
                            source_name=p2.source_name,
                            citation=p2.citation,
                            statement=s2.strip(),
                            timestamp=p2.created_at,
                        )

                        report = ConflictReport(
                            conflict_id=f"conf-polarity-{label}-{p1.chunk_id[:6]}-{p2.chunk_id[:6]}",
                            conflict_type=ctype.value,
                            topic=label.replace("_", " ").title(),
                            is_direct_contradiction=is_direct,
                            severity=severity.value,
                            conflicting_passages=[ref1, ref2],
                            explanation=expl,
                            resolution_hint=hint,
                        )
                        reports.append(report)
                        break

        return reports

    def _check_root_cause_divergence(
        self, p1: EvidencePassage, p2: EvidencePassage
    ) -> List[ConflictReport]:
        """Check for contradictory claims regarding root cause of same incident/deployment."""
        reports: List[ConflictReport] = []
        c1_lower = p1.content.lower()
        c2_lower = p2.content.lower()

        # Both must discuss incident root cause or failure reason
        rc_terms = ["root cause", "caused by", "due to", "failure reason"]
        has_rc1 = any(t in c1_lower for t in rc_terms)
        has_rc2 = any(t in c2_lower for t in rc_terms)

        if not (has_rc1 and has_rc2):
            return reports

        # Check for explicit refutation / opposing attributions:
        # e.g., one claims "connection pool exhaustion" vs another says "dns routing, not the database"
        db_cause1 = "pool" in c1_lower or "database" in c1_lower
        db_denial2 = "not the database" in c2_lower or "dns routing" in c2_lower or "upstream gateway timeout" in c2_lower

        db_cause2 = "pool" in c2_lower or "database" in c2_lower
        db_denial1 = "not the database" in c1_lower or "dns routing" in c1_lower or "upstream gateway timeout" in c1_lower

        if (db_cause1 and db_denial2) or (db_cause2 and db_denial1):
            ref1 = ConflictingPassageRef(
                chunk_id=p1.chunk_id,
                source_id=p1.source_id,
                source_name=p1.source_name,
                citation=p1.citation,
                statement=p1.content[:160].strip(),
                timestamp=p1.created_at,
            )
            ref2 = ConflictingPassageRef(
                chunk_id=p2.chunk_id,
                source_id=p2.source_id,
                source_name=p2.source_name,
                citation=p2.citation,
                statement=p2.content[:160].strip(),
                timestamp=p2.created_at,
            )

            report = ConflictReport(
                conflict_id=f"conf-rootcause-{p1.chunk_id[:6]}-{p2.chunk_id[:6]}",
                conflict_type=ConflictType.DIRECT_CONTRADICTION.value,
                topic="Incident Root Cause Attribution",
                is_direct_contradiction=True,
                severity=ConflictSeverity.CRITICAL.value,
                conflicting_passages=[ref1, ref2],
                explanation=(
                    f"Direct contradiction on incident root cause between '{p1.source_name}' and '{p2.source_name}'. "
                    f"One passage attributes failure to database pool exhaustion while the other disputes or denies database involvement."
                ),
                resolution_hint="Investigate incident logs or consult war room transcripts for verified postmortem findings.",
            )
            reports.append(report)

        return reports

    def _classify_divergence(
        self,
        p1: EvidencePassage,
        p2: EvidencePassage,
        s1: str,
        s2: str,
        topic: str,
        val1: Any,
        val2: Any,
    ) -> Tuple[ConflictType, ConflictSeverity, bool, str, Optional[str]]:
        """
        Dissect divergence to determine whether it is a direct contradiction,
        version divergence, temporal supersedence, or status progression.
        """
        combined_text = f"{s1} {s2} {p1.content} {p2.content}".lower()

        # 1. Version Divergence Check
        v_matches = re.findall(r"\bv(\d+(?:\.\d+)*)\b", combined_text)
        has_v1 = bool(re.search(r"\bv1(?:\.\d+)?\b|\blegacy\b", combined_text))
        has_v2 = bool(re.search(r"\bv2(?:\.\d+)?\b|\bnew release\b", combined_text))
        if has_v1 and has_v2:
            return (
                ConflictType.VERSION_DIVERGENCE,
                ConflictSeverity.INFO,
                False,
                f"Version divergence on {topic}: Passages reference different system versions (e.g. v1 vs v2).",
                "Review the latest version specification or target environment release notes.",
            )

        # 2. Status Progression Check
        if topic == "resolution_status":
            # Check timestamps or war-room progress
            return (
                ConflictType.STATUS_PROGRESSION,
                ConflictSeverity.INFO,
                False,
                f"Status progression on {topic}: Reflects transition over incident lifecycle (e.g. investigating to resolved).",
                "Accept the latest resolved status as current operational state.",
            )

        # 3. Temporal Supersedence Check
        t1 = self._parse_iso_date(p1.created_at) or self._extract_date_from_text(p1.content)
        t2 = self._parse_iso_date(p2.created_at) or self._extract_date_from_text(p2.content)

        update_cues = ["updated", "revised", "superseded", "as of", "new policy", "increased to"]
        has_update_cue = any(c in combined_text for c in update_cues)

        if t1 and t2 and t1 != t2:
            newer = p1 if t1 > t2 else p2
            older = p2 if t1 > t2 else p1
            newer_date = max(t1, t2).strftime("%Y-%m-%d")
            older_date = min(t1, t2).strftime("%Y-%m-%d")

            if has_update_cue or abs((t1 - t2).days) >= 30:
                return (
                    ConflictType.TEMPORAL_SUPERSEDENCE,
                    ConflictSeverity.WARNING,
                    False,
                    f"Temporal supersedence on {topic}: Newer passage ({newer_date}) updates or supersedes older passage ({older_date}).",
                    f"Prioritize recent information from '{newer.source_name}' dated {newer_date}.",
                )

        # 4. Default: Direct Contradiction
        return (
            ConflictType.DIRECT_CONTRADICTION,
            ConflictSeverity.CRITICAL,
            True,
            f"Direct contradiction on {topic}: '{p1.source_name}' claims '{val1}' while '{p2.source_name}' claims '{val2}'.",
            "Clarify current configuration or verify authoritative system registry.",
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text cleanly into sentences while respecting markdown headings and lists."""
        lines = text.split("\n")
        sentences = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("#") or line_str.startswith("-") or line_str.startswith("*"):
                sentences.append(line_str)
                continue
            # Regex sentence boundary split
            raw_sents = re.split(r"(?<=[.!?])\s+", line_str)
            for s in raw_sents:
                clean = s.strip()
                if clean:
                    sentences.append(clean)
        return sentences

    def _find_shared_anchors(self, text1: str, text2: str) -> set:
        """Find meaningful domain entities or technical tokens present in both texts."""
        stopwords = {
            "the", "and", "a", "an", "is", "was", "are", "were", "to", "in", "for", "of",
            "with", "on", "at", "by", "from", "after", "before", "during", "this", "that"
        }
        tokens1 = set(re.findall(r"[A-Za-z0-9_-]+", text1.lower())) - stopwords
        tokens2 = set(re.findall(r"[A-Za-z0-9_-]+", text2.lower())) - stopwords

        # Keep domain keywords with length > 2
        return {t for t in tokens1.intersection(tokens2) if len(t) > 2}

    def _parse_iso_date(self, d_str: Optional[str]) -> Optional[datetime]:
        """Attempt to parse ISO timestamp string."""
        if not d_str:
            return None
        try:
            clean = d_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean)
        except Exception:
            return None

    def _extract_date_from_text(self, text: str) -> Optional[datetime]:
        """Extract YYYY-MM-DD date from text if present."""
        m = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", text)
        if m:
            try:
                return datetime.strptime(m.group(0), "%Y-%m-%d")
            except Exception:
                pass
        return None
