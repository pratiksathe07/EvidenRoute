# EVIDENROUTE — QUERY WORKSPACE FUNCTIONAL IMPLEMENTATION REPORT

**Author:** Senior Product Engineer, React Developer, Backend Integration Engineer & UI/UX Architect  
**Project:** EvidenRoute — Intelligent Context Selection Engine  
**Milestone:** Query Workspace Functional Implementation  
**Status:** Complete & Verified  

---

## 1. SOURCE SELECTION PAGE ANALYSIS

Before touching the Query Workspace implementation, an in-depth audit of the **Source Selection Studio** (`/source-selection`) was conducted to understand its architectural purpose, data flow, backend contracts, and user experience.

### What the Source Selection Page Currently Does
- **Pre-Retrieval Source Discovery:** Displays all registered knowledge repositories (`GET /api/sources`) spanning Documents (`DOC-001`), Conversations (`CONV-001`), and Incident Tickets (`TICKET-001`).
- **Query-Aware Multi-Factor Ranking:** Calculates composite suitability scores (`POST /api/query` or `POST /api/intelligence/plan`) evaluating relevance, source type suitability, authority level, availability, and historical usefulness.
- **Selection versus Exclusion Explanations:** Explains why high-value sources are prioritized and why irrelevant or unavailable sources are skipped before retrieval begins.
- **Budget Preservation Tracking:** Visualizes reductions in source API calls and tokens saved by excluding off-topic context sources.
- **Decision Trace Visualizer:** Outlines step-by-step query understanding, keyword extraction, and source ranking metadata.

### Backend Endpoints Consumed by Source Selection
1. `GET /api/health` — Probes backend status and service health.
2. `GET /api/sources` — Fetches active registered sources and metadata.
3. `POST /api/query` / `POST /api/intelligence/plan` — Generates pre-retrieval ranking decisions and scoring traces.

---

## 2. EXISTING FUNCTIONALITY AND OVERLAP IDENTIFIED

To prevent duplicated functionality, duplicated components, redundant API calls, and cluttered interfaces, the boundaries between the two pages were strictly established:

| Feature / UI Concern | Source Selection Studio (`/source-selection`) | Query Workspace (`/query-workspace`) | Overlap Resolution |
|---|---|---|---|
| **Primary Goal** | Pre-retrieval source governance & ranking | End-to-end question answering & evidence synthesis | Decoupled workflows |
| **Input Focus** | Operational scenario / topic for source filtering | Natural language user question | Specialized textarea with keyboard shortcuts |
| **Source Registry Table** | Full registry with sliders, weights, and status | Excluded (Compact summary only) | Query Workspace provides a direct link to Source Selection Studio |
| **Evidence Retrieval** | Not displayed (Pre-retrieval only) | **Core feature** (BM25 bounded lexical passages) | Exclusive to Query Workspace |
| **4D Evidence Scoring** | Not displayed (Only source-level suitability) | **Core feature** (Relevance, Authority, Freshness, Directness) | Exclusive to Query Workspace |
| **Conflict & Contradiction** | Not displayed | **Core feature** (Contradictions, topics, claims, resolution hints) | Exclusive to Query Workspace |
| **Answer Synthesis & Citations** | Not displayed | **Core feature** (Grounding verdict, answer text, citations tray) | Exclusive to Query Workspace |
| **Execution Trace** | Source selection trace stages only | Complete 9-stage pipeline visualization | Query Workspace visualizes stages 1 through 9 |
| **Query History** | Not displayed | **Integrated** (`GET /api/query` database persistence) | Exclusive to Query Workspace |

---

## 3. FINAL RESPONSIBILITY SEPARATION

### A. Source Selection Studio (`/source-selection`)
- Granular source discovery and registry inventory.
- Weight adjustments (relevance, suitability, authority, historical, availability).
- Selection threshold configuration.
- Detailed multi-factor source score breakdown.
- Deep dive into source exclusion rationale.

### B. Query Workspace (`/query-workspace`)
- Natural language question input with real-world local dataset scenario suggestions.
- Execution of the complete 9-stage intelligence pipeline.
- Compact Execution Summary with link to Source Selection Studio.
- Dedicated Answer Workspace with readiness verdict, confidence bar, grounded answer, and citations.
- Interactive Evidence Explorer with 4D metrics, snippet toggle, and search/type filtering.
- Conflict & Sufficiency Panel with contradiction comparison cards and missing info checklist.
- Database-persisted query run history with reload capability.

---

## 4. BACKEND CAPABILITIES DISCOVERED & FEATURE AVAILABILITY MATRIX

| Feature | Implemented | API Available | Frontend Connected | Status Classification |
|---|---|---|---|---|
| **Query Analysis & Understanding** | Yes (Deterministic intent, entities, keywords) | Yes (`POST /api/intelligence/analyze-query`) | Yes | **Implemented and Verified** |
| **Source Selection Engine** | Yes (Multi-factor ranking & pruning) | Yes (`POST /api/intelligence/select-sources`, `POST /api/query`) | Yes | **Implemented and Verified** |
| **Budget Allocation & Ceilings** | Yes (Source calls, candidates, token quotas) | Yes (`POST /api/query`, `POST /api/intelligence/retrieve`) | Yes | **Implemented and Verified** |
| **Bounded Context Retrieval** | Yes (BM25 lexical index across selected sources) | Yes (`POST /api/intelligence/retrieve`) | Yes | **Implemented and Verified** |
| **Multi-Dimensional (4D) Evidence Scoring** | Yes (Relevance, Authority, Freshness, Directness) | Yes (`POST /api/intelligence/retrieve`) | Yes | **Implemented and Verified** |
| **Inter-Source Conflict Detection** | Yes (Direct contradiction, status progression, etc.) | Yes (`POST /api/intelligence/detect-conflicts`, `retrieve`) | Yes | **Implemented and Verified** |
| **Evidence Sufficiency Evaluation** | Yes (Sufficiency score, dimension scores, action) | Yes (`POST /api/intelligence/evaluate-evidence`, `retrieve`) | Yes | **Implemented and Verified** |
| **Counter-Evidence Stress Testing** | Yes (14 stress test scenarios, caveats, search) | Yes (`POST /api/intelligence/stress-test`, `retrieve`) | Yes | **Implemented and Verified** |
| **Budget-Aware Context Pruning** | Yes (Redundancy deduplication, conflict shielding) | Yes (`POST /api/intelligence/prune-context`, `retrieve`) | Yes | **Implemented and Verified** |
| **Google Gemini LLM Answer Generation** | Placeholder only (`GEMINI_API_KEY=""`) | No external API call made | Handled honestly with offline banner | **Backend Dependency Missing** (Handled transparently) |
| **Citation Tracking & Validation** | Yes (Citation references, source IDs, chunk IDs) | Yes (`POST /api/intelligence/retrieve`, `POST /api/query`) | Yes | **Implemented and Verified** |
| **Query Run Database Persistence** | Yes (`QueryRunModel` in PostgreSQL/SQLite) | Yes (`GET /api/query`, `GET /api/query/{id}`) | Yes | **Implemented and Verified** |

---

## 5. API ENDPOINTS INTEGRATED

1. `POST /api/intelligence/retrieve`: Primary endpoint for rich intelligence execution. Returns retrieved evidence passages, 4D scores, conflict detection results, sufficiency evaluation, context pruning, and decision trace stages.
2. `POST /api/query`: Secondary orchestrator execution. Persists query runs in the database, verifies budget quotas, and supplies verified deterministic answer summaries.
3. `GET /api/query?limit=20`: Fetches recent persisted execution history records.
4. `GET /api/query/{query_id}`: Retrieves single query execution run details from the database.
5. `GET /api/health`: Dynamic heartbeat probe verifying backend orchestrator availability on port 8000.

---

## 6. REUSED COMPONENTS & PATTERNS

- `apiClient` (`frontend/src/services/api.ts`): Reused centralized Axios instance with baseURL `http://127.0.0.1:8000`, standard error handling, and timeout configurations.
- `getSystemHealth` (`frontend/src/services/dashboardService.ts`): Reused system probe for live connection status.
- Design tokens & typography (`frontend/src/index.css`): Reused CSS variables for brand colors (`--accent-primary`), dark themes (`--sidebar-bg`), surfaces, status badges, typography (`Inter`, `JetBrains Mono`), and box shadows.
- Navigation Layout (`MainLayout.tsx`, `Sidebar.tsx`, `Header.tsx`): Maintained sidebar navigation active routing for `/query-workspace`.

---

## 7. NEW COMPONENTS CREATED

All new components reside in `frontend/src/components/query-workspace/` and have dedicated CSS modules adhering to vanilla CSS rules (NO Tailwind CSS):

1. **`WorkspaceQueryInput.tsx` + `WorkspaceQueryInput.css`**:
   - Multi-line auto-resizing textarea with keyboard shortcut support (`Ctrl+Enter` / `Cmd+Enter`).
   - Run Query and Clear buttons with spinning loading indicator.
   - Example scenario suggestion pills mapped to actual local dataset topics:
     - *Payment API Failure* (`Why did the payment API fail after deployment?`)
     - *Product Planning Decision* (`What was decided during the last product planning meeting?`)
     - *DB Connection Timeout* (`What caused the database connection timeout?`)
     - *Employee Leave Policy* (`What is the employee leave policy?`)
   - Visual validation errors and backend communication warnings.

2. **`ExecutionSummaryBar.tsx` + `ExecutionSummaryBar.css`**:
   - Compact status bar showing Sources Evaluated (`4 / 10`, 6 skipped), Evidence Passages retrieved (`5`), Pipeline Latency (`218 ms`), Source Calls Quota (`3 / 5 calls`), and Retrieval Mode (`lexical_only`).
   - Deep-link button to navigate to Source Selection Studio without duplicating its heavy tables.

3. **`PipelineStageTracker.tsx` + `PipelineStageTracker.css`**:
   - Tracks all 9 stages of the intelligence pipeline:
     1. Query Understanding & Analysis
     2. Intelligent Source Selection
     3. Budget Allocation & Enforcement
     4. Bounded Context Retrieval
     5. Multi-Dimensional Evidence Scoring (4D)
     6. Inter-Source Conflict Detection
     7. Evidence Sufficiency Evaluation
     8. Budget-Aware Context Pruning
     9. Gemini Answer Generation (Unconfigured / Skipped indicator)
   - Visual status badges (`Completed`, `Pending`, `Skipped`, `Failed`), stage duration in ms, summary trace text, and expandable JSON details dropdown.

4. **`AnswerWorkspacePanel.tsx` + `AnswerWorkspacePanel.css`**:
   - Grounding verdict (`READY_TO_ANSWER`, `ABSTAIN`, `CLARIFY`, `RETRIEVE_MORE`).
   - Offline Deterministic Gemini status banner clearly communicating that LLM generation is unconfigured while deterministic evidence grounding is active.
   - Formatted answer text with copy to clipboard action.
   - Readiness confidence meter and color-coded progress bar.
   - Engine decision rationale justification.
   - Cited evidence grounding pills (`[DOC-001]`, `[DOC-002]`).

5. **`EvidenceExplorerPanel.tsx` + `EvidenceExplorerPanel.css`**:
   - Expandable evidence cards with ranking badges (`#1`, `#2`...).
   - Source badges for Documents, Conversations, and Tickets.
   - 4D multi-dimensional metric progress bars: Relevance, Authority, Freshness, and Directness.
   - Citation references, Chunk IDs, and Source IDs.
   - Live text search and source type filter chips (`All`, `Document`, `Conversation`, `Ticket`).
   - Expand All / Collapse All controls.

6. **`ConflictSufficiencyPanel.tsx` + `ConflictSufficiencyPanel.css`**:
   - Sufficiency score percentage and progress gauge.
   - Sufficiency status (`Sufficient`, `Partially Sufficient`, `Contradictory`, `Insufficient`) and recommended action (`Answer`, `Clarify`, `Retrieve More`, `Abstain`).
   - Missing information and coverage gaps checklist.
   - Contradiction cards displaying conflict topic, severity (`Critical`, `Warning`, `Informational`), conflict type, conflicting claims compared side-by-side, and resolution hints.
   - Step 4 Counter-Evidence stress testing summary with decision impact and examined passage count.

7. **`QueryHistorySidebar.tsx` + `QueryHistorySidebar.css`**:
   - Displays real-time database-persisted query runs fetched from `GET /api/query`.
   - Displays query timestamp, question, outcome badge, and budget calls consumed.
   - One-click reloading of prior queries into the workspace.
   - Refresh button with rotate animation.

8. **`QueryWorkspacePage.tsx` + `QueryWorkspacePage.css`**:
   - Replaced placeholder card with comprehensive tabbed layout (`Answer & Supporting Evidence`, `Conflicts & Sufficiency`, `Execution Pipeline Trace`).
   - Responsive grid with sticky history sidebar.
   - Dynamic engine health status pill (`Pipeline Engine Online`).
   - Clean empty state hero guiding the user before submission.

---

## 8. FILES MODIFIED / CREATED

### Created Files
- `frontend/src/types/queryWorkspace.ts`
- `frontend/src/services/queryWorkspaceService.ts`
- `frontend/src/components/query-workspace/WorkspaceQueryInput.tsx`
- `frontend/src/components/query-workspace/WorkspaceQueryInput.css`
- `frontend/src/components/query-workspace/ExecutionSummaryBar.tsx`
- `frontend/src/components/query-workspace/ExecutionSummaryBar.css`
- `frontend/src/components/query-workspace/PipelineStageTracker.tsx`
- `frontend/src/components/query-workspace/PipelineStageTracker.css`
- `frontend/src/components/query-workspace/AnswerWorkspacePanel.tsx`
- `frontend/src/components/query-workspace/AnswerWorkspacePanel.css`
- `frontend/src/components/query-workspace/EvidenceExplorerPanel.tsx`
- `frontend/src/components/query-workspace/EvidenceExplorerPanel.css`
- `frontend/src/components/query-workspace/ConflictSufficiencyPanel.tsx`
- `frontend/src/components/query-workspace/ConflictSufficiencyPanel.css`
- `frontend/src/components/query-workspace/QueryHistorySidebar.tsx`
- `frontend/src/components/query-workspace/QueryHistorySidebar.css`
- `EVIDENROUTE_QUERY_WORKSPACE_IMPLEMENTATION_REPORT.md`

### Modified Files
- `frontend/src/pages/QueryWorkspacePage.tsx`
- `frontend/src/pages/QueryWorkspacePage.css`

*(Note: Zero files in `SourceSelectionPage.tsx` or `components/source-selection/` were modified, strictly honoring the requirement to protect existing functionality.)*

---

## 9. QUERY EXECUTION WORKFLOW

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Query Workspace (React)
    participant Svc as queryWorkspaceService
    participant API1 as POST /api/intelligence/retrieve
    participant API2 as POST /api/query
    participant DB as PostgreSQL / SQLite (QueryRunModel)

    User->>UI: Types query or clicks verified scenario pill
    User->>UI: Clicks "Run Query" (or Ctrl+Enter)
    UI->>UI: Validates non-empty input; sets isLoading=true
    UI->>Svc: executeWorkspaceQuery(question)
    par Parallel Execution
        Svc->>API1: POST /api/intelligence/retrieve (top_k=5, stress_test=true)
        API1-->>Svc: 4D scored evidence, conflicts, sufficiency, pruning
    and
        Svc->>API2: POST /api/query (budget ceilings, persistence)
        API2->>DB: Log QueryRunModel (query_id, question, outcome, calls, tokens)
        API2-->>Svc: QueryResponse (outcome, final_answer, budget_status)
    end
    Svc-->>UI: Unified WorkspaceExecutionResult (9 stages, latency, evidence)
    UI->>UI: Renders ExecutionSummaryBar & AnswerWorkspacePanel
    UI->>Svc: getQueryHistory()
    Svc->>DB: GET /api/query?limit=20
    DB-->>UI: Updates QueryHistorySidebar with persisted run
```

---

## 10. EVIDENCE AND CITATION INTEGRATION

Every passage retrieved through `POST /api/intelligence/retrieve` includes full origin metadata:
- **Source Identification:** Source Name, Source Type (`document`, `conversation`, `ticket`), Source ID (`DOC-001`), Chunk ID (`DOC-001_chunk_0`).
- **Citation Badges:** Referenced in the answer synthesis tray (`[DOC-001]`, `[DOC-002]`) and attached to individual passage headers.
- **4D Evidence Metrics:**
  - `Relevance`: BM25 lexical score normalized against query term frequency.
  - `Authority`: Source trust level (Tier 1 runbooks/docs: 0.95; Tier 2 tickets: 0.85; Tier 3 chat: 0.70).
  - `Freshness`: Decay computed relative to incident/query timeframe.
  - `Directness`: Ratio of exact claim statements to contextual background.
- **Filtering & Search:** Real-time client-side filter chips allow filtering by passage source type or searching text within passages without re-triggering network requests.

---

## 11. GEMINI INTEGRATION STATUS

- **Audit Finding:** In `backend/app/core/config.py`, `GEMINI_API_KEY: str = ""` is unconfigured.
- **Strict Compliance:** No fake API calls or synthetic LLM text generation were fabricated.
- **User Experience:**
  - An informational status banner in `AnswerWorkspacePanel` alerts the user:  
    *"Google Gemini LLM generation is currently unconfigured. The engine executed deterministic query understanding, source selection, 4D scoring, conflict detection, and context pruning."*
  - The answer workspace displays the deterministic verified evidence passages as the ground truth.
  - Stage 9 in `PipelineStageTracker` clearly displays status `Skipped (Unconfigured)` with 0 ms duration.

---

## 12. ERROR HANDLING & RESILIENCE

1. **Empty Query Submission:** Intercepted before dispatching any network request. The textarea displays an alert: *"Please enter a natural-language question to query the intelligence engine."*
2. **Backend Service Offline:** If the FastAPI backend is down, the header status chip turns amber (*Engine Standby (Port 8000)*), and query attempts fail gracefully with: *"Backend retrieval service is currently unreachable. Start the backend API on port 8000."*
3. **Double Submission Prevention:** While `isLoading` is true, submit and clear buttons are disabled, the textarea is read-only, and a spinner animation indicates active execution.
4. **Network Fallback:** If `POST /api/query` fails but `POST /api/intelligence/retrieve` succeeds (or vice-versa), `Promise.allSettled` ensures partial data is synthesized without crashing the application.
5. **Null Safety:** All 4D scores (specifically `freshness_score: number | null`) and optional fields are safely guarded with nullish coalescing.

---

## 13. TEST RESULTS

### A. Frontend Compilation & Linting
- **Command:** `npm run build` (`tsc -b && vite build`)
- **Result:** Code 0 (Success)
- **Transform:** 2,311 modules transformed in 9.87s
- **Output:** `dist/index.html` (1.14 kB), `dist/assets/index-*.css` (97.76 kB), `dist/assets/index-*.js` (747.47 kB)

### B. Live Browser Subagent Verification
- **Recording Artifact:** `query_workspace_flow_1793377974295.webp`
- **Scenarios Tested:**
  1. Empty input validation: Displayed validation warning.
  2. Scenario pill click: Correctly populated textarea.
  3. Execution: Successfully called backend in 218 ms.
  4. Execution Summary Bar: Verified 4/10 sources evaluated, 5 evidence passages retrieved, 3/5 calls consumed, lexical_only mode.
  5. Answer Workspace: Verified READY_TO_ANSWER verdict, confidence 85%, citation pills `[DOC-001]`, `[DOC-002]`.
  6. Evidence Explorer: Verified 4D scores, collapsible cards, Expand/Collapse All.
  7. Conflicts & Sufficiency Tab: Verified 97% sufficiency score, missing information checklist, and 0 contradiction state.
  8. Pipeline Trace Tab: Verified all 9 stages with timing and summaries.
  9. Query History: Verified immediate database persistence and entry in the sidebar.

### C. Backend Regression Suite
- **Command:** `python -m pytest tests/ -v`
- **Result:** **93 passed, 0 failed** in 5.97s (100% pass rate across Phase 1, Phase 2, Phase 3, and Step 4 tests).

---

## 14. RESPONSIVE UI VERIFICATION

- **Desktop (>1100px):** Two-column layout with center execution stream (Input -> Summary Bar -> Tabs -> Panels) and sticky right history sidebar (320px).
- **Tablet & Mobile (<=1100px):** Single-column stacked layout where the history sidebar moves below the main workspace.
- **Scrollbars & Overflow:** Custom subtle scrollbars prevent horizontal page stretching; long JSON technical traces are safely wrapped.

---

## 15. REMAINING LIMITATIONS & NEXT STEPS

1. **Google Gemini API Key:** External LLM generation requires adding a valid `GEMINI_API_KEY` to `backend/.env`. When provided, the backend can pass the pruned context into `google-genai` and flip Stage 9 to `Completed`.
2. **Semantic Embedding Provider:** Sentence Transformers embeddings are lazy-loaded and run offline in BM25 lexical mode when offline. Enabling PyTorch semantic vectors enhances directness and semantic similarity scores.
3. **Multi-Hop Query Deconstruction:** In future phases, sub-queries generated during complex multi-hop investigations can be visualized as branching sub-pipelines within `PipelineStageTracker`.
