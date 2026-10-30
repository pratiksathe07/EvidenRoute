import threading
from typing import Optional
from backend.app.schemas.budget import BudgetConfig, BudgetStatus, BudgetUsage


class BudgetExceededError(Exception):
    """Raised when an operation requests retrieval exceeding configured limits."""
    pass


class BudgetManager:
    """
    Central, thread-safe budget controller for all retrieval operations and stress tests.
    Strictly prevents quota overruns across calls, candidates, and tokens.
    Uses RLock to support re-entrant status inspection.
    """

    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        self._lock = threading.RLock()

        # Consumption counters
        self.calls_consumed: int = 0
        self.candidates_consumed: int = 0
        self.tokens_consumed: int = 0

        # Pending reservations (in-flight queries)
        self.calls_reserved: int = 0
        self.candidates_reserved: int = 0
        self.tokens_reserved: int = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Calculates conservative token estimate (~4 characters per token).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def remaining_calls(self) -> int:
        with self._lock:
            return max(0, self.config.max_source_calls - (self.calls_consumed + self.calls_reserved))

    def remaining_candidates(self) -> int:
        with self._lock:
            return max(0, self.config.max_candidates - (self.candidates_consumed + self.candidates_reserved))

    def remaining_tokens(self) -> int:
        with self._lock:
            return max(0, self.config.max_tokens - (self.tokens_consumed + self.tokens_reserved))

    def can_allocate(self, calls: int = 1, candidates: int = 1, tokens: int = 0) -> bool:
        """
        Checks if requested quota is available without committing it.
        """
        with self._lock:
            calls_avail = (self.calls_consumed + self.calls_reserved + calls) <= self.config.max_source_calls
            cands_avail = (self.candidates_consumed + self.candidates_reserved + candidates) <= self.config.max_candidates
            tokens_avail = (self.tokens_consumed + self.tokens_reserved + tokens) <= self.config.max_tokens
            return calls_avail and cands_avail and tokens_avail

    def reserve(self, calls: int = 1, candidates: int = 1, tokens: int = 0) -> bool:
        """
        Atomically reserves budget for an in-flight adapter or stress test call.
        Returns True if reservation succeeded, False if insufficient budget.
        """
        with self._lock:
            if not (
                (self.calls_consumed + self.calls_reserved + calls) <= self.config.max_source_calls
                and (self.candidates_consumed + self.candidates_reserved + candidates) <= self.config.max_candidates
                and (self.tokens_consumed + self.tokens_reserved + tokens) <= self.config.max_tokens
            ):
                return False

            self.calls_reserved += calls
            self.candidates_reserved += candidates
            self.tokens_reserved += tokens
            return True

    def commit(
        self,
        reserved_calls: int = 1,
        reserved_candidates: int = 0,
        reserved_tokens: int = 0,
        actual_calls: int = 1,
        actual_candidates: int = 0,
        actual_tokens: int = 0,
    ) -> None:
        """
        Finalizes an operation by decrementing reserved quota and incrementing consumed quota.
        """
        with self._lock:
            self.calls_reserved = max(0, self.calls_reserved - reserved_calls)
            self.candidates_reserved = max(0, self.candidates_reserved - reserved_candidates)
            self.tokens_reserved = max(0, self.tokens_reserved - reserved_tokens)

            self.calls_consumed += actual_calls
            self.candidates_consumed += actual_candidates
            self.tokens_consumed += actual_tokens

    def release(self, calls: int = 1, candidates: int = 0, tokens: int = 0) -> None:
        """
        Releases reserved budget if a search failed or was cancelled.
        """
        with self._lock:
            self.calls_reserved = max(0, self.calls_reserved - calls)
            self.candidates_reserved = max(0, self.candidates_reserved - candidates)
            self.tokens_reserved = max(0, self.tokens_reserved - tokens)

    def record_consumption(self, calls: int = 0, candidates: int = 0, tokens: int = 0) -> None:
        """
        Directly charges budget for completed operations (e.g. ad-hoc chunks).
        Raises BudgetExceededError if it would exceed limits.
        """
        with self._lock:
            if (self.calls_consumed + calls) > self.config.max_source_calls:
                raise BudgetExceededError(
                    f"Calls exceeded limit: {self.calls_consumed + calls} > {self.config.max_source_calls}"
                )
            if (self.candidates_consumed + candidates) > self.config.max_candidates:
                raise BudgetExceededError(
                    f"Candidates exceeded limit: {self.candidates_consumed + candidates} > {self.config.max_candidates}"
                )
            if (self.tokens_consumed + tokens) > self.config.max_tokens:
                raise BudgetExceededError(
                    f"Tokens exceeded limit: {self.tokens_consumed + tokens} > {self.config.max_tokens}"
                )

            self.calls_consumed += calls
            self.candidates_consumed += candidates
            self.tokens_consumed += tokens

    def is_exhausted(self) -> bool:
        """
        Returns True if any critical dimension has 0 budget remaining.
        """
        with self._lock:
            return (
                self.calls_consumed >= self.config.max_source_calls
                or self.candidates_consumed >= self.config.max_candidates
                or self.tokens_consumed >= self.config.max_tokens
            )

    def get_status(self) -> BudgetStatus:
        """
        Returns an immutable snapshot of current budget state.
        """
        with self._lock:
            return BudgetStatus(
                configured=self.config.model_copy(),
                consumed=BudgetUsage(
                    calls_consumed=self.calls_consumed,
                    candidates_consumed=self.candidates_consumed,
                    tokens_consumed=self.tokens_consumed,
                ),
                remaining_calls=max(0, self.config.max_source_calls - self.calls_consumed),
                remaining_candidates=max(0, self.config.max_candidates - self.candidates_consumed),
                remaining_tokens=max(0, self.config.max_tokens - self.tokens_consumed),
                is_exhausted=self.is_exhausted(),
            )
