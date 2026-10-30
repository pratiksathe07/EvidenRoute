# EvidenRoute — Architecture & System Contracts Specification

## 1. System Overview & Vision

**EvidenRoute** is an intelligent context selection and evidence evaluation engine situated between an AI agent and diverse knowledge sources (knowledge bases, ticket repositories, conversation logs, etc.).

Instead of blindly querying every available source and feeding noisy, unverified context to an LLM, EvidenRoute:
1. **Analyzes queries** to determine topic, intent, and source relevance.
2. **Selects and ranks sources** dynamically to avoid wasteful searches.
3. **Enforces a strict retrieval budget** (API calls, candidate count, token ceiling).
4. **Evaluates evidence** across four orthogonal dimensions: *Relevance*, *Authority*, *Freshness*, and *Directness*.
5. **Detects contradictions** between sources (distinguishing actual factual/status conflicts from temporal updates).
6. **Performs an Evidence Stress Test** (bounded counterevidence search using remaining budget).
7. **Determines sufficiency** to decide whether to `ANSWER` with precise citations, `RETRIEVE_MORE` (if budget allows), or `ABSTAIN` (honestly acknowledging uncertainty or conflict).

---

## 2. Core Modules & Data Flow

```
                      [ User Query + Budget Config ]
                                    │
                                    ▼
                        [ 1. Query Understanding ]
                        (Intent, entities, domains)
                                    │
                                    ▼
                      [ 2. Intelligent Source Selector ]
                     (Ranks sources: Docs vs Tickets vs Chats)
                                    │
                                    ▼
                    [ 3. Central Budget Allocation ]
                   (Allots quotas based on remaining budget)
                                    │
                                    ▼
                    [ 4. Selected Source Adapters ]
                     (Executes bounded lexical/FTS5 searches)
                                    │
                                    ▼
                      [ 5. Evidence Evaluator ]
               (Scores: Relevance, Authority, Freshness, Directness)
                                    │
                                    ▼
                    [ 6. Contradiction Detector ]
                   (Subject, temporal, & value conflicts)
                                    │
                                    ▼
                   [ 7. Evidence Sufficiency Gate ]
                   /                               \
         [ Insufficient / Exhausted ]      [ Candidate Answer Formed ]
                  │                                     │
                  │                          [ 8. Stress Test Enabled? ]
                  │                          /                         \
                  │                    (Yes: Bounded Search)        (No)
                  │                    using remaining budget          │
                  │                          │                         │
                  │                    [ Counterevidence               │
                  │                      Found / Clear ]               │
                  │                          │                         │
                  ▼                          ▼                         ▼
              [ ABSTAIN ]            [ Final Decision: ANSWER / ABSTAIN ]
         (Transparent Reason)        (With Verified Source Citations)
```

---

## 3. Normalized Evidence Format (Pydantic Contract)

Every source adapter must return evidence adhering to this uniform schema:

```json
{
  "evidence_id": "doc_kb_001_chunk_2",
  "source_id": "kb_official_docs",
  "source_type": "document",
  "title": "Refund Policy v3.2",
  "content": "Customers are eligible for a 100% refund within 14 calendar days of purchase.",
  "uri": "https://internal.docs/policies/refunds-v3.2.md#section-4",
  "created_at": "2025-01-15T09:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z",
  "author": "Policy Team",
  "authority_score": 0.95,
  "metadata": {
    "version": "3.2",
    "department": "Billing",
    "tags": ["refund", "billing", "policy"]
  }
}
```

---

## 4. Central Budget Manager Contract

The budget manager enforces that no retrieval or stress test can bypass limits.

- **Configurable Dimensions:**
  - `max_source_calls`: Maximum allowable adapter calls per query run (e.g. 5).
  - `max_candidates`: Maximum total evidence records retrieved (e.g. 15).
  - `max_tokens`: Evidence token ceiling (e.g. 4000 tokens).

- **Operations:**
  - `reserve(calls, candidates, tokens) -> bool`: Atomically check and reserve budget before invoking adapters.
  - `record_consumption(actual_calls, actual_candidates, actual_tokens)`: Adjust reserved budget to actual consumption.
  - `get_remaining() -> BudgetState`: Returns remaining allowance.
  - `has_budget_for(dimension, amount) -> bool`: Checks feasibility.

---

## 5. Decision Outcomes

1. **`ANSWER`**:
   - Evidence sufficiency threshold met.
   - No unresolvable critical contradictions.
   - All assertions cite verified `evidence_id`s.
2. **`RETRIEVE_MORE`**:
   - Initial evidence is promising but incomplete.
   - Budget remains for targeted secondary retrieval.
3. **`ABSTAIN`**:
   - Evidence is insufficient, sources irreconcilably conflict, or budget exhausted before reaching confidence threshold.
   - A clear explanation of why the system abstained is provided.

---

## 6. Team Division & Module Responsibilities

| Role | Focus Area | Key Deliverables |
| :--- | :--- | :--- |
| **Member 1 (You & Pair)** | Backend & Core APIs | FastAPI server, SQLite DB, Budget Manager, Source Adapters, REST endpoints, Pydantic schemas. |
| **Member 2** | AI & Intelligence Engine | Query Understanding, Source Selector heuristics, Evidence Evaluation formulas, Contradiction Engine, Stress Test logic. |
| **Member 3** | Frontend & UI | React + Vite dashboard, Query Workspace, Source Studio, Evidence Explorer, Visual Execution Trace. |
| **Member 4** | Datasets, Benchmarks & Validation | Test datasets (Docs, Tickets, Chats), Ground-truth evaluation benchmarks, Baseline comparison scripts. |
