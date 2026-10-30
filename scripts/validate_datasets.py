"""
EvidenRoute Dataset and Benchmark Validation Suite.

Validates:
1. JSON / JSONL structural integrity.
2. Required schema fields.
3. Uniqueness of record identifiers (no duplicate IDs).
4. Referential integrity: Verifies that benchmark expected_evidence_ids resolve to valid records.
5. Content non-emptiness.
6. Specified record counts (20 tickets, 15 conversations, >= 12 benchmark questions).
"""

import json
import os
import sys
from typing import Dict, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTHETIC_DIR = os.path.join(BASE_DIR, "data", "synthetic")
BENCHMARK_DIR = os.path.join(BASE_DIR, "data", "benchmarks")

TICKETS_FILE = os.path.join(SYNTHETIC_DIR, "sample_tickets.jsonl")
CONVERSATIONS_FILE = os.path.join(SYNTHETIC_DIR, "sample_conversations.jsonl")
BENCHMARKS_FILE = os.path.join(BENCHMARK_DIR, "benchmark_questions.jsonl")

# Built-in seed document IDs present in the EvidenRoute knowledge base
KNOWN_SEED_DOC_IDS = {
    "doc_policy_refund_v3",
    "doc_sla_agreement_2024",
    "doc_sla_agreement_2025_updated",
    "doc_feature_export_csv",
    "ticket_billing_9482",
    "slack_thread_billing_refunds",
    "ticket_sla_claim_1102",
    "slack_thread_export_deprecation",
}

REQUIRED_EVIDENCE_FIELDS = {"record_id", "source_id", "source_type", "title", "content", "authority_score"}
REQUIRED_BENCHMARK_FIELDS = {"benchmark_id", "question", "expected_decision", "test_category", "expected_evidence_ids", "expected_source_types"}


def validate_jsonl_file(file_path: str, required_fields: Set[str], id_field: str) -> Tuple[List[Dict], List[str]]:
    records = []
    errors = []

    if not os.path.exists(file_path):
        errors.append(f"File missing: {file_path}")
        return records, errors

    seen_ids = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
            except Exception as e:
                errors.append(f"Line {line_num}: Invalid JSON syntax ({e})")
                continue

            # Check required fields
            missing = required_fields - set(data.keys())
            if missing:
                errors.append(f"Line {line_num}: Missing required field(s): {missing}")

            # Check ID uniqueness
            rec_id = data.get(id_field)
            if not rec_id:
                errors.append(f"Line {line_num}: Missing '{id_field}'")
            elif rec_id in seen_ids:
                errors.append(f"Line {line_num}: Duplicate {id_field} detected: '{rec_id}'")
            else:
                seen_ids.add(rec_id)

            # Check non-empty content
            content = data.get("content") or data.get("question")
            if content is not None and not str(content).strip():
                errors.append(f"Line {line_num}: Empty text/content in record '{rec_id}'")

            records.append(data)

    return records, errors


def run_full_validation() -> bool:
    print("=" * 75)
    print("       EVIDENROUTE LOCAL DATASETS & BENCHMARK VALIDATION SUITE")
    print("=" * 75)

    all_passed = True
    total_errors: List[str] = []

    # 1. Validate Support Tickets
    print("\n[1/3] Validating Synthetic Support Tickets...")
    tickets, ticket_errors = validate_jsonl_file(TICKETS_FILE, REQUIRED_EVIDENCE_FIELDS, "record_id")
    print(f"      File: {TICKETS_FILE}")
    print(f"      Records loaded: {len(tickets)}")
    if len(tickets) != 20:
        ticket_errors.append(f"Target count is 20 tickets, found {len(tickets)}")
    if ticket_errors:
        all_passed = False
        total_errors.extend([f"[Tickets] {e}" for e in ticket_errors])
        print(f"      [FAILED] {len(ticket_errors)} validation error(s)")
    else:
        print("      [PASSED] 20 tickets verified, unique IDs, complete schemas.")

    # 2. Validate Support Conversations
    print("\n[2/3] Validating Synthetic Support Conversations...")
    convs, conv_errors = validate_jsonl_file(CONVERSATIONS_FILE, REQUIRED_EVIDENCE_FIELDS, "record_id")
    print(f"      File: {CONVERSATIONS_FILE}")
    print(f"      Records loaded: {len(convs)}")
    if len(convs) != 15:
        conv_errors.append(f"Target count is 15 conversations, found {len(convs)}")
    if conv_errors:
        all_passed = False
        total_errors.extend([f"[Conversations] {e}" for e in conv_errors])
        print(f"      [FAILED] {len(conv_errors)} validation error(s)")
    else:
        print("      [PASSED] 15 conversations verified, unique IDs, complete schemas.")

    # 3. Validate Benchmark Questions & Referential Integrity
    print("\n[3/3] Validating Benchmark Questions & Provenance References...")
    benchmarks, bm_errors = validate_jsonl_file(BENCHMARKS_FILE, REQUIRED_BENCHMARK_FIELDS, "benchmark_id")
    print(f"      File: {BENCHMARKS_FILE}")
    print(f"      Records loaded: {len(benchmarks)}")
    if len(benchmarks) < 12:
        bm_errors.append(f"Target count is at least 12 benchmark questions, found {len(benchmarks)}")

    # Build universe of all existing evidence IDs
    known_evidence_ids: Set[str] = set(KNOWN_SEED_DOC_IDS)
    for t in tickets:
        known_evidence_ids.add(t["record_id"])
    for c in convs:
        known_evidence_ids.add(c["record_id"])

    # Check referential integrity: Every expected_evidence_id must exist in known records
    dangling_refs = 0
    categories_found = set()
    for bm in benchmarks:
        categories_found.add(bm.get("test_category"))
        expected_ids = bm.get("expected_evidence_ids", [])
        for ref_id in expected_ids:
            if ref_id not in known_evidence_ids:
                bm_errors.append(
                    f"Benchmark '{bm.get('benchmark_id')}' references non-existent evidence_id: '{ref_id}'"
                )
                dangling_refs += 1

    expected_categories = {
        "source_selection",
        "evidence_relevance",
        "freshness",
        "contradiction_detection",
        "evidence_sufficiency",
        "abstention",
        "counterevidence_verification",
        "budget_exhaustion",
    }
    missing_cats = expected_categories - categories_found
    if missing_cats:
        bm_errors.append(f"Missing required benchmark test categories: {missing_cats}")

    if bm_errors:
        all_passed = False
        total_errors.extend([f"[Benchmarks] {e}" for e in bm_errors])
        print(f"      [FAILED] {len(bm_errors)} validation error(s)")
    else:
        print(f"      [PASSED] {len(benchmarks)} benchmark questions verified.")
        print(f"      [PASSED] All referenced evidence IDs verified against existing datasets.")
        print(f"      [PASSED] All {len(expected_categories)} core test categories represented.")

    print("\n" + "=" * 75)
    if all_passed:
        print("                 DATASET VALIDATION SUMMARY: ALL CHECKS PASSED!")
        print("=" * 75)
        print(f"  * Synthetic Tickets      : {len(tickets)} / 20")
        print(f"  * Synthetic Conversations: {len(convs)} / 15")
        print(f"  * Benchmark Questions    : {len(benchmarks)} (Target: >= 12)")
        print(f"  * Total Known Evidence   : {len(known_evidence_ids)} records")
        print("=" * 75)
        return True
    else:
        print(f"                 DATASET VALIDATION SUMMARY: {len(total_errors)} ERROR(S) FOUND")
        print("=" * 75)
        for err in total_errors:
            print(f"  - {err}")
        return False


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
