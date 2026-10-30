"""
EvidenRoute - Unified Backend Application Entrypoint
FastAPI application integrating Core Backend APIs (Sources, Budget Management, Dynamic Querying)
and the Intelligence Engine (Query Analysis, Source Selection, Hybrid Retrieval, Conflict Detection & Sufficiency).
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Member 1 Backend Routers & Database
try:
    from backend.app.api.sources import router as sources_router, seed_sources_and_records
    from backend.app.api.query import router as query_router
    from backend.app.api.settings_routes import router as settings_router
    from backend.app.database.db import SessionLocal, init_db
except ImportError:
    from app.api.sources import router as sources_router, seed_sources_and_records
    from app.api.query import router as query_router
    from app.api.settings_routes import router as settings_router
    from app.database.db import SessionLocal, init_db

# Member 2 Intelligence Engine Router & Core Configuration
try:
    from .api.intelligence_routes import router as intelligence_router
    from .core.config import settings
except ImportError:
    from backend.app.api.intelligence_routes import router as intelligence_router
    from backend.app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("evidenroute")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite schema & default records
    logger.info("Initializing EvidenRoute database tables and seed sources...")
    try:
        init_db()
        with SessionLocal() as db:
            seed_sources_and_records(db)
        logger.info("EvidenRoute database and seed sources initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    yield
    # Shutdown logic
    logger.info("EvidenRoute server shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Intelligent Context Selection & Evidence Evaluation Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for local React/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Member 1 Core API Routers
app.include_router(sources_router)
app.include_router(query_router)
app.include_router(settings_router)

# Register Member 2 Intelligence API Routers
app.include_router(intelligence_router, prefix=settings.API_V1_STR, tags=["Intelligence"])


@app.get("/api/health", tags=["system"])
def health_check():
    """
    Returns system health and runtime metrics for Member 1 test contracts.
    """
    return {
        "status": "healthy",
        "service": "EvidenRoute Intelligent Context Selection Engine",
        "version": "1.0.0",
        "database": "sqlite",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "EvidenRoute",
        "description": "Intelligent Context Selection Engine",
        "status": "operational",
        "health_check": f"{settings.API_V1_STR}/health",
        "system_health": "/api/health",
        "api_docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

