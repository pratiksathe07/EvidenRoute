# EvidenRoute

> **An Intelligent Context Selection & Evidence Evaluation Engine**  
> *Problem Statement 1 — Hackathon Project*

---

## 1. Problem Overview

Modern AI agents and RAG pipelines retrieve information from multiple heterogeneous sources before generating answers. However, they suffer from critical flaws:
- **Indiscriminate Retrieval:** Querying every available source instead of selecting the most useful ones, wasting token budgets and API calls.
- **Weak or Outdated Evidence:** Generating confident answers based on stale documentation or unverified rumors.
- **Unnoticed Contradictions:** Failing to recognize when multiple sources disagree on values, policies, or operational statuses.
- **Hallucination over Abstention:** Inventing answers when evidence is insufficient rather than transparently acknowledging uncertainty.

---

## 2. Our Solution — EvidenRoute

**EvidenRoute** is an intelligent decision-making layer between an AI agent and its available knowledge sources.

```
USER QUESTION
     ↓
1. QUERY UNDERSTANDING       (Extracts topic, intent, keywords, temporal cues)
     ↓
2. SOURCE SELECTION          (Ranks & selects relevant sources; rejects mismatched ones)
     ↓
3. BUDGET ALLOCATION         (Enforces call, candidate, and token limits via BudgetManager)
     ↓
4. BOUNDED RETRIEVAL         (Executes targeted searches through normalized adapters)
     ↓
5. EVIDENCE EVALUATION       (Multi-dimensional scoring: Relevance, Authority, Freshness, Directness)
     ↓
6. CONTRADICTION DETECTION   (Detects factual vs. temporal updates vs. scope exceptions)
     ↓
7. EVIDENCE SUFFICIENCY GATE (Validates whether evidence meets confidence thresholds)
     ↓
8. EVIDENCE STRESS TEST      (Bounded counterevidence search using remaining budget)
     ↓
FINAL DECISION               (ANSWER with citations OR honest ABSTAIN)
```

---

## 3. Key Differentiating Feature: Evidence Stress Test

Before returning a final answer, EvidenRoute can perform a bounded, proactive verification process:
- Tests tentative conclusions against adversarial or qualifying counter-queries (e.g., checking for policy exceptions, recent deprecation notices, or caveats).
- **Strictly constrained by the remaining retrieval budget**—never exceeds configured call or token ceilings.
- Updates decision confidence and annotates answers with discovered caveats.
- If evidence becomes contradictory or insufficient, the engine cleanly **abstains** rather than guessing.

---

## 4. Technology Stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite
- **Architecture:** Thread-safe central Budget Manager, standardized Source Adapters, modular pipeline services
- **Evaluation & Benchmarks:** 14 ground-truth test scenarios, 20 synthetic customer tickets, 15 synthetic team conversations, and HotpotQA integration pipelines.

---

## 5. Repository Structure

```
EvidenRoute/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint
│   │   ├── api/
│   │   │   ├── sources.py           # Source registration & batch ingestion routes
│   │   │   └── query.py             # Query execution, trace & audit history routes
│   │   ├── database/
│   │   │   ├── db.py                # Database connection & session factory
│   │   │   └── models.py            # SQLAlchemy models (sources, records, runs, logs)
│   │   ├── schemas/
│   │   │   ├── evidence.py          # Normalized evidence contracts & scoring models
│   │   │   ├── budget.py            # Budget configuration & status contracts
│   │   │   ├── source.py            # Source metadata & selection decision schemas
│   │   │   └── query.py             # Query request, response & trace step schemas
│   │   ├── adapters/
│   │   │   ├── base.py              # Abstract BaseSourceAdapter
│   │   │   └── sqlite_source.py     # SQLite lexical keyword adapter
│   │   └── services/
│   │       ├── budget_manager.py    # Central thread-safe budget controller
│   │       ├── query_understanding.py # Intent & entity extractor
│   │       ├── source_selector.py   # Heuristic source ranking engine
│   │       ├── evidence_evaluator.py # 4D evidence scoring service
│   │       ├── contradiction_detector.py # Conflict & temporal update detector
│   │       ├── stress_test.py       # Bounded counterevidence verification engine
│   │       └── query_orchestrator.py # End-to-end pipeline coordinator
│   ├── tests/
│   │   ├── test_contracts.py        # Schema validation tests
│   │   ├── test_budget_manager.py   # Quota enforcement unit tests
│   │   ├── test_api_sources.py      # Source & ingestion integration tests
│   │   └── test_intelligence.py     # End-to-end intelligence & stress test suite
│   ├── demo_cli.py                  # Interactive CLI demonstration runner
│   └── requirements.txt
├── data/
│   ├── synthetic/
│   │   ├── sample_tickets.jsonl     # 20 synthetic customer tickets
│   │   └── sample_conversations.jsonl # 15 synthetic team conversations
│   ├── benchmarks/
│   │   └── benchmark_questions.jsonl# 14 ground-truth benchmark questions
│   ├── raw/                         # Raw external benchmark datasets
│   ├── processed/                   # Normalized evidence chunks
│   ├── metadata/
│   │   └── DATASET_SOURCES.md       # Dataset documentation, provenance & licensing
│   └── evidenroute_combined_dataset.json # All-in-one consolidated JSON bundle
├── scripts/
│   ├── validate_datasets.py         # Automated dataset validation suite
│   ├── download_hotpotqa.py         # HotpotQA dataset downloader
│   ├── prepare_hotpotqa.py          # HotpotQA multi-hop preprocessor
│   └── import_datasets.py           # Safe, optional backend ingestion utility
├── docs/
│   └── architecture_and_contracts.md# Complete architectural specification
├── .gitignore
└── README.md
```

---

## 6. Getting Started

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/pratiksathe07/EvidenRoute.git
cd EvidenRoute

# Install dependencies
pip install -r backend/requirements.txt
```

---

## 7. Running the Application

### Option A: Start the FastAPI Server & Interactive API Docs
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger API: **http://127.0.0.1:8000/docs**
- Health Check: **http://127.0.0.1:8000/api/health**
- Source Catalog: **http://127.0.0.1:8000/api/sources**

### Option B: Run the Interactive Demo CLI
Runs 4 representative scenarios demonstrating verified answers, SLA temporal update resolution, Evidence Stress Testing, and honest abstention:
```bash
python -m backend.demo_cli
```

---

## 8. Testing & Validation

### Run Automated Backend Unit & Integration Tests (17 Tests)
```bash
python -m pytest backend/tests -v
```

### Validate Datasets & Referential Integrity
```bash
python scripts/validate_datasets.py
```

---

## 9. License

This project is licensed under the MIT License - see the LICENSE file for details.
External datasets such as HotpotQA are governed by their respective licenses (e.g. CC BY-SA 4.0).
