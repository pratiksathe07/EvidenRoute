import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.db import get_db
from backend.app.database.models import QueryRunModel
from backend.app.schemas.query import QueryRequest, QueryResponse, TraceStep
from backend.app.services.query_orchestrator import QueryOrchestrator

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def submit_query(payload: QueryRequest, db: Session = Depends(get_db)):
    """
    Primary endpoint: Executes intelligent context selection, bounded retrieval,
    evidence scoring, contradiction checking, bounded stress testing, and final decision.
    """
    orchestrator = QueryOrchestrator(db)
    return orchestrator.execute(payload)


@router.get("/{query_id}")
def get_query_details(query_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full details of a past query run.
    """
    run = db.query(QueryRunModel).filter(QueryRunModel.query_id == query_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID '{query_id}' not found."
        )

    trace = []
    if run.trace_json:
        try:
            trace = json.loads(run.trace_json)
        except Exception:
            pass

    return {
        "query_id": run.query_id,
        "question": run.question,
        "outcome": run.outcome,
        "final_answer": run.final_answer,
        "abstention_reason": run.abstention_reason,
        "budget": {
            "calls_consumed": run.budget_calls_consumed,
            "calls_max": run.budget_calls_max,
            "candidates_consumed": run.budget_candidates_consumed,
            "candidates_max": run.budget_candidates_max,
            "tokens_consumed": run.budget_tokens_consumed,
            "tokens_max": run.budget_tokens_max,
        },
        "stress_test": {
            "executed": run.stress_test_executed,
            "impact": run.stress_test_impact,
            "summary": run.stress_test_summary,
        },
        "created_at": run.created_at,
        "trace": trace,
    }


@router.get("/{query_id}/trace", response_model=List[TraceStep])
def get_query_trace(query_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the sequential execution trace for visual inspection.
    """
    run = db.query(QueryRunModel).filter(QueryRunModel.query_id == query_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID '{query_id}' not found."
        )

    if not run.trace_json:
        return []

    try:
        raw_trace = json.loads(run.trace_json)
        return [TraceStep(**t) for t in raw_trace]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse trace log: {str(e)}"
        )


@router.get("", response_model=List[Dict[str, Any]])
def list_recent_queries(limit: int = 20, db: Session = Depends(get_db)):
    """
    Lists recent queries for dashboard analytics and audit log.
    """
    runs = db.query(QueryRunModel).order_by(QueryRunModel.created_at.desc()).limit(limit).all()
    return [
        {
            "query_id": r.query_id,
            "question": r.question,
            "outcome": r.outcome,
            "final_answer": r.final_answer,
            "budget_calls_consumed": r.budget_calls_consumed,
            "budget_tokens_consumed": r.budget_tokens_consumed,
            "stress_test_executed": r.stress_test_executed,
            "stress_test_impact": r.stress_test_impact,
            "created_at": r.created_at,
        }
        for r in runs
    ]
