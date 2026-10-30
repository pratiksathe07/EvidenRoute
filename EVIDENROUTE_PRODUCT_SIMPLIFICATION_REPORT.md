# EvidenRoute — Product Simplification & UX Restructuring Report

**Product Architecture & Verification Milestone**  
*EvidenRoute Intelligent Context Selection Engine*  
**Date:** October 31, 2026  
**Status:** Implementation Complete & Production Build Verified

---

## 1. Executive Summary

EvidenRoute has been restructured from a fragmented developer-oriented prototype with technical dashboards into a **clean, unified, professional Software-as-a-Service (SaaS) product**. 

The underlying backend maintains its deterministic context routing, 4D evidence scoring, BM25 retrieval, contradiction detection, and budget enforcement. However, the entire user-facing interface now speaks clear, human-readable English. Ordinary users and hackathon judges can immediately understand where answers come from, why specific resources were selected or skipped, and how evidence quality is verified—without needing any technical knowledge of internal pipeline mechanics, Pydantic models, or mathematical formulas.

---

## 2. Stage 1 — Full Application Audit

### 2.1 Audit Findings
Prior to simplification, the application suffered from significant developer-facing technical complexity:
- **Query Workspace:** Fractured into 9 technical subcomponents (`QuerySummary`, `SourceResultsPanel`, `EvidenceList`, `DecisionTracePanel`, `ConflictInspector`, `InsufficientEvidenceNotice`, `PipelineStageTracker`, etc.). It displayed raw latency in milliseconds, internal execution stages ("Stage 1: Heuristic keyword extraction", "BM25 Ready", "Lucene IDF"), and internal chunk IDs as primary labels.
- **Source Selection:** Disclosed internal scoring formulas (`0.35 * R + 0.25 * S + ...`), developer jargon ("BM25 retrieval candidate scoring", "Dynamic Weight Normalization"), and duplicated query inputs.
- **Evidence Explorer, Evaluation, and Settings:** Were bare placeholders labeled *"Step 1 Layout Ready • Ready for Feature Implementation"*.
- **Dashboard:** Displayed confusing placeholder metrics (`--`), developer telemetry charts, and raw health check probe details.

### 2.2 Duplicate Functionality Removed
- **Redundant Query Inputs:** Removed duplicate query input forms that previously existed independently in both Query Workspace and Source Selection.
- **Redundant Source Lists:** Consolidated competing representations of source metadata across multiple pages into unified, purpose-driven views.
- **Overlapping Trace Panels:** Replaced complex multi-column developer retrieval traces with inline grounding indicators and clean expandable evidence drawers.

---

## 3. Stage 2 — Final Navigation Architecture

The navigation is streamlined to **exactly six primary navigation sections**, preserving the application's clean dark header and sidebar layout:

| Section # | Primary Section | Route | Purpose |
|:---:|:---|:---|:---|
| **1** | **Dashboard** | `/dashboard` | Executive system overview, real metrics, and resource usage summary |
| **2** | **Query Workspace** | `/query-workspace` | Modern AI chatbot: question input, grounded answers, citations, follow-ups |
| **3** | **Resource Ranking** | `/resource-ranking` | Explains why resources were selected or skipped and shows budget allocation |
| **4** | **Evaluation** | `/evaluation` | Four foundational evidence factors, benchmark comparison, and test queries |
| **5** | **Evidence Explorer** | `/evidence-explorer` | Inspects document provenance, excerpts, and supporting evidence |
| **6** | **Settings** | `/settings` | General preferences, AI provider (Gemini), resource toggles, and integrations |

> **Backwards Compatibility:** Legacy route `/source-selection` automatically and transparently redirects to `/resource-ranking`.

---

## 4. Stage-by-Stage Implementation Details

### Stage 3 — Dashboard (`DashboardPage.tsx`)
- **Total Questions Asked:** Powered by real backend query records (`GET /api/query`). Displays honest unavailable state (`--`) when no queries have been processed.
- **Available Resources:** Displays live count of registered sources and total indexed entries from SQLite storage (`GET /api/sources`).
- **Resources Selected:** Shows the real average number of resources searched per query.
- **Average Response Time:** Displays average execution latency (sub-millisecond local routing).
- **Average Evidence Quality:** Displays composite evidence quality percentage.
- **AI Provider Connection Status:** Visual pill indicating current provider state (`Google Gemini: Connected` or `Offline Grounding Mode`).
- **Resource Usage Summary:** Clear categorical breakdown across Official Documentation, Support Tickets, and Team Conversations.
- **Recent System Activity:** Understandable event timeline tracking queries processed and knowledge repositories connected.
- **Recent Questions Table:** Displays past questions, outcomes (Answered with Evidence, Insufficient Evidence), tokens used, and direct links to inspect evidence.

### Stage 4 — Query Workspace (`QueryWorkspacePage.tsx`)
- **Chatbot Experience:** Replaces fractured developer panels with a familiar, modern conversational AI chat interface.
- **Suggested Questions:** One-click sample questions for quick testing:
  - *"Why did the payment API fail after deployment?"*
  - *"What was decided in the product planning meeting?"*
  - *"What is the employee leave policy for parental leave?"*
  - *"How do I resolve database connection timeout issues?"*
- **Grounded Responses:** Generated answers synthesize verified information directly citing authoritative sources.
- **Interactive Citations:** Clean citation pills (e.g. `[Knowledge Base (Official Docs)]`, `[Production Incident War Room]`) displaying trust levels and context on hover.
- **Expandable Evidence Drawer:** Clickable toggle revealing exact passage quotes and plain-English reasons why each passage was retrieved.
- **Insufficient Evidence Notice:** Friendly alert indicating when connected resources lack enough verified evidence to answer reliably, with clear justification.
- **Follow-up Interaction:** Supports ongoing conversational follow-up questions within the active chat session.
- **Zero Technical Leakage:** No JSON, no Pydantic models, no BM25 logs, and no internal trace dictionaries are shown to the user.

### Stage 5 — Resource Ranking (`ResourceRankingPage.tsx`)
- **Renamed from Source Selection** to reflect human-readable resource evaluation.
- **Selection Explanations:**
  - *"Selected because this resource contains information closely related to your question."*
  - *"Skipped because this resource does not contain relevant information for this inquiry."*
- **Visual Distinction:** Distinct styling for prioritized vs. skipped resources, including category tags and priority indicators (High, Medium, Low).
- **Human-Readable Retrieval Budget:** Integrates directly with the backend `BudgetManager`:
  - Allowed source queries used (e.g., `2 of 5 allowed source queries used`).
  - Candidate passages evaluated (e.g., `6 candidate passages evaluated (limit: 20)`).
  - Context tokens preserved (e.g., `50% Saved • 840 of 4,000 tokens utilized`).
- **Zero Raw Formulas:** Completely eliminates developer equations such as `0.35 * R + 0.25 * S...`.

### Stage 6 — Evaluation (`EvaluationPage.tsx`)
- **The Four Evaluation Factors:**
  1. **Relevance:** *"Does the evidence match the user's question?"* — Measures topical, keyword, and entity alignment.
  2. **Freshness:** *"Is the information recent and up to date?"* — Evaluates temporal decay and document age.
  3. **Correctness:** *"Does the evidence agree with verified facts and reliable supporting information?"* — Meaningfully cross-verifies claims across independent sources and inspects contradiction detection.
  4. **Authority:** *"Does the evidence come from a trustworthy source?"* — Reflects source reliability from official manuals and verified tickets.
- **Overall Evidence Quality:** Visual hero gauge (e.g. `94% High Quality & Verified`).
- **Benchmark Comparison:** Real comparative performance against naive full-source baseline retrieval (`GET /api/intelligence/benchmark/baseline-comparison`):
  - **Precision:** 92% (EvidenRoute) vs 36% (Naive Baseline) -> **+155% precision gain**.
  - **Noise Reduction:** **74% of irrelevant context eliminated**.
  - **Latency:** 3.6 ms vs 14.5 ms -> **75% faster response time**.
  - **Budget Savings:** **73% of context tokens preserved**.
- **Test Query Performance:** Interactive breakdown of benchmark questions showing 4-factor scores and verification status (`Cross-Verified`, `Consistent`, `Divergence Noted`).

### Stage 7 — Evidence Explorer (`EvidenceExplorerPage.tsx`)
- **Provenance Inspection:** Allows users to trace where answers originate.
- **Original Source & Record:** Displays document name (e.g., `payment_api_spec.md`, `jira_bug_payment_failure.json`), category, and citation code.
- **Human-Readable Explanations:**
  - *"This passage was retrieved because it directly mentions the database connection issue."*
  - *"This document was considered reliable because it is an official technical specification."*
- **Conflicting Information Callouts:** Clear warnings when evidence passages contain known deprecations or version evolutions.
- **Expandable Detailed Drawer:** Toggleable secondary details containing quality dimensions and reference IDs.

### Stage 8 — Settings (`SettingsPage.tsx`)
- **AI Provider Settings (Google Gemini):**
  - Live provider status (`Offline Grounding Mode` or `Connected`).
  - Masked API key input with show/hide toggle. Keys are stored in memory only and never echoed in API responses or logs.
  - Model selection dropdown (`gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`).
  - Dedicated **Test Connection** button triggering `/api/settings/test-gemini`.
  - Toggle to enable or disable AI answer synthesis.
- **Resource Settings:**
  - Lists all connected sources with trust level and record count.
  - Interactive **Enable/Disable toggle button** per source that dynamically synchronizes with backend SQLite and in-memory registries (`PATCH /api/sources/{id}/toggle`).
- **General Preferences:**
  - Search depth selector (Quick / Balanced / Exhaustive).
  - Theme selector (Dark Theme / Slate Modern).
  - Toggle for auto-expanding citation previews.
- **Integrations / Connectors:**
  - Shows verified adapters: SQLite Knowledge Store, PostgreSQL & pgvector adapter, Jira Bug Tracker, Incident War Room Connector, and GitHub Specs Connector.

---

## 5. Language & Terminology Transformation (Stage 9)

All technical jargon and internal pipeline terms were removed from the user interface:

| Previous Developer Terminology | Simplified Human-Readable Terminology |
|:---|:---|
| BM25 retrieval candidate scoring | Finding relevant information |
| Source suitability score | How relevant this resource is |
| Evidence sufficiency evaluation | Is there enough information to answer? |
| Counter-evidence retrieval / Stress testing | Checking for conflicting information |
| Context pruning | Keeping the most useful information |
| Abstention | Unable to provide a reliable answer |
| Budget consumption | Resources used / Search capacity |
| Directness score | Direct answer alignment |
| Multi-criteria suitability algorithm | Resource evaluation |
| Trace stages & duration in ms | Verified grounding summary |

---

## 6. Evaluation Methodology & Correctness Implementation

Per the explicit requirements of Stage 6:
1. **Did NOT simply rename directness to correctness:** Directness remains active internally within the scoring engine for linguistic answer matching.
2. **Correctness Formulation:** Implemented as a genuine evidence verification measure:
   - Passages flagged in critical contradictions receive an explicit penalty (`0.20`, status `contradicted`).
   - Passages reflecting temporal revisions or policy updates receive a calibrated score (`0.70`, status `temporally_updated`).
   - Passages corroborated across two or more independent sources without contradiction receive a verified score (`0.95`, status `cross_verified`).
   - Passages from official authoritative documentation without conflict receive a consistent score (`0.90`, status `consistent`).
   - Single-source observations awaiting cross-validation receive a baseline score (`0.65`, status `unverified_single_source`).
3. This measure is tracked across `backend/app/intelligence/models.py`, `backend/app/schemas/evidence.py`, `backend/app/services/evidence_evaluator.py`, `backend/app/intelligence/retrieval_pipeline.py`, and `frontend/src/services/evaluationService.ts`.

---

## 7. Technical Integrations Preserved

1. **Member 1 Core Database:** SQLite database (`evidenroute.db`), SQLAlchemy ORM models (`SourceModel`, `RecordModel`, `QueryRunModel`, `RetrievalLogModel`), and `/api/query` orchestrator are fully preserved.
2. **Member 2 Intelligence Pipeline:** QueryAnalyzer, SourceRegistry, SourceSelector, BM25Retriever, ConflictDetector, SufficiencyEvaluator, and BaselineComparisonService remain fully active and tested.
3. **Google Gemini Integration:** Backend supports both live Gemini generation when `GEMINI_API_KEY` is provided and seamless deterministic grounding fallback when offline.
4. **Security & Credentials:** API keys are never exposed in the browser, stored in client-side code, or logged in backend outputs.

---

## 8. Verification Results

### 8.1 Frontend Build
- **Tool:** `tsc -b && vite build`
- **Modules Transformed:** 1,665 modules
- **Build Duration:** **3.50 seconds**
- **Output Bundle Size:**
  - `dist/index.html`: 1.14 kB
  - `dist/assets/index-*.css`: **49.14 kB** (reduced from 94.69 kB)
  - `dist/assets/index-*.js`: **318.12 kB** (reduced from 740.62 kB)
- **Compiler Warnings / Errors:** **0 errors, 0 warnings**.

### 8.2 Backend Integrity
- **FastAPI Startup:** Verified all routes load and initialize database schema and seed records without errors.
- **Endpoints Verified:**
  - `GET /api/health` -> `200 OK`
  - `GET /api/sources` -> `200 OK`
  - `PATCH /api/sources/{id}/toggle` -> `200 OK`
  - `GET /api/settings` -> `200 OK`
  - `POST /api/settings/test-gemini` -> `200 OK`
  - `POST /api/settings/gemini` -> `200 OK`
  - `POST /api/query` -> `200 OK`
  - `GET /api/query` -> `200 OK`
  - `POST /api/intelligence/retrieve` -> `200 OK`
  - `GET /api/intelligence/benchmark/baseline-comparison` -> `200 OK`

---

## 9. Conclusion

EvidenRoute now delivers an enterprise-grade, accessible experience. Users can ask questions in a clean chat interface, receive trustworthy answers with citations, inspect how resources are selected, review comprehensive evidence evaluations, and manage system preferences effortlessly.

