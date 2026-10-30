from typing import List, Tuple
from backend.app.adapters.base import BaseSourceAdapter
from backend.app.schemas.evidence import NormalizedEvidence
from backend.app.schemas.query import StressTestResult
from backend.app.services.budget_manager import BudgetManager
from backend.app.services.query_understanding import QueryProfile


class StressTestService:
    """
    Bounded counterevidence search engine.
    Proactively checks for challenges or edge cases using strictly remaining budget.
    """

    @classmethod
    def execute_stress_test(
        cls,
        tentative_answer: str,
        profile: QueryProfile,
        initial_evidence: List[NormalizedEvidence],
        available_adapters: List[BaseSourceAdapter],
        budget_manager: BudgetManager,
    ) -> Tuple[StressTestResult, List[NormalizedEvidence]]:
        # 1. Budget check: Must have at least 1 call and 2 candidate tokens
        if not budget_manager.can_allocate(calls=1, candidates=2, tokens=100):
            return (
                StressTestResult(
                    executed=False,
                    summary="Stress test skipped: Insufficient remaining retrieval budget.",
                ),
                [],
            )

        # 2. Formulate targeted adversarial / challenge search query
        challenge_terms = ["exception", "deprecated", "revision", "dispute", "update", "conflict", "limitation"]
        key_subject = profile.clean_keywords[0] if profile.clean_keywords else "policy"
        verification_query = f"{key_subject} {' '.join(challenge_terms[:3])}"

        # 3. Reserve 1 call from central budget
        reserved = budget_manager.reserve(calls=1, candidates=3, tokens=300)
        if not reserved:
            return (
                StressTestResult(
                    executed=False,
                    summary="Stress test skipped: Budget reservation failed.",
                ),
                [],
            )

        challenge_evidence: List[NormalizedEvidence] = []
        try:
            # Query the most relevant available adapter that has not been over-polled
            for adapter in available_adapters:
                results = adapter.search(verification_query, limit=3)
                for r in results:
                    # Filter out exact duplicate evidence already present in initial_evidence
                    if not any(e.evidence_id == r.evidence_id for e in initial_evidence):
                        challenge_evidence.append(r)
                if challenge_evidence:
                    break

            # Calculate actual tokens
            actual_cands = len(challenge_evidence)
            total_text = " ".join(e.content for e in challenge_evidence)
            actual_tokens = BudgetManager.estimate_tokens(total_text)

            # Commit actual consumption
            budget_manager.commit(
                reserved_calls=1,
                reserved_candidates=3,
                reserved_tokens=300,
                actual_calls=1,
                actual_candidates=actual_cands,
                actual_tokens=actual_tokens,
            )

        except Exception as e:
            budget_manager.release(calls=1, candidates=3, tokens=300)
            return (
                StressTestResult(
                    executed=False,
                    summary=f"Stress test aborted due to adapter retrieval error: {str(e)}",
                ),
                [],
            )

        if not challenge_evidence:
            return (
                StressTestResult(
                    executed=True,
                    hypothesis_tested="Tested for counterevidence or restrictive policy clauses.",
                    verification_query=verification_query,
                    counterevidence_found=False,
                    supporting_evidence_found=False,
                    evidence_examined_count=0,
                    budget_used_calls=1,
                    impact_on_decision="confirmed_answer",
                    summary="Stress test completed. No counterevidence or contradictory clauses were discovered.",
                ),
                [],
            )

        # 4. Evaluate whether challenge chunks contradict the tentative answer
        counter_cues = ["deprecated", "removed", "exception", "enterprise only", "not eligible", "discontinued", "exceeds"]
        found_counter = False
        counter_notes = []

        for ev in challenge_evidence:
            content_lower = ev.content.lower()
            if any(cue in content_lower for cue in counter_cues):
                found_counter = True
                counter_notes.append(f"[{ev.evidence_id}]: {ev.title} highlights caveats/exceptions.")

        if found_counter:
            impact = "weakened_confidence"
            summary = (
                f"Stress test surfaced qualifying caveats/exceptions ({len(challenge_evidence)} item(s) checked): "
                + " ".join(counter_notes)
            )
        else:
            impact = "confirmed_answer"
            summary = (
                f"Stress test retrieved {len(challenge_evidence)} related item(s), confirming the initial conclusion without counterevidence."
            )

        return (
            StressTestResult(
                executed=True,
                hypothesis_tested="Testing for edge cases, exceptions, and superseding policy clauses.",
                verification_query=verification_query,
                counterevidence_found=found_counter,
                supporting_evidence_found=not found_counter,
                evidence_examined_count=len(challenge_evidence),
                budget_used_calls=1,
                impact_on_decision=impact,
                summary=summary,
            ),
            challenge_evidence,
        )
