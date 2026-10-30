from datetime import datetime
from backend.app.schemas import (
    SourceType,
    NormalizedEvidence,
    EvidenceScore,
    BudgetConfig,
    BudgetUsage,
    BudgetStatus,
    SourceRegistration,
    SourceInfo,
    SourceSelectionDecision,
    DecisionOutcome,
    ContradictionType,
    ContradictionItem,
    StressTestResult,
    TraceStep,
    QueryRequest,
    QueryResponse,
)


def test_normalized_evidence_schema():
    ev = NormalizedEvidence(
        evidence_id="ev_001",
        source_id="src_docs",
        source_type=SourceType.DOCUMENT,
        title="Payment Policy",
        content="All refunds must be requested within 14 days.",
        authority_score=0.9,
    )
    assert ev.evidence_id == "ev_001"
    assert ev.authority_score == 0.9
    data = ev.model_dump()
    assert data["source_type"] == "document"


def test_budget_schemas():
    config = BudgetConfig(max_source_calls=3, max_candidates=10, max_tokens=2000)
    usage = BudgetUsage(calls_consumed=1, candidates_consumed=5, tokens_consumed=800)
    status = BudgetStatus(
        configured=config,
        consumed=usage,
        remaining_calls=2,
        remaining_candidates=5,
        remaining_tokens=1200,
        is_exhausted=False,
    )
    assert status.remaining_calls == 2
    assert not status.is_exhausted


def test_query_schemas():
    req = QueryRequest(question="What is the refund period?", enable_stress_test=True)
    assert req.enable_stress_test is True

    resp = QueryResponse(
        query_id="q_100",
        question=req.question,
        outcome=DecisionOutcome.ANSWER,
        final_answer="The refund period is 14 days [ev_001].",
        citations=["ev_001"],
        budget_status=BudgetStatus(
            configured=BudgetConfig(),
            consumed=BudgetUsage(calls_consumed=1, candidates_consumed=1, tokens_consumed=50),
            remaining_calls=4,
            remaining_candidates=19,
            remaining_tokens=3950,
            is_exhausted=False,
        ),
        stress_test=StressTestResult(executed=False),
        execution_trace=[
            TraceStep(
                step_name="Query Understanding",
                summary="Detected refund policy question",
            )
        ],
    )
    assert resp.outcome == DecisionOutcome.ANSWER
    assert resp.citations == ["ev_001"]


if __name__ == "__main__":
    test_normalized_evidence_schema()
    test_budget_schemas()
    test_query_schemas()
    print("All contract schema tests passed successfully!")
