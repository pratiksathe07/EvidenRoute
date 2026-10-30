# EvidenRoute — Intelligent Context Selection & Evidence Scoring Engine
> **Hackathon Problem Statement 1 | Round 3 — Development Progress Review**  
> *Phase 1: Project Foundation, Deterministic Query Understanding & Intelligent Source Selection*  
> *Phase 2: Hybrid Retrieval & Multi-Dimensional Evidence Scoring Engine*  
> *Phase 3: Factual Conflict Detection, Evidence Sufficiency & Answer Readiness Control*

---

## 1. Executive Summary

**EvidenRoute** is a local-first, explainable, and budget-aware context selection engine. Instead of blindly sending every user prompt across all available enterprise databases, communication channels, and documentation repositories (which wastes tokens, degrades retrieval quality, and leaks budget), EvidenRoute acts as an intelligent pre-retrieval routing and evidence scoring layer:
- **Phase 1 (Context Selection)**: Decides where an AI agent should search, which sources are relevant, how they are prioritized, and why each source was selected or skipped.
- **Phase 2 (Hybrid Retrieval & Evidence Scoring)**: Searches strictly within selected sources, retrieves candidate passages, and scores evidence across 4 independent dimensions: Relevance, Authority, Freshness, and Directness.
- **Phase 3 (Conflict Detection & Answer Sufficiency)**: Dissects factual claims across multi-source evidence, flags direct contradictions while recognizing temporal and version evolutions, computes multi-factor answer sufficiency, deduplicates context while shielding citations and conflicts, and delivers an explainable answer-readiness decision.

All intelligence operates **locally and deterministically** without external API keys, paid services, or cloud dependencies. The architecture is modular and interface-ready for Google Gemini and PostgreSQL/pgvector integration in subsequent phases.

---

## 2. System Architecture

```text
EvidenRoute/
│
├── frontend/                                   # React 19 + TypeScript + Vite UI
│   ├── src/
│   │   ├── App.tsx                             # Intelligence Studio (Dual-Mode: Selection + Retrieval)
│   │   ├── App.css                             # Vanilla CSS (Modern Dark Theme, No Tailwind)
│   │   ├── types.ts                            # Strict TypeScript API Data Contracts
│   │   ├── index.css                           # Global tokens & CSS variables
│   │   └── main.tsx                            # React root mount
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                                    # Python FastAPI Intelligence Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── intelligence_routes.py          # REST Endpoints (Analyze, Select, Plan, Ingest, Retrieve, Health)
│   │   │
│   │   ├── intelligence/                       # Core Intelligence Engine (Local-First)
│   │   │   ├── __init__.py                     # Package exports
│   │   │   ├── models.py                       # Pydantic Schemas & Validation Models
│   │   │   ├── query_analyzer.py               # Deterministic Linguistic & Intent Analyzer
│   │   │   ├── source_registry.py              # BaseSourceRegistry & In-Memory Store
│   │   │   ├── source_selector.py              # Multi-Factor Source Selection Scoring
│   │   │   ├── pipeline.py                     # Context Routing Pipeline & Trace
│   │   │   ├── storage.py                      # BaseChunkStore & InMemoryChunkStore (PostgreSQL Interface)
│   │   │   ├── chunker.py                      # Sentence-Aware Passage Chunking & Deterministic Hashing
│   │   │   ├── ingestion.py                    # Local Ingestion Service (Markdown, JSON, Tickets)
│   │   │   ├── retriever.py                    # BM25 Keyword Retriever (Lucene IDF & Identifier Bonus)
│   │   │   ├── embedding_provider.py           # Lazy Sentence Transformers Provider & Hybrid Interface
│   │   │   ├── evidence_scorer.py              # 4-Dimension Evidence Scorer (R, A, F, D)
│   │   │   └── retrieval_pipeline.py           # End-to-End Retrieval & Evidence Ranking Pipeline
│   │   │
│   │   ├── core/
│   │   │   └── config.py                       # App settings, CORS, PostgreSQL placeholder
│   │   │
│   │   └── main.py                             # FastAPI Entrypoint & CORS Middleware
│   │
│   ├── tests/                                  # Automated Pytest Suite (47 Tests Passing)
│   │   ├── test_query_analyzer.py              # Intent, entity, keyword, and edge case tests
│   │   ├── test_source_selector.py             # Benchmark 1-5 & scoring normalization tests
│   │   ├── test_intelligence_api.py            # Phase 1 REST endpoints & CORS tests
│   │   ├── test_chunker_and_ingestion.py       # Markdown, conversation, ticket chunking & ingestion
│   │   ├── test_retrieval_and_evidence.py      # BM25, semantic provider, evidence scoring, pipeline
│   │   └── test_retrieval_api.py               # Phase 2 REST endpoints (/ingest, /retrieve, /retrieval-health)
│   │
│   ├── requirements.txt                        # Backend dependencies
│   └── .env.example                            # Config template & PostgreSQL placeholders
│
├── data/                                       # Local Demo Knowledge Repositories
│   ├── documents/                              # Technical API specs, DB guides, HR handbook
│   │   ├── payment_api_spec.md
│   │   ├── db_troubleshooting_guide.md
│   │   └── employee_leave_handbook.md
│   │
│   ├── conversations/                          # Meeting & incident war room chat transcripts
│   │   ├── planning_meeting_transcript.json
│   │   └── incident_war_room_chat.json
│   │
│   └── tickets/                                # Jira & customer bug reports
│       ├── jira_bug_payment_failure.json
│       └── jira_bug_db_timeout.json
│
├── pytest.ini                                  # Pytest configuration with pythonpath=backend
├── .gitignore                                  # Git exclusion list
└── README.md                                   # Comprehensive Project Documentation
```

---

## 3. Core Intelligence Modules

### Phase 1: Context Selection Routing
1. **Query Analyzer (`query_analyzer.py`)**: Local deterministic linguistic parser identifying intent, technical terms, keywords, multi-word entities, information category, expected evidence types, and likely source types.
2. **Source Registry (`source_registry.py`)**: In-memory registry with abstract `BaseSourceRegistry` interface decoupled from physical storage.
3. **Source Selector (`source_selector.py`)**: 5-factor pre-retrieval scoring:
   $$\text{Source Score} = 0.35 \times \text{Relevance} + 0.25 \times \text{Suitability} + 0.20 \times \text{Authority} + 0.10 \times \text{Historical} + 0.10 \times \text{Availability}$$
   Implements proportional weight normalization for missing historical data and unconditional skip for offline sources.
4. **Context Pipeline (`pipeline.py`)**: Produces an auditable `PipelineDecisionTrace`.

### Phase 2: Hybrid Retrieval & Evidence Scoring
1. **Storage Interface (`storage.py`)**: `BaseChunkStore` interface decouples retrieval from PostgreSQL/pgvector. `InMemoryChunkStore` provides thread-safe fast indexing by `source_id`.
2. **Document Chunker (`chunker.py`)**: Structure-preserving chunker for markdown (section headers and paragraphs), conversation transcripts (grouped dialogue turns), and tickets (title, status, priority, description, resolution). Generates deterministic SHA-256 chunk IDs.
3. **Ingestion Service (`ingestion.py`)**: Discovers files in `data/`, maps them to registered source IDs, resolves authority levels, and outputs structured `IngestionReport`.
4. **BM25 Retriever (`retriever.py`)**: Robertson/Lucene BM25Okapi implementation with positive IDF guarantee on small corpora and exact identifier matching. **Strictly filters candidate passages to sources selected in Phase 1**.
5. **Semantic Embedding Provider (`embedding_provider.py`)**: `BaseEmbeddingProvider` interface with optional `SentenceTransformerEmbeddingProvider` (`all-MiniLM-L6-v2`). Model loading is lazy; automatic downloads are prohibited. Reports `retrieval_mode = "lexical_only"` when offline and `hybrid` when enabled.
6. **Evidence Scoring Engine (`evidence_scorer.py`)**:
   Passages are evaluated across four independent dimensions:
   - **Relevance ($R \in [0, 1]$)**: Normalized retrieval score.
   - **Authority ($A \in [0, 1]$)**: Inherited source trust level.
   - **Freshness ($F \in [0, 1]$)**: Exponential decay formula:
     $$F = 2^{-\text{AgeDays} / \text{HalfLifeDays}}$$
     *(Missing timestamps are marked unknown; freshness weight is dynamically normalized across active dimensions).*
   - **Directness ($D \in [0, 1]$)**: Transparent rule-based classification into `direct` (1.0), `supporting` (0.75-0.85), `indirect` (0.45), or `tangential` (0.15).
   - **Final Evidence Score**:
     $$E = 0.35 R + 0.25 A + 0.20 F + 0.20 D$$
7. **Retrieval Pipeline (`retrieval_pipeline.py`)**: Connects Phase 1 and Phase 2. If Phase 1 selects zero sources (e.g. unrelated query), retrieval terminates early, preserving 100% of retrieval budget.

---

## 4. REST API Endpoints

| Method | Endpoint | Phase | Description |
|:-------|:---------|:------|:------------|
| `POST` | `/api/intelligence/analyze-query` | Phase 1 | Extracts intent, keywords, entities, and likely source types. |
| `POST` | `/api/intelligence/select-sources` | Phase 1 | Ranks registered sources with multi-factor scores and explanations. |
| `POST` | `/api/intelligence/plan` | Phase 1 | Returns complete source selection decision trace. |
| `GET` | `/api/intelligence/health` | Phase 1 | Reports component status and unconfigured LLM state. |
| `GET` | `/api/intelligence/sources` | Phase 1 | Lists all candidate sources in the registry. |
| `POST` | `/api/intelligence/ingest` | Phase 2 | Triggers local document chunking and ingestion. |
| `GET` | `/api/intelligence/ingestion-status`| Phase 2 | Returns total stored chunks and last ingestion report. |
| `POST` | `/api/intelligence/retrieve` | Phase 2 | Executes Phase 1 context routing + Phase 2 evidence scoring. |
| `GET` | `/api/intelligence/retrieval-health`| Phase 2 | Reports diagnostic health of Ingestion, BM25, and Scorer. |

---

## 5. Setup & Execution Instructions

### 5.1 Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Swagger Docs:** `http://localhost:8000/docs`
- **Retrieval Health:** `http://localhost:8000/api/intelligence/retrieval-health`

### 5.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Studio Interface:** `http://localhost:5173/`

### 5.3 Automated Testing
```bash
python -m pytest -v
```

---

## 6. Automated Test Results (47 Passed)

```text
backend/tests/test_chunker_and_ingestion.py::test_markdown_chunking_and_headers PASSED [  2%]
backend/tests/test_chunker_and_ingestion.py::test_deterministic_chunk_ids PASSED [  4%]
backend/tests/test_chunker_and_ingestion.py::test_conversation_chunking PASSED [  6%]
backend/tests/test_chunker_and_ingestion.py::test_ticket_chunking PASSED [  8%]
backend/tests/test_chunker_and_ingestion.py::test_ingestion_service_real_files PASSED [ 10%]
backend/tests/test_chunker_and_ingestion.py::test_ingestion_malformed_and_empty_file_resilience PASSED [ 12%]
backend/tests/test_chunker_and_ingestion.py::test_duplicate_reingestion_idempotence PASSED [ 14%]
backend/tests/test_intelligence_api.py::test_root_endpoint PASSED        [ 17%]
backend/tests/test_intelligence_api.py::test_health_check_endpoint PASSED [ 19%]
backend/tests/test_intelligence_api.py::test_sources_list_endpoint PASSED [ 21%]
backend/tests/test_intelligence_api.py::test_analyze_query_endpoint PASSED [ 23%]
backend/tests/test_intelligence_api.py::test_analyze_query_empty_error PASSED [ 25%]
backend/tests/test_intelligence_api.py::test_select_sources_endpoint PASSED [ 27%]
backend/tests/test_intelligence_api.py::test_plan_endpoint_complete_decision_trace PASSED [ 29%]
backend/tests/test_intelligence_api.py::test_plan_endpoint_unrelated_query PASSED [ 31%]
backend/tests/test_intelligence_api.py::test_cors_headers PASSED         [ 34%]
backend/tests/test_query_analyzer.py::test_payment_api_failure_example PASSED [ 36%]
backend/tests/test_query_analyzer.py::test_product_planning_decision PASSED [ 38%]
backend/tests/test_query_analyzer.py::test_employee_leave_policy PASSED  [ 40%]
backend/tests/test_query_analyzer.py::test_database_connection_timeout PASSED [ 42%]
backend/tests/test_query_analyzer.py::test_unrelated_topic_query PASSED  [ 44%]
backend/tests/test_query_analyzer.py::test_empty_and_whitespace_query PASSED [ 46%]
backend/tests/test_query_analyzer.py::test_special_characters_query PASSED [ 48%]
backend/tests/test_retrieval_and_evidence.py::test_bm25_technical_query_matching PASSED [ 51%]
backend/tests/test_retrieval_and_evidence.py::test_bm25_exact_identifier_matching PASSED [ 53%]
backend/tests/test_retrieval_and_evidence.py::test_bm25_selected_source_filtering_strictly_enforced PASSED [ 55%]
backend/tests/test_retrieval_and_evidence.py::test_bm25_empty_query_and_empty_index PASSED [ 57%]
backend/tests/test_retrieval_and_evidence.py::test_semantic_provider_lazy_loading_and_offline_safety PASSED [ 59%]
backend/tests/test_retrieval_and_evidence.py::test_evidence_scoring_dimensions PASSED [ 61%]
backend/tests/test_retrieval_and_evidence.py::test_freshness_decay_calculation PASSED [ 63%]
backend/tests/test_retrieval_and_evidence.py::test_missing_timestamp_weight_normalization PASSED [ 65%]
backend/tests/test_retrieval_and_evidence.py::test_pipeline_payment_api_question PASSED [ 68%]
backend/tests/test_retrieval_and_evidence.py::test_pipeline_unrelated_query_budget_preservation PASSED [ 70%]
backend/tests/test_retrieval_api.py::test_api_trigger_ingestion PASSED   [ 72%]
backend/tests/test_retrieval_api.py::test_api_ingestion_status PASSED    [ 74%]
backend/tests/test_retrieval_api.py::test_api_retrieve_endpoint PASSED   [ 76%]
backend/tests/test_retrieval_api.py::test_api_retrieve_empty_validation_error PASSED [ 78%]
backend/tests/test_retrieval_api.py::test_api_retrieval_health PASSED    [ 80%]
backend/tests/test_source_selector.py::test_benchmark_1_payment_api_failure PASSED [ 82%]
backend/tests/test_source_selector.py::test_benchmark_2_product_planning_meeting PASSED [ 85%]
backend/tests/test_source_selector.py::test_benchmark_3_employee_leave_policy PASSED [ 87%]
backend/tests/test_source_selector.py::test_benchmark_4_database_connection_timeout PASSED [ 89%]
backend/tests/test_source_selector.py::test_benchmark_5_unrelated_topic PASSED [ 91%]
backend/tests/test_source_selector.py::test_empty_registry PASSED        [ 93%]
backend/tests/test_source_selector.py::test_unavailable_source_handling PASSED [ 95%]
backend/tests/test_source_selector.py::test_missing_metadata_weight_normalization PASSED [ 97%]
backend/tests/test_source_selector.py::test_configurable_thresholds PASSED [100%]

======================= 47 passed in 0.98s =======================
```

---

## 7. Evidence Citations & Results for Benchmark Questions

### Query: *"Why did the payment API fail after deployment?"*
- **Phase 1 Routing**:
  - `doc-api-gateway` (Selected)
  - `tkt-jira-bugs` (Selected)
  - `conv-incident-war-room` (Selected)
  - `doc-hr-policies` (Skipped: Unrelated)
- **Phase 2 Top Retrieved Evidence**:
  1. **Rank #1 (Evidence Score: 95.8%)**:
     - *Citation*: `[Production Incident & Deployment War Room Transcripts (conv-incident-war-room) § Chunk 1, File: incident_war_room_chat.json, Record: incident_war_room_chat]`
     - *Content Excerpt*: `lead-arch: The deployment misconfigured DB pool max size to 5 instead of 50. Rolling back the config hotfix now. dev-oncall: Hotfix deployed. Error rate back to normal at 0.02%.`
     - *Explanation*: Direct answer containing root cause and deployment recovery.
  2. **Rank #2 (Evidence Score: 91.9%)**:
     - *Citation*: `[Engineering Bug Tracker & Incident Reports (tkt-jira-bugs) § Chunk 0, File: jira_bug_payment_failure.json, Record: ENG-4029]`
     - *Content Excerpt*: `ENG-4029 (Bug): After release-2026.10-rc2 deployment, payments began failing intermittently with 504 gateway timeout... Resolution: Increased pool limit to 50 connections.`
     - *Explanation*: High authority bug ticket with matching entities and resolution.
  3. **Rank #3 (Evidence Score: 87.7%)**:
     - *Citation*: `[Payment & API Gateway Technical Specifications (doc-api-gateway) § Chunk 3, File: payment_api_spec.md, Record: payment_api_spec]`
     - *Content Excerpt*: `Deployment Notes (Release 2026.10-rc2): During deployment, connection pool timeouts were observed... Ensure MAX_DB_POOL_SIZE is at least 50.`

---

## 8. Database Integration Contract for Member 1

Member 1 can connect PostgreSQL and `pgvector` by implementing `BaseChunkStore` in `backend/app/intelligence/storage.py`:

```python
from app.intelligence.storage import BaseChunkStore
from app.intelligence.models import ChunkData
from typing import List, Optional

class PostgreSQLChunkStore(BaseChunkStore):
    def __init__(self, db_session):
        self.session = db_session

    def save_chunks(self, chunks: List[ChunkData]) -> None:
        ...

    def get_chunks_by_source_ids(self, source_ids: List[str]) -> List[ChunkData]:
        # SELECT * FROM document_chunks WHERE source_id = ANY(:source_ids)
        ...

    def get_all_chunks(self) -> List[ChunkData]:
        ...

    def get_chunk_by_id(self, chunk_id: str) -> Optional[ChunkData]:
        ...

    def count(self) -> int:
        ...

    def clear(self) -> None:
        ...
```

Suggested PostgreSQL Table Schema:
```sql
CREATE TABLE document_chunks (
    chunk_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES knowledge_sources(source_id),
    source_type VARCHAR(32) NOT NULL,
    record_id VARCHAR(128) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    authority_level NUMERIC(3, 2) NOT NULL,
    original_file_path VARCHAR(255) NOT NULL,
    chunk_index INT NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_chunks_source_id ON document_chunks(source_id);
```

---

## 9. Phase 3: Conflict Detection & Answer Sufficiency Control

### 9.1 Conflict Detection Engine (`conflict_detector.py`)
- Analyzes factual claims across documents, conversations, and tickets.
- Distinguishes **direct contradictions** from:
  - `temporal_supersedence`: newer policy or status update superseding older records.
  - `version_divergence`: differences across software specs (e.g. v1 vs v2).
  - `status_progression`: normal incident lifecycle transitions (e.g. investigating to resolved).
- Preserves chunk IDs, source IDs, citations, and conflicting sentence statements.

### 9.2 Evidence Sufficiency Evaluation (`sufficiency_evaluator.py`)
- Evaluates whether retrieved evidence provides enough facts to answer the question without hallucinating.
- Evaluates 6 dimensions: Relevance, Directness, Expected Coverage, Authority, Diversity, and Freshness.
- Calculates an explainable `sufficiency_score` $[0.0, 1.0]$ and assigns a deterministic `recommended_action`:
  - `answer`: high sufficiency ($\ge 0.70$), direct corroboration, zero unresolved contradictions.
  - `retrieve_more`: partially sufficient ($< 0.70$) or missing required info artifacts.
  - `clarify`: conflicting claims detected across authoritative evidence.
  - `abstain`: insufficient or missing evidence ($< 0.30$).

### 9.3 Budget-Aware Context Pruning (`context_pruner.py`)
- Deduplicates redundant sentences across passages while preserving citations and source metadata.
- **Conflict Shielding**: Sentences or passages involved in detected conflicts are never pruned.
- Preserves important technical identifiers, error codes (`504`, `500`), dates, decisions, and resolutions.
- Produces an audit report with `compression_ratio`, `pruned_details`, and retained evidence passages.

---

## 10. Running the Application

### Option A: Start the FastAPI Server & Interactive API Docs
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger API: **http://127.0.0.1:8000/docs**
- Health Check: **http://127.0.0.1:8000/api/health**
- Intelligence Health: **http://127.0.0.1:8000/api/intelligence/health**
- Source Catalog: **http://127.0.0.1:8000/api/sources**

### Option B: Start the React 19 Frontend UI
```bash
cd frontend
npm install
npm run dev
```
- Web Application: **http://localhost:5173**

### Option C: Run the Interactive Demo CLI
Runs 4 representative scenarios demonstrating verified answers, SLA temporal update resolution, Evidence Stress Testing, and honest abstention:
```bash
python -m backend.demo_cli
```

---

## 11. Test Suite & Verification (79 Passing Tests)

Run complete test suite across all modules:
```bash
python -m pytest -v
```

```text
======================= 79 passed, 17 warnings in 1.93s =======================
```

| Test Category | Test File | Tests Passed | Key Coverage |
| :--- | :--- | :---: | :--- |
| **Phase 1: Query Analyzer** | `test_query_analyzer.py` | 7 | Intent classification, entity extraction, keywords, empty/special queries |
| **Phase 1: Source Selector** | `test_source_selector.py` | 9 | Benchmarks 1-5, weight normalization, offline skipping, thresholds |
| **Phase 1: REST API** | `test_intelligence_api.py` | 9 | `/analyze-query`, `/select-sources`, `/plan`, `/health`, CORS headers |
| **Phase 2: Chunker & Ingestion** | `test_chunker_and_ingestion.py` | 6 | Markdown, JSON, tickets, chunk IDs, idempotency, malformed files |
| **Phase 2: Hybrid Retrieval & Scoring** | `test_retrieval_and_evidence.py` | 10 | BM25, exact IDs, source constraints, lazy embeddings, 4D scoring |
| **Phase 2: Retrieval REST API** | `test_retrieval_api.py` | 5 | `/ingest`, `/ingestion-status`, `/retrieve`, `/retrieval-health` |
| **Phase 3: Conflict & Sufficiency** | `test_phase3_conflict_and_sufficiency.py` | 15 | Contradictions, consistent facts, dates/versions, sufficiency, pruning, readiness, API |
| **Member 1: Sources & Ingestion API** | `test_api_sources.py` | 5 | Source registration, batch ingestion, duplicate checks, seed populator |
| **Member 1: Budget Manager** | `test_budget_manager.py` | 5 | Call limits, candidate thresholds, token limits, exhaustion |
| **Member 1: Data Contracts** | `test_contracts.py` | 3 | Pydantic model validation for queries, budgets, and evidence |
| **Member 1: Intelligence Endpoints** | `test_intelligence.py` | 5 | End-to-end answers, temporal contradictions, abstention, stress testing |
| **TOTAL** | **11 test modules** | **79 / 79 (100%)** | **Complete end-to-end regression validation** |

### Validate Datasets & Referential Integrity
```bash
python scripts/validate_datasets.py
```

---

## 12. Current Limitations & Roadmap
1. **Rule-Based Conflict Extraction**: Conflict detection currently uses deterministic attribute regex and polarity analysis. Designed to be augmented with Gemini LLM cross-examination in Phase 4.
2. **Lexical-First Default**: BM25 remains the active retrieval default per the local-first rule.
3. **Database Architecture**: SQLite is the active local database with full SQLAlchemy 2.0 ORM models; PostgreSQL + pgvector adapter interface is ready for cloud deployment.

---

## 13. License

This project is licensed under the MIT License - see the LICENSE file for details.
External datasets such as HotpotQA are governed by their respective licenses (e.g. CC BY-SA 4.0).
