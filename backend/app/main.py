"""
FastAPI application entry point — Phase 1 foundation.

Phase 1 exposes only:
  GET /health  — verifies that the backend starts and the DB is reachable.

Phase 2+ endpoints will be added in later files/routers.
"""

import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

from app.training.router import router as training_router
from app.dashboard.router import router as dashboard_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CAT Smart Operator Assistant",
    description=(
        "Backend API for the CAT Smart Operator Assistant. "
        "Phase 1: Data Foundation."
    ),
    version="0.1.0",
)

# CORS configuration for frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(training_router)
app.include_router(dashboard_router)


# ── Health endpoint ───────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health_check() -> dict:
    """
    Health check.

    Returns a JSON object confirming:
      - the backend process is running
      - the PostgreSQL database is reachable
    """
    db_status = "ok"
    db_error: str | None = None

    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_error = str(exc)
        logger.warning("Health check: DB error: %s", exc)

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": "CAT Smart Operator Assistant",
        "phase": 1,
        "database": db_status,
        **({"db_error": db_error} if db_error else {}),
    }
