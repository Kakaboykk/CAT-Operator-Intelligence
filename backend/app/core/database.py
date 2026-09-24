"""
Database module.

Provides:
  - SQLAlchemy async-compatible engine
  - Session factory
  - Declarative Base
  - FastAPI dependency get_db()
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # detect stale connections
    echo=(settings.APP_ENV == "development"),
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """Yield a database session; close it when the request is done."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
