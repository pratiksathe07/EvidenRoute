"""
EvidenRoute - Core Configuration Module
Handles application settings, CORS, configurable scoring weights,
and database connection placeholders for Member 1 integration.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable override support."""
    
    # App Information
    APP_NAME: str = "EvidenRoute Intelligence Engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/intelligence"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # PostgreSQL Database Connection Placeholder (for Member 1)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "evidenroute"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/evidenroute"

    # Default Source Scoring Weights (Sum = 1.0)
    WEIGHT_RELEVANCE: float = Field(0.35, ge=0.0, le=1.0)
    WEIGHT_SUITABILITY: float = Field(0.25, ge=0.0, le=1.0)
    WEIGHT_AUTHORITY: float = Field(0.20, ge=0.0, le=1.0)
    WEIGHT_HISTORICAL: float = Field(0.10, ge=0.0, le=1.0)
    WEIGHT_AVAILABILITY: float = Field(0.10, ge=0.0, le=1.0)

    # Source Selection Thresholds
    SELECTION_THRESHOLD: float = Field(0.40, ge=0.0, le=1.0)
    MIN_RELEVANCE_THRESHOLD: float = Field(0.15, ge=0.0, le=1.0)

    # LLM Settings (Disabled for Phase 1 - Local-first rule)
    LLM_PROVIDER: str = "none"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
