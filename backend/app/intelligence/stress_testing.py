"""
EvidenRoute - Evidence Stress-Testing Framework
Comprehensive test framework evaluating all 14 difficult evidence scenarios
and adversarial boundary conditions.

Evaluated Scenarios:
1. Strong supporting evidence from multiple sources.
2. High relevance but low-authority evidence.
3. Old evidence versus recent evidence (temporal supersedence).
4. Contradictory statements across documents and conversations.
5. Contradictory ticket resolutions.
6. Multiple sources/passages repeating the same information (no false consensus).
7. Insufficient evidence for a query.
8. Missing timestamps and metadata.
9. Unrelated sources (budget preservation).
10. Exact technical identifier queries.
11. Ambiguous queries requiring clarification.
12. No available evidence (honest abstention).
13. Conflicting evidence with different authority levels.
14. Evidence that appears relevant but does not directly answer the question.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from .conflict_detector import ConflictDetector
from .counter_evidence import CounterEvidenceService
from .evidence_scorer import EvidenceScorer
from .models import (
    ConflictSeverity,
    ConflictType,
    EvidencePassage,
    EvidenceReliabilityStatus,
    EvidenceScore,
    QueryAnalysisResult,
    IntentType,
    RecommendedAction,
    StressTestScenarioResult,
    StressTestSuiteReport,
)
from .reliability_evaluator import EvidenceReliabilityEvaluator
from .retrieval_pipeline import RetrievalPipeline
from .source_registry import SourceRegistry
from .storage import ChunkStore
from .sufficiency_evaluator import SufficiencyEvaluator


class StressTestingFramework:
    """
    Executes and scores the 14 EvidenRoute evidence stress-testing scenarios.
    """

    def __init__(
        self,
        retrieval_pipeline: Optional[RetrievalPipeline] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        sufficiency_evaluator: Optional[SufficiencyEvaluator] = None,
        reliability_evaluator: Optional[EvidenceReliabilityEvaluator] = None,
        counter_evidence_service: Optional[CounterEvidenceService] = None,
    ):
        self.pipeline = retrieval_pipeline or RetrievalPipeline()
        if len(self.pipeline.chunk_store.get_all_chunks()) == 0:
            from .ingestion import IngestionService
            IngestionService(chunk_store=self.pipeline.chunk_store).run_ingestion(clear_existing=False)
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.sufficiency_evaluator = sufficiency_evaluator or SufficiencyEvaluator()
        self.reliability_evaluator = reliability_evaluator or EvidenceReliabilityEvaluator()
        self.counter_service = counter_evidence_service or CounterEvidenceService()

    def run_all_scenarios(self) -> StressTestSuiteReport:
        """
        Runs all 14 scenarios sequentially and returns a comprehensive report.
        """
        t0 = time.perf_counter()
        results: List[StressTestScenarioResult] = []

        scenario_runners = [
            self.test_scenario_1_strong_multi_source,
            self.test_scenario_2_high_relevance_low_authority,
            self.test_scenario_3_old_vs_recent_evidence,
            self.test_scenario_4_doc_vs_conv_contradiction,
            self.test_scenario_5_contradictory_ticket_resolutions,
            self.test_scenario_6_repeated_information_no_false_consensus,
            self.test_scenario_7_insufficient_evidence,
            self.test_scenario_8_missing_timestamps_and_metadata,
            self.test_scenario_9_unrelated_sources_budget_preservation,
            self.test_scenario_10_exact_technical_identifier,
            self.test_scenario_11_ambiguous_query_clarification,
            self.test_scenario_12_no_available_evidence_abstention,
            self.test_scenario_13_conflicting_authority_resolution,
            self.test_scenario_14_relevant_but_indirect_evidence,
        ]

        passed_count = 0
        for runner in scenario_runners:
            res = runner()
            if res.passed:
                passed_count += 1
            results.append(res)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return StressTestSuiteReport(
            total_scenarios=len(results),
            passed_scenarios=passed_count,
            failed_scenarios=len(results) - passed_count,
            pass_rate_pct=round((passed_count / len(results)) * 100.0, 2),
            results=results,
            execution_time_ms=round(elapsed_ms, 2),
        )

    # -------------------------------------------------------------
    # Scenario 1: Strong Supporting Evidence from Multiple Sources
    # -------------------------------------------------------------
    def test_scenario_1_strong_multi_source(self) -> StressTestScenarioResult:
        query = "Why did the payment API fail after deployment?"
        trace = self.pipeline.run(query, enable_stress_test=True)

        has_multi_sources = (
            trace.evidence_reliability is not None
            and trace.evidence_reliability.independent_sources_count >= 2
        )
        is_ready = trace.answer_readiness.is_ready_to_answer

        passed = is_ready and has_multi_sources
        return StressTestScenarioResult(
            scenario_id=1,
            scenario_name="Strong supporting evidence from multiple sources",
            query=query,
            expected_behavior="Identifies independent sources, verifies corroboration, clears for answer.",
            actual_verdict=trace.answer_readiness.readiness_verdict,
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status=trace.evidence_reliability.status if trace.evidence_reliability else "unknown",
            conflicts_detected=len(trace.conflicts),
            counter_evidence_found=trace.counter_evidence.counter_evidence_found if trace.counter_evidence else False,
            passed=passed,
            details={
                "independent_sources_count": trace.evidence_reliability.independent_sources_count if trace.evidence_reliability else 0,
                "confidence_score": trace.answer_readiness.confidence_score,
            },
        )

    # -------------------------------------------------------------
    # Scenario 2: High Relevance but Low-Authority Evidence
    # -------------------------------------------------------------
    def test_scenario_2_high_relevance_low_authority(self) -> StressTestScenarioResult:
        # Synthetic fixture: Passage with high lexical match but low authority (0.40)
        p_low_auth = self._make_dummy_passage(
            chunk_id="chk-sc2-low-auth",
            source_id="conv-random-chat",
            source_name="Random Informal Chat",
            content="To fix error 504 you can just bypass authentication completely.",
            authority_level=0.40,
            relevance=0.95,
        )
        analysis = self._make_dummy_analysis(
            intent=IntentType.TECHNICAL_TROUBLESHOOTING.value,
            keywords=["error", "504", "bypass"],
        )
        rel = self.reliability_evaluator.evaluate_reliability("How to fix error 504?", analysis, [p_low_auth])

        passed = rel.status in [EvidenceReliabilityStatus.MODERATE.value, EvidenceReliabilityStatus.UNRELIABLE.value]
        passed = passed and any("Low average authority" in lim for lim in rel.confidence_limitations)

        return StressTestScenarioResult(
            scenario_id=2,
            scenario_name="High relevance but low-authority evidence",
            query="How to fix error 504?",
            expected_behavior="Penalizes low authority and notes credibility limitations in trace.",
            actual_verdict=rel.status,
            decision_outcome=rel.recommended_action,
            reliability_status=rel.status,
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"reliability_score": rel.reliability_score, "limitations": rel.confidence_limitations},
        )

    # -------------------------------------------------------------
    # Scenario 3: Old Evidence vs Recent Evidence (Temporal Supersedence)
    # -------------------------------------------------------------
    def test_scenario_3_old_vs_recent_evidence(self) -> StressTestScenarioResult:
        p_old = self._make_dummy_passage(
            chunk_id="chk-sc3-old",
            source_id="doc-sla-2024",
            source_name="2024 SLA Policy",
            content="The standard SLA refund credit is 10% under policy 2024.",
            created_at="2024-01-01T00:00:00Z",
            authority_level=0.90,
        )
        p_new = self._make_dummy_passage(
            chunk_id="chk-sc3-new",
            source_id="doc-sla-2025",
            source_name="2025 SLA Policy",
            content="The standard SLA refund credit is 15% under policy 2025.",
            created_at="2025-06-01T00:00:00Z",
            authority_level=0.90,
        )
        conflict_res = self.conflict_detector.detect_conflicts([p_old, p_new])

        is_temporal = any(c.conflict_type == ConflictType.TEMPORAL_SUPERSEDENCE.value for c in conflict_res.conflicts)
        passed = is_temporal and conflict_res.direct_contradictions_count == 0

        return StressTestScenarioResult(
            scenario_id=3,
            scenario_name="Old evidence versus recent evidence",
            query="What is the SLA outage credit?",
            expected_behavior="Classifies discrepancy as temporal supersedence rather than direct contradiction.",
            actual_verdict="TEMPORAL_SUPERSEDENCE_DETECTED" if is_temporal else "NOT_DETECTED",
            decision_outcome=RecommendedAction.ANSWER.value,
            reliability_status=EvidenceReliabilityStatus.HIGH.value,
            conflicts_detected=conflict_res.conflicts_detected_count,
            counter_evidence_found=False,
            passed=passed,
            details={"conflicts": [c.model_dump() for c in conflict_res.conflicts]},
        )

    # -------------------------------------------------------------
    # Scenario 4: Contradictory Statements Across Documents and Conversations
    # -------------------------------------------------------------
    def test_scenario_4_doc_vs_conv_contradiction(self) -> StressTestScenarioResult:
        p_doc = self._make_dummy_passage(
            chunk_id="chk-sc4-doc",
            source_id="doc-refund-policy",
            source_name="Official Refund Policy",
            content="The refund window is strictly 14 days from date of purchase.",
            authority_level=0.95,
        )
        p_chat = self._make_dummy_passage(
            chunk_id="chk-sc4-chat",
            source_id="conv-support-chat",
            source_name="Support Team Slack",
            content="The refund window is strictly 30 days from date of purchase.",
            authority_level=0.60,
        )
        conflict_res = self.conflict_detector.detect_conflicts([p_doc, p_chat])
        analysis = self._make_dummy_analysis(keywords=["refund", "window", "days"])
        suff = self.sufficiency_evaluator.evaluate_sufficiency("What is the refund window?", analysis, [p_doc, p_chat], conflict_res.conflicts)

        passed = conflict_res.direct_contradictions_count == 1 and suff.recommended_action == RecommendedAction.CLARIFY.value

        return StressTestScenarioResult(
            scenario_id=4,
            scenario_name="Contradictory statements across documents and conversations",
            query="What is the refund window?",
            expected_behavior="Detects direct contradiction between documentation and chat, requesting clarification.",
            actual_verdict=suff.sufficiency_status,
            decision_outcome=suff.recommended_action,
            reliability_status=EvidenceReliabilityStatus.CONTRADICTED.value,
            conflicts_detected=conflict_res.conflicts_detected_count,
            counter_evidence_found=True,
            passed=passed,
            details={"direct_contradictions": conflict_res.direct_contradictions_count},
        )

    # -------------------------------------------------------------
    # Scenario 5: Contradictory Ticket Resolutions
    # -------------------------------------------------------------
    def test_scenario_5_contradictory_ticket_resolutions(self) -> StressTestScenarioResult:
        t1 = self._make_dummy_passage(
            chunk_id="chk-sc5-t1",
            source_id="tkt-jira-bugs",
            source_name="Jira Bugs",
            content="Resolution: Set database pool size to 50 connections permanently.",
            authority_level=0.80,
        )
        t2 = self._make_dummy_passage(
            chunk_id="chk-sc5-t2",
            source_id="tkt-jira-bugs",
            source_name="Jira Bugs",
            content="Resolution: Set database pool size to 5 connections permanently.",
            authority_level=0.80,
        )
        conflict_res = self.conflict_detector.detect_conflicts([t1, t2])
        passed = conflict_res.direct_contradictions_count >= 1

        return StressTestScenarioResult(
            scenario_id=5,
            scenario_name="Contradictory ticket resolutions",
            query="What is the permanent database pool size?",
            expected_behavior="Detects factual contradiction between competing ticket resolutions.",
            actual_verdict="DIRECT_CONTRADICTION" if passed else "MISSED",
            decision_outcome=RecommendedAction.CLARIFY.value,
            reliability_status=EvidenceReliabilityStatus.CONTRADICTED.value,
            conflicts_detected=conflict_res.conflicts_detected_count,
            counter_evidence_found=True,
            passed=passed,
            details={"conflicts_detected": conflict_res.conflicts_detected_count},
        )

    # -------------------------------------------------------------
    # Scenario 6: Multiple Sources Repeating Same Info (No False Consensus)
    # -------------------------------------------------------------
    def test_scenario_6_repeated_information_no_false_consensus(self) -> StressTestScenarioResult:
        # Three passages from the exact same source_id: should NOT count as 3 independent sources
        p1 = self._make_dummy_passage(chunk_id="chk-sc6-1", source_id="doc-api-gateway", content="DB connection pool is 50.", authority_level=0.90)
        p2 = self._make_dummy_passage(chunk_id="chk-sc6-2", source_id="doc-api-gateway", content="DB connection pool is 50.", authority_level=0.90)
        p3 = self._make_dummy_passage(chunk_id="chk-sc6-3", source_id="doc-api-gateway", content="DB connection pool is 50.", authority_level=0.90)

        analysis = self._make_dummy_analysis(keywords=["DB", "pool"])
        rel = self.reliability_evaluator.evaluate_reliability("What is pool size?", analysis, [p1, p2, p3])

        # Independent sources count must be exactly 1
        passed = rel.independent_sources_count == 1
        passed = passed and any("single source" in lim for lim in rel.confidence_limitations)

        return StressTestScenarioResult(
            scenario_id=6,
            scenario_name="Multiple sources repeating the same information",
            query="What is pool size?",
            expected_behavior="Groups by source_id to prevent duplicate chunks from inflating independent confirmation.",
            actual_verdict=f"INDEPENDENT_SOURCES_{rel.independent_sources_count}",
            decision_outcome=rel.recommended_action,
            reliability_status=rel.status,
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"independent_sources_count": rel.independent_sources_count, "limitations": rel.confidence_limitations},
        )

    # -------------------------------------------------------------
    # Scenario 7: Insufficient Evidence for a Query
    # -------------------------------------------------------------
    def test_scenario_7_insufficient_evidence(self) -> StressTestScenarioResult:
        query = "What are the configuration parameters for quantum key distribution in EvidenRoute?"
        trace = self.pipeline.run(query)

        # Expected: Either no sources selected, or sufficiency indicates insufficient evidence
        is_abstain = trace.answer_readiness.recommended_action in [RecommendedAction.ABSTAIN.value, RecommendedAction.RETRIEVE_MORE.value]
        is_not_ready = not trace.answer_readiness.is_ready_to_answer

        passed = is_abstain and is_not_ready
        return StressTestScenarioResult(
            scenario_id=7,
            scenario_name="Insufficient evidence for a query",
            query=query,
            expected_behavior="Abstains or halts rather than producing an unjustified answer.",
            actual_verdict=trace.answer_readiness.readiness_verdict,
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status=trace.evidence_reliability.status if trace.evidence_reliability else "insufficient",
            conflicts_detected=len(trace.conflicts),
            counter_evidence_found=False,
            passed=passed,
            details={"is_ready_to_answer": trace.answer_readiness.is_ready_to_answer},
        )

    # -------------------------------------------------------------
    # Scenario 8: Missing Timestamps and Metadata
    # -------------------------------------------------------------
    def test_scenario_8_missing_timestamps_and_metadata(self) -> StressTestScenarioResult:
        p = self._make_dummy_passage(
            chunk_id="chk-sc8-nodate",
            source_id="doc-legacy",
            source_name="Legacy Documentation",
            content="Standard API rate limits are 100 requests per second.",
            created_at=None,
            authority_level=0.80,
        )
        scorer = EvidenceScorer()
        analysis = self._make_dummy_analysis(keywords=["API", "rate", "limit"])
        ev_score = scorer.score_evidence(
            chunk=self._passage_to_chunk(p),
            retrieval_score=0.85,
            query_analysis=analysis,
        )

        # Proportional weight normalization must keep score normalized
        passed = 0.0 <= ev_score.final_evidence_score <= 1.0
        passed = passed and ev_score.freshness_status == "unknown"

        return StressTestScenarioResult(
            scenario_id=8,
            scenario_name="Missing timestamps and metadata",
            query="What are API rate limits?",
            expected_behavior="Applies proportional weight redistribution without failing.",
            actual_verdict=f"FINAL_SCORE_{ev_score.final_evidence_score:.2f}",
            decision_outcome="normalized",
            reliability_status="unknown_freshness",
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"score": ev_score.model_dump()},
        )

    # -------------------------------------------------------------
    # Scenario 9: Unrelated Sources (Budget Preservation)
    # -------------------------------------------------------------
    def test_scenario_9_unrelated_sources_budget_preservation(self) -> StressTestScenarioResult:
        query = "How do quantum hyperspace engines calibrate on Mars?"
        trace = self.pipeline.run(query)

        passed = (
            len(trace.selected_source_ids) == 0
            and trace.budget_info.get("status") == "budget_preserved"
            and trace.answer_readiness.is_ready_to_answer is False
        )
        return StressTestScenarioResult(
            scenario_id=9,
            scenario_name="Unrelated sources",
            query=query,
            expected_behavior="Selects zero sources, skips retrieval entirely, preserves 100% of budget.",
            actual_verdict=trace.budget_info.get("status", "unknown"),
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status=trace.evidence_reliability.status if trace.evidence_reliability else "insufficient",
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"selected_sources": trace.selected_source_ids, "budget_info": trace.budget_info},
        )

    # -------------------------------------------------------------
    # Scenario 10: Exact Technical Identifier Queries
    # -------------------------------------------------------------
    def test_scenario_10_exact_technical_identifier(self) -> StressTestScenarioResult:
        query = "What occurred in release-2026.10-rc2 deployment with 504 gateway timeout?"
        trace = self.pipeline.run(query, enable_stress_test=True)

        # High BM25 and exact match
        found_target_chunk = any(
            "release-2026.10-rc2" in p.content or "504" in p.content
            for p in trace.retrieved_evidence
        )
        passed = found_target_chunk and trace.answer_readiness.is_ready_to_answer

        return StressTestScenarioResult(
            scenario_id=10,
            scenario_name="Exact technical identifier queries",
            query=query,
            expected_behavior="Boosts exact technical token match and pinpoints target postmortem/spec.",
            actual_verdict="TARGET_CHUNK_RETRIEVED" if found_target_chunk else "TARGET_MISSED",
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status=trace.evidence_reliability.status if trace.evidence_reliability else "high",
            conflicts_detected=len(trace.conflicts),
            counter_evidence_found=trace.counter_evidence.counter_evidence_found if trace.counter_evidence else False,
            passed=passed,
            details={"retrieved_evidence_count": len(trace.retrieved_evidence)},
        )

    # -------------------------------------------------------------
    # Scenario 11: Ambiguous Queries Requiring Clarification
    # -------------------------------------------------------------
    def test_scenario_11_ambiguous_query_clarification(self) -> StressTestScenarioResult:
        query = "policy"
        trace = self.pipeline.run(query)

        is_unclear_or_retrieve = trace.analysis.intent == IntentType.UNCLEAR_QUERY.value or trace.answer_readiness.recommended_action in [
            RecommendedAction.CLARIFY.value,
            RecommendedAction.RETRIEVE_MORE.value,
            RecommendedAction.ABSTAIN.value,
        ]
        passed = is_unclear_or_retrieve and not trace.answer_readiness.is_ready_to_answer

        return StressTestScenarioResult(
            scenario_id=11,
            scenario_name="Ambiguous queries requiring clarification",
            query=query,
            expected_behavior="Flags ambiguous one-word queries as unclear, withholding ready-to-answer.",
            actual_verdict=trace.analysis.intent,
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status=trace.evidence_reliability.status if trace.evidence_reliability else "insufficient",
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"intent": trace.analysis.intent, "action": trace.answer_readiness.recommended_action},
        )

    # -------------------------------------------------------------
    # Scenario 12: No Available Evidence (Honest Abstention)
    # -------------------------------------------------------------
    def test_scenario_12_no_available_evidence_abstention(self) -> StressTestScenarioResult:
        query = "XYZ9999NONEXISTENT_KEYWORD_NOT_FOUND_IN_DATA"
        trace = self.pipeline.run(query)

        passed = (
            len(trace.retrieved_evidence) == 0
            and trace.answer_readiness.is_ready_to_answer is False
            and trace.answer_readiness.recommended_action in [RecommendedAction.ABSTAIN.value, RecommendedAction.RETRIEVE_MORE.value]
        )
        return StressTestScenarioResult(
            scenario_id=12,
            scenario_name="No available evidence",
            query=query,
            expected_behavior="Honest abstention when zero candidate chunks match the query.",
            actual_verdict=trace.answer_readiness.readiness_verdict,
            decision_outcome=trace.answer_readiness.recommended_action,
            reliability_status="insufficient",
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"retrieved_evidence_count": len(trace.retrieved_evidence)},
        )

    # -------------------------------------------------------------
    # Scenario 13: Conflicting Evidence with Different Authority Levels
    # -------------------------------------------------------------
    def test_scenario_13_conflicting_authority_resolution(self) -> StressTestScenarioResult:
        p_high = self._make_dummy_passage(
            chunk_id="chk-sc13-high",
            source_id="doc-official-kb",
            source_name="Official Knowledge Base",
            content="Enterprise SSO is supported for Okta, Azure AD, and Google Workspace.",
            authority_level=0.95,
        )
        p_low = self._make_dummy_passage(
            chunk_id="chk-sc13-low",
            source_id="conv-slack",
            source_name="Team Slack Chat",
            content="Enterprise SSO is unsupported for Okta and Azure AD.",
            authority_level=0.50,
        )
        conflict_res = self.conflict_detector.detect_conflicts([p_high, p_low])

        # Authority delta is 0.45 >= 0.25 -> resolved by authority
        has_resolution_hint = any(c.resolution_hint is not None and "Official Knowledge Base" in c.resolution_hint for c in conflict_res.conflicts)
        passed = has_resolution_hint

        return StressTestScenarioResult(
            scenario_id=13,
            scenario_name="Conflicting evidence with different authority levels",
            query="What identity providers are supported for SSO?",
            expected_behavior="Reconciles conflict by prioritizing higher authority official documentation.",
            actual_verdict="RESOLVED_BY_AUTHORITY" if passed else "UNRESOLVED",
            decision_outcome=RecommendedAction.ANSWER.value,
            reliability_status=EvidenceReliabilityStatus.MODERATE.value,
            conflicts_detected=conflict_res.conflicts_detected_count,
            counter_evidence_found=True,
            passed=passed,
            details={"resolution_hints": [c.resolution_hint for c in conflict_res.conflicts]},
        )

    # -------------------------------------------------------------
    # Scenario 14: Evidence that Appears Relevant but Does Not Directly Answer
    # -------------------------------------------------------------
    def test_scenario_14_relevant_but_indirect_evidence(self) -> StressTestScenarioResult:
        # Passage shares terms 'refund', 'payment', 'billing' but describes billing dates, not the refund window
        p_indirect = self._make_dummy_passage(
            chunk_id="chk-sc14-indirect",
            source_id="doc-billing-cycle",
            source_name="Billing Cycle Specification",
            content="All customer payment cycles renew on the 1st day of the billing month.",
            authority_level=0.85,
            relevance=0.75,
        )
        analysis = self._make_dummy_analysis(
            intent=IntentType.POLICY_LOOKUP.value,
            keywords=["refund", "window", "eligibility"],
        )
        scorer = EvidenceScorer()
        ev_score = scorer.score_evidence(
            chunk=self._passage_to_chunk(p_indirect),
            retrieval_score=0.75,
            query_analysis=analysis,
        )

        # Directness score must be heavily penalized
        passed = ev_score.directness_score <= 0.30
        return StressTestScenarioResult(
            scenario_id=14,
            scenario_name="Evidence that appears relevant but does not directly answer",
            query="What is the refund eligibility window?",
            expected_behavior="Assigns directness penalty for topically adjacent background passages.",
            actual_verdict=f"DIRECTNESS_SCORE_{ev_score.directness_score:.2f}",
            decision_outcome="directness_penalized",
            reliability_status=EvidenceReliabilityStatus.MODERATE.value,
            conflicts_detected=0,
            counter_evidence_found=False,
            passed=passed,
            details={"directness_score": ev_score.directness_score, "relevance_score": ev_score.relevance_score},
        )

    # -------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------
    def _make_dummy_passage(
        self,
        chunk_id: str,
        source_id: str,
        source_name: str = "Test Source",
        content: str = "",
        authority_level: float = 0.80,
        created_at: Optional[str] = "2025-06-01T00:00:00Z",
        relevance: float = 0.80,
    ) -> EvidencePassage:
        ev_score = EvidenceScore(
            relevance_score=relevance,
            authority_score=authority_level,
            freshness_score=0.90 if created_at else None,
            freshness_status="fresh" if created_at else "unknown",
            directness_score=0.85,
            directness_label="direct",
            final_evidence_score=round(0.35 * relevance + 0.25 * authority_level + 0.20 * 0.90 + 0.20 * 0.85, 4),
            scoring_explanation="Synthetic test passage",
            weights_applied={},
        )
        return EvidencePassage(
            chunk_id=chunk_id,
            source_id=source_id,
            source_name=source_name,
            source_type="documents",
            record_id=chunk_id,
            title="Synthetic Passage",
            content=content,
            authority_level=authority_level,
            created_at=created_at,
            original_file_path=f"data/{source_id}.json",
            chunk_index=0,
            retrieval_score=relevance,
            bm25_score=relevance,
            semantic_score=None,
            retrieval_mode="lexical_only",
            evidence_score=ev_score,
            citation=f"[{source_name} ({source_id}) § Chunk 0]",
            ranking_position=1,
        )

    def _passage_to_chunk(self, passage: EvidencePassage):
        from .models import ChunkData
        return ChunkData(
            chunk_id=passage.chunk_id,
            source_id=passage.source_id,
            source_type=passage.source_type,
            record_id=passage.record_id,
            title=passage.title,
            content=passage.content,
            created_at=passage.created_at,
            updated_at=passage.created_at,
            authority_level=passage.authority_level,
            original_file_path=passage.original_file_path,
            chunk_index=passage.chunk_index,
            metadata={},
        )

    def _make_dummy_analysis(
        self,
        intent: str = IntentType.POLICY_LOOKUP.value,
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
    ) -> QueryAnalysisResult:
        from .models import InformationCategory
        return QueryAnalysisResult(
            intent=intent,
            confidence=0.90,
            keywords=keywords or ["test"],
            entities=entities or [],
            technical_terms=[],
            information_category=InformationCategory.TECHNICAL.value,
            expected_information=["specifications"],
            likely_source_types=["documents"],
        )

