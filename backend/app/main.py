import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.sources import router as sources_router, seed_sources_and_records
from backend.app.api.query import router as query_router
from backend.app.database.db import SessionLocal, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("evidenroute")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite schema
    logger.info("Initializing EvidenRoute database tables...")
    init_db()

    # Seed default sample data if not already populated
    with SessionLocal() as db:
        seed_sources_and_records(db)
    logger.info("EvidenRoute database and seed sources initialized successfully.")

    yield
    # Shutdown logic if any
    logger.info("EvidenRoute server shutting down.")


app = FastAPI(
    title="EvidenRoute API",
    description="Intelligent Context Selection & Evidence Evaluation Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(sources_router)
app.include_router(query_router)


@app.get("/api/health", tags=["system"])
def health_check():
    """
    Returns system health and runtime metrics.
    """
    return {
        "status": "healthy",
        "service": "EvidenRoute Intelligent Context Selection Engine",
        "version": "1.0.0",
        "database": "sqlite",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
