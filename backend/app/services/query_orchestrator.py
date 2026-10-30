import json
import time
import uuid
from typing import Dict, List
from sqlalchemy.orm import Session

from backend.app.adapters.sqlite_source import SQLiteSourceAdapter
from backend.app.database.db import SessionLocal
from backend.app.database.models import (
    ContradictionModel,
    EvidenceResultModel,
    QueryRunModel,
    RecordModel,
    RetrievalLogModel,
    SourceModel,
)
from backend.app.schemas.evidence import NormalizedEvidence, SourceType
from backend.app.schemas.query import (
    DecisionOutcome,
    QueryRequest,
    QueryResponse,
    TraceStep,
)
from backend.app.schemas.source import SourceInfo
from backend.app.services.budget_manager import BudgetManager
from backend.app.services.contradiction_detector import ContradictionDetectorService
from backend.app.services.evidence_evaluator import EvidenceEvaluatorService
from backend.app.services.query_understanding import QueryUnderstandingService
from backend.app.services.source_selector import SourceSelectorService
from backend.app.services.stress_test import StressTestService


class QueryOrchestrator:
    """
    Coordinates the complete EvidenRoute context selection, budget enforcement,
    evidence scoring, contradiction analysis, stress testing, and decision pipeline.
    """

    def __init__(self, db: Session):
        self.db = db

    def execute(self, request: QueryRequest) -> QueryResponse:
        query_id = f"qr_{uuid.uuid4().hex[:10]}"
        trace: List[TraceStep] = []
        budget_mgr = BudgetManager(request.budget)

        # -------------------------------------------------------------
        # Step 1: Query Understanding
        # -------------------------------------------------------------
        t0 = time.time()
        profile = QueryUnderstandingService.analyze(request.question)
        duration_ms = (time.time() - t0) * 1000
        trace.append(
            TraceStep(
                step_name="Query Understanding",
                duration_ms=round(duration_ms, 2),
                summary=f"Extracted topic '{profile.topic}', intent '{profile.intent}', and {len(profile.clean_keywords)} keyword(s).",
                details={
                    "keywords": profile.clean_keywords,
                    "entities": profile.entities,
                    "expected_source_types": [t.value for t in profile.expected_source_types],
                    "requires_recent_info": profile.requires_recent_info,
                },
            )
        )

        # -------------------------------------------------------------
        # Step 2: Intelligent Source Selection
        # -------------------------------------------------------------
        t0 = time.time()
        available_sources = self._get_available_sources()
        decisions = SourceSelectorService.select_sources(
            profile=profile,
            available_sources=available_sources,
            max_to_select=2,
            min_relevance_threshold=0.30,
        )
        duration_ms = (time.time() - t0) * 1000
        selected_source_ids = [d.source_id for d in decisions if d.selected]
        trace.append(
            TraceStep(
                step_name="Source Selection",
                duration_ms=round(duration_ms, 2),
                summary=f"Selected {len(selected_source_ids)} source(s): {', '.join(selected_source_ids) if selected_source_ids else 'None'}.",
                details={"decisions": [d.model_dump() for d in decisions]},
            )
        )

        # -------------------------------------------------------------
        # Step 3: Bounded Retrieval
        # -------------------------------------------------------------
        t0 = time.time()
        retrieved_evidence: List[NormalizedEvidence] = []
        retrieval_log_records = []

        for decision in decisions:
            if not decision.selected:
                retrieval_log_records.append({
                    "source_id": decision.source_id,
                    "selected": False,
                    "relevance_score": decision.relevance_score,
                    "reason": decision.reason,
                    "candidates_retrieved": 0,
                })
                continue

            # Check and reserve budget for this source
            candidate_quota = min(decision.allocated_limit, budget_mgr.remaining_candidates())
            if not budget_mgr.reserve(calls=1, candidates=candidate_quota, tokens=1000):
                retrieval_log_records.append({
                    "source_id": decision.source_id,
                    "selected": False,
                    "relevance_score": decision.relevance_score,
                    "reason": "Skipped: Budget ceiling reached prior to invocation.",
                    "candidates_retrieved": 0,
                })
                continue

            # Execute search through adapter
            adapter = SQLiteSourceAdapter(decision.source_id, SessionLocal)
            query_str = " ".join(profile.clean_keywords) if profile.clean_keywords else request.question
            items = adapter.search(query_str, limit=candidate_quota)

            # Measure actual tokens
            actual_text = " ".join(item.content for item in items)
            actual_tokens = BudgetManager.estimate_tokens(actual_text)

            # Commit budget consumption
            budget_mgr.commit(
                reserved_calls=1,
                reserved_candidates=candidate_quota,
                reserved_tokens=1000,
                actual_calls=1,
                actual_candidates=len(items),
                actual_tokens=actual_tokens,
            )

            retrieved_evidence.extend(items)
            retrieval_log_records.append({
                "source_id": decision.source_id,
                "selected": True,
                "relevance_score": decision.relevance_score,
                "reason": decision.reason,
                "candidates_retrieved": len(items),
            })

        duration_ms = (time.time() - t0) * 1000
        trace.append(
            TraceStep(
                step_name="Bounded Retrieval",
                duration_ms=round(duration_ms, 2),
                summary=f"Retrieved {len(retrieved_evidence)} total evidence chunk(s) from {len(selected_source_ids)} source(s).",
                details={
                    "evidence_ids": [e.evidence_id for e in retrieved_evidence],
                    "budget_state": budget_mgr.get_status().model_dump(),
                },
            )
        )

        # -------------------------------------------------------------
        # Step 4: Evidence Evaluation
        # -------------------------------------------------------------
        t0 = time.time()
        scores = EvidenceEvaluatorService.evaluate(retrieved_evidence, profile)
        duration_ms = (time.time() - t0) * 1000
        trace.append(
            TraceStep(
                step_name="Evidence Evaluation",
                duration_ms=round(duration_ms, 2),
                summary=f"Evaluated {len(scores)} item(s) on Relevance, Authority, Freshness, and Directness.",
                details={"scores": [s.model_dump() for s in scores]},
            )
        )

        # -------------------------------------------------------------
        # Step 5: Contradiction Detection
        # -------------------------------------------------------------
        t0 = time.time()
        contradictions = ContradictionDetectorService.detect_contradictions(retrieved_evidence)
        duration_ms = (time.time() - t0) * 1000
        trace.append(
            TraceStep(
                step_name="Contradiction Detection",
                duration_ms=round(duration_ms, 2),
                summary=f"Detected {len(contradictions)} potential conflict(s) between evidence items.",
                details={"contradictions": [c.model_dump() for c in contradictions]},
            )
        )

        # -------------------------------------------------------------
        # Step 6: Sufficiency Gate & Initial Synthesis
        # -------------------------------------------------------------
        # Filter evidence with acceptable quality
        score_map = {s.evidence_id: s for s in scores}
        viable_evidence = [
            e for e in retrieved_evidence
            if score_map.get(e.evidence_id) and score_map[e.evidence_id].composite_score >= 0.40
        ]

        # Check for unresolvable critical conflicts
        critical_unresolved_conflicts = [
            c for c in contradictions if c.severity == "critical" and c.resolution_status == "unresolved"
        ]

        outcome = DecisionOutcome.ANSWER
        final_answer = None
        abstention_reason = None
        cited_ids: List[str] = []

        if not viable_evidence:
            outcome = DecisionOutcome.ABSTAIN
            abstention_reason = "No sufficiently relevant or authoritative evidence was found to answer the question reliably."
        elif critical_unresolved_conflicts:
            outcome = DecisionOutcome.ABSTAIN
            abstention_reason = (
                f"Abstained due to critical unresolved contradictions: {critical_unresolved_conflicts[0].description}"
            )
        else:
            # Sort viable evidence by composite score descending
            viable_evidence.sort(key=lambda e: score_map[e.evidence_id].composite_score, reverse=True)
            top_evidence = viable_evidence[:2]
            cited_ids = [e.evidence_id for e in top_evidence]

            # Construct verified answer directly referencing evidence chunks
            answer_snippets = [f"\"{e.content}\" [Source: {e.title} ({e.evidence_id})]" for e in top_evidence]
            final_answer = "Based on verified evidence:\n" + "\n".join(answer_snippets)

            # If Gemini is configured and enabled, synthesize grounded fluent answer
            try:
                from backend.app.core.config import settings
                if settings.GEMINI_API_KEY and settings.LLM_PROVIDER != "none":
                    import google.generativeai as genai
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    grounding_context = "\n".join(f"- [{e.title}]: {e.content}" for e in top_evidence)
                    prompt = (
                        f"You are EvidenRoute, an explainable context-grounded AI assistant.\n"
                        f"Answer the user question using ONLY the following verified evidence passages.\n"
                        f"Cite sources with their titles in brackets like [Source Title].\n"
                        f"Question: {request.question}\n\n"
                        f"Evidence:\n{grounding_context}\n\n"
                        f"Answer:"
                    )
                    resp = model.generate_content(prompt)
                    if resp and resp.text and resp.text.strip():
                        final_answer = resp.text.strip()
            except Exception:
                pass  # Gracefully fall back to deterministic verified snippets

        # -------------------------------------------------------------
        # Step 7: Evidence Stress Test (Key Differentiator)
        # -------------------------------------------------------------
        stress_result = None
        if outcome == DecisionOutcome.ANSWER and request.enable_stress_test:
            # Strictly constrain counterevidence search to Phase 1 selected sources
            selected_adapters = [
                SQLiteSourceAdapter(s.source_id, SessionLocal)
                for s in available_sources
                if s.source_id in selected_source_ids
            ]
            stress_result, challenge_items = StressTestService.execute_stress_test(
                tentative_answer=final_answer,
                profile=profile,
                initial_evidence=retrieved_evidence,
                available_adapters=selected_adapters,
                budget_manager=budget_mgr,
            )
            duration_ms = (time.time() - t0) * 1000

            if challenge_items:
                retrieved_evidence.extend(challenge_items)
                challenge_scores = EvidenceEvaluatorService.evaluate(challenge_items, profile)
                scores.extend(challenge_scores)

            if stress_result.counterevidence_found:
                final_answer += f"\n\n[Evidence Stress Test Caveat]: {stress_result.summary}"
                cited_ids.extend([e.evidence_id for e in challenge_items])

            trace.append(
                TraceStep(
                    step_name="Evidence Stress Test",
                    duration_ms=round(duration_ms, 2),
                    summary=f"Stress test outcome: {stress_result.impact_on_decision}. {stress_result.summary}",
                    details=stress_result.model_dump(),
                )
            )
        else:
            from backend.app.schemas.query import StressTestResult
            stress_result = StressTestResult(
                executed=False,
                summary="Stress test was not requested or was bypassed due to earlier abstention.",
            )

        # -------------------------------------------------------------
        # Step 8: Persist Run & Trace to Database
        # -------------------------------------------------------------
        budget_status = budget_mgr.get_status()
        self._persist_query_run(
            query_id=query_id,
            question=request.question,
            outcome=outcome,
            final_answer=final_answer,
            abstention_reason=abstention_reason,
            budget_status=budget_status,
            stress_result=stress_result,
            trace=trace,
            retrieval_logs=retrieval_log_records,
            scores=scores,
            cited_ids=cited_ids,
            contradictions=contradictions,
        )

        return QueryResponse(
            query_id=query_id,
            question=request.question,
            outcome=outcome,
            final_answer=final_answer,
            abstention_reason=abstention_reason,
            citations=cited_ids,
            selected_sources=decisions,
            retrieved_evidence=retrieved_evidence,
            evidence_scores=scores,
            contradictions=contradictions,
            budget_status=budget_status,
            stress_test=stress_result,
            execution_trace=trace,
        )

    def _get_available_sources(self) -> List[SourceInfo]:
        sources = self.db.query(SourceModel).all()
        results = []
        for src in sources:
            count = self.db.query(RecordModel).filter(RecordModel.source_id == src.source_id).count()
            metadata = {}
            if src.metadata_json:
                try:
                    metadata = json.loads(src.metadata_json)
                except Exception:
                    pass

            results.append(
                SourceInfo(
                    source_id=src.source_id,
                    name=src.name,
                    source_type=SourceType(src.source_type) if src.source_type in [e.value for e in SourceType] else SourceType.DOCUMENT,
                    description=src.description,
                    default_authority=src.default_authority,
                    enabled=src.enabled,
                    record_count=count,
                    status="healthy" if src.enabled else "disabled",
                    metadata=metadata,
                )
            )
        return results

    def _persist_query_run(
        self,
        query_id: str,
        question: str,
        outcome: DecisionOutcome,
        final_answer: str,
        abstention_reason: str,
        budget_status,
        stress_result,
        trace: List[TraceStep],
        retrieval_logs: List[dict],
        scores: List,
        cited_ids: List[str],
        contradictions: List,
    ):
        try:
            run_model = QueryRunModel(
                query_id=query_id,
                question=question,
                outcome=outcome.value,
                final_answer=final_answer,
                abstention_reason=abstention_reason,
                budget_calls_max=budget_status.configured.max_source_calls,
                budget_calls_consumed=budget_status.consumed.calls_consumed,
                budget_candidates_max=budget_status.configured.max_candidates,
                budget_candidates_consumed=budget_status.consumed.candidates_consumed,
                budget_tokens_max=budget_status.configured.max_tokens,
                budget_tokens_consumed=budget_status.consumed.tokens_consumed,
                stress_test_executed=stress_result.executed,
                stress_test_impact=stress_result.impact_on_decision,
                stress_test_summary=stress_result.summary,
                trace_json=json.dumps([t.model_dump(mode="json") for t in trace]),
            )
            self.db.add(run_model)

            # Persist retrieval decisions
            for log_data in retrieval_logs:
                log_entry = RetrievalLogModel(
                    query_id=query_id,
                    source_id=log_data["source_id"],
                    selected=log_data["selected"],
                    relevance_score=log_data["relevance_score"],
                    reason=log_data["reason"],
                    candidates_retrieved=log_data["candidates_retrieved"],
                )
                self.db.add(log_entry)

            # Persist evidence scores
            for sc in scores:
                ev_result = EvidenceResultModel(
                    query_id=query_id,
                    evidence_id=sc.evidence_id,
                    source_id="",
                    relevance_score=sc.relevance_score,
                    authority_score=sc.authority_score,
                    freshness_score=sc.freshness_score,
                    directness_score=sc.directness_score,
                    composite_score=sc.composite_score,
                    cited=sc.evidence_id in cited_ids,
                    notes=sc.evaluation_notes,
                )
                self.db.add(ev_result)

            # Persist contradictions
            for ct in contradictions:
                ct_model = ContradictionModel(
                    conflict_id=ct.conflict_id,
                    query_id=query_id,
                    evidence_a_id=ct.evidence_a_id,
                    evidence_b_id=ct.evidence_b_id,
                    contradiction_type=ct.contradiction_type.value,
                    description=ct.description,
                    severity=ct.severity,
                    resolution_status=ct.resolution_status,
                )
                self.db.add(ct_model)

            self.db.commit()
        except Exception:
            self.db.rollback()
