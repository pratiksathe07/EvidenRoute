import pytest
from backend.app.schemas.budget import BudgetConfig
from backend.app.services.budget_manager import BudgetExceededError, BudgetManager


def test_budget_manager_initialization():
    config = BudgetConfig(max_source_calls=3, max_candidates=10, max_tokens=1000)
    bm = BudgetManager(config)
    status = bm.get_status()

    assert status.remaining_calls == 3
    assert status.remaining_candidates == 10
    assert status.remaining_tokens == 1000
    assert not status.is_exhausted


def test_budget_reservation_and_commit():
    config = BudgetConfig(max_source_calls=2, max_candidates=5, max_tokens=500)
    bm = BudgetManager(config)

    # Reserve 1 call
    reserved = bm.reserve(calls=1, candidates=2, tokens=100)
    assert reserved is True
    assert bm.remaining_calls() == 1

    # Commit with actual usage
    bm.commit(
        reserved_calls=1,
        reserved_candidates=2,
        reserved_tokens=100,
        actual_calls=1,
        actual_candidates=2,
        actual_tokens=90,
    )

    status = bm.get_status()
    assert status.consumed.calls_consumed == 1
    assert status.consumed.candidates_consumed == 2
    assert status.consumed.tokens_consumed == 90
    assert status.remaining_calls == 1
    assert not status.is_exhausted


def test_budget_reservation_rejection_when_exceeded():
    config = BudgetConfig(max_source_calls=1, max_candidates=2, max_tokens=100)
    bm = BudgetManager(config)

    # Reserve max calls
    assert bm.reserve(calls=1, candidates=1, tokens=50) is True

    # Next reservation should fail
    assert bm.reserve(calls=1, candidates=1, tokens=10) is False


def test_budget_release():
    config = BudgetConfig(max_source_calls=2, max_candidates=5, max_tokens=500)
    bm = BudgetManager(config)

    assert bm.reserve(calls=1, candidates=2, tokens=100) is True
    assert bm.remaining_calls() == 1

    # Release reservation upon search failure
    bm.release(calls=1, candidates=2, tokens=100)
    assert bm.remaining_calls() == 2


def test_direct_consumption_exceeded_error():
    config = BudgetConfig(max_source_calls=1, max_candidates=5, max_tokens=500)
    bm = BudgetManager(config)

    bm.record_consumption(calls=1, candidates=2, tokens=100)
    assert bm.is_exhausted() is True

    with pytest.raises(BudgetExceededError):
        bm.record_consumption(calls=1)


def test_token_estimation():
    text = "EvidenRoute is an intelligent context selection engine."
    tokens = BudgetManager.estimate_tokens(text)
    assert tokens > 0
    assert BudgetManager.estimate_tokens("") == 0
