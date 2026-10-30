from pydantic import BaseModel, Field


class BudgetConfig(BaseModel):
    """
    Configuration specifying retrieval ceilings across supported dimensions.
    """
    max_source_calls: int = Field(5, ge=1, description="Maximum number of external/adapter queries")
    max_candidates: int = Field(20, ge=1, description="Maximum total evidence chunks retrieved")
    max_tokens: int = Field(4000, ge=100, description="Maximum aggregate evidence token budget")


class BudgetUsage(BaseModel):
    """
    Cumulative usage tracked by the central Budget Manager.
    """
    calls_consumed: int = Field(0, ge=0)
    candidates_consumed: int = Field(0, ge=0)
    tokens_consumed: int = Field(0, ge=0)


class BudgetStatus(BaseModel):
    """
    Current snapshot of budget capacity and remaining allocations.
    """
    configured: BudgetConfig
    consumed: BudgetUsage
    remaining_calls: int
    remaining_candidates: int
    remaining_tokens: int
    is_exhausted: bool
