"""
EvidenRoute - Interactive CLI Demonstration Script
Run this script to test the backend engine across representative scenarios:
1. Clear Answerable Query (Refund Policy)
2. Temporal Contradiction Resolution (SLA Revision)
3. Abstention on Insufficient Evidence (Unknown Domain)
4. Evidence Stress Test (Adversarial Caveat Detection)
"""

import sys
from backend.app.api.sources import seed_sources_and_records
from backend.app.database.db import SessionLocal, init_db
from backend.app.schemas.budget import BudgetConfig
from backend.app.schemas.query import QueryRequest
from backend.app.services.query_orchestrator import QueryOrchestrator


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def run_test_scenario(orchestrator: QueryOrchestrator, question: str, enable_stress_test: bool = True):
    print(f"\n>> USER QUESTION: '{question}'")
    print(f">> STRESS TEST ENABLED: {enable_stress_test}")

    req = QueryRequest(
        question=question,
        budget=BudgetConfig(max_source_calls=5, max_candidates=10, max_tokens=2500),
        enable_stress_test=enable_stress_test,
    )

    response = orchestrator.execute(req)

    print("\n[PIPELINE EXECUTION TRACE]")
    for i, step in enumerate(response.execution_trace, 1):
        print(f"  {i}. {step.step_name} ({step.duration_ms}ms) -> {step.summary}")

    print("\n[BUDGET CONSUMPTION AUDIT]")
    b = response.budget_status
    print(f"  * Source Calls: {b.consumed.calls_consumed} / {b.configured.max_source_calls} (Remaining: {b.remaining_calls})")
    print(f"  * Candidate Chunks: {b.consumed.candidates_consumed} / {b.configured.max_candidates} (Remaining: {b.remaining_candidates})")
    print(f"  * Tokens: {b.consumed.tokens_consumed} / {b.configured.max_tokens} (Remaining: {b.remaining_tokens})")

    if response.contradictions:
        print("\n[CONTRADICTIONS DETECTED]")
        for c in response.contradictions:
            print(f"  * [{c.contradiction_type.value}] {c.description} -> Resolution: {c.resolution_status}")

    if response.stress_test.executed:
        print("\n[EVIDENCE STRESS TEST (DIFFERENTIATOR)]")
        print(f"  * Hypothesis Tested: {response.stress_test.hypothesis_tested}")
        print(f"  * Verification Query: '{response.stress_test.verification_query}'")
        print(f"  * Counterevidence Found: {response.stress_test.counterevidence_found}")
        print(f"  * Impact: {response.stress_test.impact_on_decision}")
        print(f"  * Summary: {response.stress_test.summary}")

    print(f"\n[FINAL DECISION]: {response.outcome.value}")
    if response.outcome.value == "ANSWER":
        print(f"Citations: {response.citations}")
        print("Answer:\n" + response.final_answer)
    else:
        print("Reason for Abstention:\n" + str(response.abstention_reason))


def main():
    print_banner("EvidenRoute - Initializing Engine & Database")
    init_db()
    with SessionLocal() as db:
        seed_sources_and_records(db)
        orchestrator = QueryOrchestrator(db)

        # Scenario 1: Standard Policy Query
        print_banner("Scenario 1: Verified Answer with Citations")
        run_test_scenario(
            orchestrator,
            question="What is the refund policy duration?",
            enable_stress_test=False,
        )

        # Scenario 2: Temporal Policy Contradiction
        print_banner("Scenario 2: Temporal Conflict Resolution (2024 vs 2025 SLA)")
        run_test_scenario(
            orchestrator,
            question="What is the outage credit percentage under the SLA?",
            enable_stress_test=False,
        )

        # Scenario 3: Bounded Evidence Stress Test
        print_banner("Scenario 3: Stress Test Caveat Detection")
        run_test_scenario(
            orchestrator,
            question="Can customers get a refund for software license?",
            enable_stress_test=True,
        )

        # Scenario 4: Clean Abstention
        print_banner("Scenario 4: Honest Abstention on Insufficient Evidence")
        run_test_scenario(
            orchestrator,
            question="How do quantum hyperdrive generators calibrate on Mars?",
            enable_stress_test=False,
        )

    print("\n" + "=" * 70)
    print("  ALL DEMO SCENARIOS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
