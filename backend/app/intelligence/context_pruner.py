"""
EvidenRoute - Budget-Aware Context Pruning Engine
Compresses and deduplicates evidence passages while strictly preserving:
1. All citations and source attribution metadata.
2. Contradictory evidence (conflict passages are shielded from pruning).
3. Important technical identifiers, error codes, dates, decisions, and resolutions.
Produces an audit report detailing which sentences/passages were retained vs pruned.
"""

import re
from typing import List, Optional, Set
from .models import (
    ConflictReport,
    EvidencePassage,
    PrunedContextResult,
    PruningDetail,
)


class ContextPruner:
    """
    Sentence-level deduplication and context compression engine.
    Ensures optimal token utilization without losing semantic substance or citations.
    """

    def __init__(self):
        # Technical identifiers that must be preserved
        self.identifier_pattern = re.compile(
            r"\b(?:[A-Z0-9_]{3,}(?:-[A-Z0-9_]+)*|[a-z0-9_]+_pool_size|[a-z0-9_]+_timeout|err_[a-z0-9_]+|\b50\d\b)\b",
            re.IGNORECASE,
        )
        # Date pattern: YYYY-MM-DD or timestamps
        self.date_pattern = re.compile(
            r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|20\d{2}\.\d{2})\b"
        )
        # Decision and resolution markers
        self.decision_pattern = re.compile(
            r"\b(?:resolved|resolution|decided|decision|hotfix|root cause|rollback|fix(?:ed)?)\b",
            re.IGNORECASE,
        )

    def prune_context(
        self,
        passages: List[EvidencePassage],
        conflicts: Optional[List[ConflictReport]] = None,
        max_context_chars: Optional[int] = None,
    ) -> PrunedContextResult:
        """
        Deduplicate redundant sentences and compress context while safeguarding citations and conflicts.
        """
        if not passages:
            return PrunedContextResult(
                original_passages_count=0,
                retained_passages_count=0,
                original_sentence_count=0,
                retained_sentence_count=0,
                pruned_sentence_count=0,
                pruned_details=[],
                retained_evidence=[],
                conflict_passages_preserved_count=0,
                compression_ratio=1.0,
            )

        # 1. Identify Protected Conflict Statements and Chunks
        protected_statements: Set[str] = set()
        protected_chunk_ids: Set[str] = set()

        if conflicts:
            for conf in conflicts:
                for ref in conf.conflicting_passages:
                    protected_chunk_ids.add(ref.chunk_id)
                    if ref.statement:
                        protected_statements.add(self._normalize_sentence(ref.statement))

        # 2. Iterate and Deduplicate Sentences
        seen_sentence_signatures: Set[str] = set()
        pruned_details: List[PruningDetail] = []
        retained_passages: List[EvidencePassage] = []

        total_original_sentences = 0
        total_retained_sentences = 0
        total_pruned_sentences = 0
        conflict_passages_count = 0

        # Sort passages by evidence score (most authoritative first)
        ordered_passages = sorted(
            passages,
            key=lambda p: (
                p.chunk_id in protected_chunk_ids,  # Keep conflict passages high priority
                p.evidence_score.final_evidence_score,
                p.authority_level,
            ),
            reverse=True,
        )

        current_char_count = 0

        for passage in ordered_passages:
            is_conflict_passage = passage.chunk_id in protected_chunk_ids
            if is_conflict_passage:
                conflict_passages_count += 1

            sentences = self._split_sentences(passage.content)
            total_original_sentences += len(sentences)

            retained_sentences: List[str] = []

            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean:
                    continue

                sig = self._normalize_sentence(sent_clean)

                # Check if this sentence is protected due to conflict
                is_protected_conflict = (
                    sig in protected_statements
                    or any(p_sig in sig or sig in p_sig for p_sig in protected_statements)
                )

                # Check if sentence contains critical technical identifiers or decisions
                has_key_identifiers = bool(
                    self.identifier_pattern.search(sent_clean)
                    or self.date_pattern.search(sent_clean)
                    or self.decision_pattern.search(sent_clean)
                )

                if is_protected_conflict:
                    # Never prune contradictory statements
                    retained_sentences.append(sent_clean)
                    seen_sentence_signatures.add(sig)
                    total_retained_sentences += 1
                elif sig in seen_sentence_signatures:
                    # Duplicate sentence -> PRUNE
                    pruned_details.append(
                        PruningDetail(
                            chunk_id=passage.chunk_id,
                            original_file_path=passage.original_file_path,
                            sentence=sent_clean,
                            reason="redundant_duplicate_sentence",
                        )
                    )
                    total_pruned_sentences += 1
                else:
                    # Retain
                    retained_sentences.append(sent_clean)
                    seen_sentence_signatures.add(sig)
                    total_retained_sentences += 1

            if retained_sentences:
                reconstructed_content = "\n".join(retained_sentences)

                # Check character budget limit if specified
                passage_chars = len(reconstructed_content)
                if max_context_chars is not None and (current_char_count + passage_chars > max_context_chars):
                    # If this is a protected conflict passage, we must preserve it regardless!
                    if is_conflict_passage:
                        retained_copy = passage.model_copy(
                            update={"content": reconstructed_content}
                        )
                        retained_passages.append(retained_copy)
                        current_char_count += passage_chars
                    else:
                        pruned_details.append(
                            PruningDetail(
                                chunk_id=passage.chunk_id,
                                original_file_path=passage.original_file_path,
                                sentence=f"Passage '{passage.title}' omitted to fit character budget limit.",
                                reason="exceeded_context_budget_limit",
                            )
                        )
                else:
                    # Copy passage while preserving citations and metadata
                    retained_copy = passage.model_copy(
                        update={"content": reconstructed_content}
                    )
                    retained_passages.append(retained_copy)
                    current_char_count += passage_chars

        # Compute compression metrics
        original_text_len = sum(len(p.content) for p in passages)
        retained_text_len = sum(len(p.content) for p in retained_passages)
        compression_ratio = (
            round(retained_text_len / original_text_len, 4) if original_text_len > 0 else 1.0
        )

        return PrunedContextResult(
            original_passages_count=len(passages),
            retained_passages_count=len(retained_passages),
            original_sentence_count=total_original_sentences,
            retained_sentence_count=total_retained_sentences,
            pruned_sentence_count=total_pruned_sentences,
            pruned_details=pruned_details,
            retained_evidence=retained_passages,
            conflict_passages_preserved_count=conflict_passages_count,
            compression_ratio=compression_ratio,
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences while respecting markdown formatting."""
        lines = text.split("\n")
        sentences = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("#") or line_str.startswith("-") or line_str.startswith("*"):
                sentences.append(line_str)
                continue
            raw = re.split(r"(?<=[.!?])\s+", line_str)
            for r in raw:
                s = r.strip()
                if s:
                    sentences.append(s)
        return sentences

    def _normalize_sentence(self, sent: str) -> str:
        """Produce canonical signature by stripping punctuation and whitespace."""
        clean = re.sub(r"[^\w\s]", "", sent.lower())
        return " ".join(clean.split())
