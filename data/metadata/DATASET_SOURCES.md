# EvidenRoute Dataset Sources & Provenance Metadata

This document provides official metadata, provenance, licensing, and schema mappings for all local datasets and benchmark suites used in the **EvidenRoute** project.

---

## 1. Summary of Datasets

| Dataset Name | Origin / Type | Local File Path | Records | License | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic Support Tickets** | Synthetic (Fictional) | `data/synthetic/sample_tickets.jsonl` | 20 | Apache 2.0 / MIT (Internal) | Verified |
| **Synthetic Support Conversations** | Synthetic (Fictional) | `data/synthetic/sample_conversations.jsonl` | 15 | Apache 2.0 / MIT (Internal) | Verified |
| **EvidenRoute Evaluation Benchmarks** | Synthetic Ground-Truth | `data/benchmarks/benchmark_questions.jsonl` | 14 | Apache 2.0 / MIT (Internal) | Verified |
| **HotpotQA Dev Distractor Set** | External (CMU / Stanford) | `data/raw/hotpot_dev_distractor_v1.json` | 7,405 (Raw) | CC BY-SA 4.0 | Download Script Ready |
| **HotpotQA Processed Evidence** | Processed Multi-Hop | `data/processed/hotpotqa_evidence.jsonl` | 100+ chunks | CC BY-SA 4.0 | Preprocessing Pipeline Ready |

---

## 2. Dataset Profiles & Licensing Details

### A. Synthetic Customer Support Tickets
- **Dataset Name:** EvidenRoute Synthetic Support Tickets
- **Local File Path:** `data/synthetic/sample_tickets.jsonl`
- **Creation Date:** October 2026
- **Source Type:** Synthetic customer service ticket resolutions.
- **Record Count:** 20 records
- **License:** Open Source (MIT / Apache 2.0)
- **Attribution:** Generated specifically for the EvidenRoute benchmark suite. Fictional names, company identifiers, and scenario details only.
- **Intended Usage:** 
  - Evaluating source selection for customer ticket repositories.
  - Testing policy exception detection (e.g. enterprise POC clauses vs. standard 14-day rules).
  - Testing status disagreement handling and edge case customer inquiries.

### B. Synthetic Internal Support Conversations
- **Dataset Name:** EvidenRoute Synthetic Team Conversations
- **Local File Path:** `data/synthetic/sample_conversations.jsonl`
- **Creation Date:** October 2026
- **Source Type:** Synthetic developer and operations Slack/chat threads.
- **Record Count:** 15 records
- **License:** Open Source (MIT / Apache 2.0)
- **Attribution:** Generated specifically for the EvidenRoute benchmark suite. Fictional usernames and channels.
- **Intended Usage:**
  - Testing low-to-medium authority conversational source evaluation.
  - Testing temporal policy updates (2024 SLA vs. 2025 SLA discussions).
  - Testing security announcements (release v2.4 CSV export deprecation).
  - Testing rumor debunking and counterevidence verification.

### C. EvidenRoute Benchmark Suite
- **Dataset Name:** EvidenRoute Evaluation Benchmark Questions
- **Local File Path:** `data/benchmarks/benchmark_questions.jsonl`
- **Creation Date:** October 2026
- **Record Count:** 14 test questions
- **License:** Open Source (MIT / Apache 2.0)
- **Schema Fields:**
  - `benchmark_id`: Unique identifier (e.g., `bm_001`)
  - `question`: Natural language test question
  - `expected_answer`: Ground truth reference answer (or `null` if expected to abstain)
  - `expected_evidence_ids`: Array of explicit record IDs required to justify the answer
  - `expected_source_types`: Categories of sources expected (document, ticket, conversation)
  - `expected_decision`: `ANSWER` or `ABSTAIN`
  - `test_category`: One of `source_selection`, `evidence_relevance`, `freshness`, `contradiction_detection`, `evidence_sufficiency`, `abstention`, `counterevidence_verification`, `budget_exhaustion`

### D. HotpotQA Development Distractor Dataset
- **Dataset Name:** HotpotQA (Development Distractor Set v1)
- **Original Source URL:** `https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json`
- **Target Local Path:** `data/raw/hotpot_dev_distractor_v1.json`
- **Original Authors:** Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen, Ruslan Salakhutdinov, Christopher D. Manning (EMNLP 2018).
- **Official Paper:** *"HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering"*
- **Official Website:** `https://hotpotqa.github.io/`
- **License:** **CC BY-SA 4.0** (Creative Commons Attribution-ShareAlike 4.0 International)
  - Original Wikipedia text fragments are distributed under CC BY-SA 3.0 / GFDL.
- **Intended Usage:** 
  - Cross-source multi-hop reasoning benchmarks.
  - Distractor paragraph identification and evidence relevance filtering.
- **Local Download Status:**
  - Automated downloader: `scripts/download_hotpotqa.py`
  - Preprocessing pipeline: `scripts/prepare_hotpotqa.py`
  - Manual download command:
    ```bash
    curl -o data/raw/hotpot_dev_distractor_v1.json https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json
    ```

---

## 3. Schema Compatibility with EvidenRoute Backend

All processed records map strictly to EvidenRoute's `NormalizedEvidence` contract without requiring any modifications to the backend Pydantic schemas or database models:

```
[Dataset Record]                          [EvidenRoute NormalizedEvidence]
----------------                          --------------------------------
record_id           ==================>   evidence_id
source_id           ==================>   source_id ("support_tickets", "slack_conversations", "hotpotqa_wikipedia")
source_type         ==================>   source_type (ticket, conversation, document)
title               ==================>   title
content             ==================>   content
uri                 ==================>   uri
created_at          ==================>   created_at
updated_at          ==================>   updated_at
author              ==================>   author
authority_score     ==================>   authority_score (0.0 to 1.0)
metadata            ==================>   metadata (JSON dict)
```

No backend models or APIs were altered.
