"""
EvidenRoute - BM25 Keyword Retriever
Executes lexical passage retrieval strictly within sources pre-selected by Phase 1.
"""

import math
import re
from typing import Dict, List, Optional, Set, Tuple
from .models import ChunkData
from .storage import BaseChunkStore, ChunkStore


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize and normalize text into lowercase alphanumeric terms and identifiers.
    Preserves compound tokens like 'eng-4029' and 'v2.4' alongside split terms.
    """
    if not text:
        return []
    raw_tokens = re.findall(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*", text.lower())
    all_tokens: List[str] = []
    for t in raw_tokens:
        all_tokens.append(t)
        if "-" in t:
            all_tokens.extend(part for part in t.split("-") if part)
    return all_tokens


class BM25OkapiEngine:
    """
    Lucene-aligned BM25Okapi implementation.
    Uses log(1 + (N - n + 0.5)/(n + 0.5)) to guarantee positive IDF even on small corpora.
    """

    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.doc_lens = [len(d) for d in corpus_tokens]
        self.avg_doc_len = sum(self.doc_lens) / max(1, self.corpus_size)

        # Compute document frequencies
        self.df: Dict[str, int] = {}
        for doc in corpus_tokens:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

        # Lucene/Robertson BM25 positive IDF formula
        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

        self.corpus_tokens = corpus_tokens

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        if not query_tokens:
            return scores

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for doc_idx, doc in enumerate(self.corpus_tokens):
                tf = doc.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                scores[doc_idx] += idf_val * (numerator / denominator)

        # Exact identifier bonus (e.g. ENG-4029, INC-88912)
        for doc_idx, doc in enumerate(self.corpus_tokens):
            for q_term in query_tokens:
                if "-" in q_term and q_term in doc:
                    scores[doc_idx] += 2.0

        return scores


class BM25Retriever:
    """
    Ranks passages within selected knowledge sources using BM25.
    Guarantees skipped sources are excluded from retrieval.
    """

    def __init__(self, chunk_store: Optional[BaseChunkStore] = None):
        self.chunk_store = chunk_store or ChunkStore

    def retrieve(
        self,
        query: str,
        selected_source_ids: List[str],
        top_k: int = 10,
    ) -> List[Tuple[ChunkData, float, float]]:
        """
        Search and rank passages.
        Returns List of tuples: (ChunkData, raw_bm25_score, normalized_bm25_score [0, 1]).
        """
        clean_query = query.strip() if query else ""
        if not clean_query or not selected_source_ids:
            return []

        # 1. Fetch chunks ONLY from selected sources
        candidate_chunks = self.chunk_store.get_chunks_by_source_ids(selected_source_ids)
        if not candidate_chunks:
            return []

        # 2. Tokenize corpus & query
        query_tokens = tokenize_text(clean_query)
        if not query_tokens:
            return []

        corpus_tokens = [tokenize_text(f"{c.title} {c.content}") for c in candidate_chunks]

        # 3. Calculate BM25 scores
        engine = BM25OkapiEngine(corpus_tokens)
        raw_scores = engine.get_scores(query_tokens)

        # 4. Filter zero-score passages and pair with chunks
        scored_pairs: List[Tuple[ChunkData, float]] = []
        for chunk, score in zip(candidate_chunks, raw_scores):
            score_float = float(score)
            if score_float > 0.001:
                scored_pairs.append((chunk, score_float))

        if not scored_pairs:
            return []

        # 5. Sort descending by raw score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        # 6. Deduplicate and limit to top_k
        seen_ids: Set[str] = set()
        deduped: List[Tuple[ChunkData, float]] = []
        for c, s in scored_pairs:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                deduped.append((c, s))
                if len(deduped) >= top_k:
                    break

        # 7. Normalize scores to [0.0, 1.0]
        max_score = max(s for _, s in deduped) if deduped else 1.0
        results: List[Tuple[ChunkData, float, float]] = []
        for chunk, raw in deduped:
            norm = min(1.0, max(0.0, raw / max_score)) if max_score > 0 else 0.0
            results.append((chunk, round(raw, 4), round(norm, 4)))

        return results
