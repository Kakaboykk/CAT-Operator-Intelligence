"""
tests/conftest.py

Shared pytest fixtures for Phase 1 tests.

Uses an in-memory SQLite database so tests run without a live PostgreSQL
instance.  SQLite does NOT enforce all PostgreSQL constraints (e.g. UUID
type), so the fixture creates tables directly from the ORM models.

For full integration testing against PostgreSQL, set the environment
variable TEST_DATABASE_URL to a real PostgreSQL connection string.
"""

import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Import Base and all models to ensure table metadata is registered.
from app.core.database import Base
import app.models  # noqa: F401  registers all ORM classes


# ── Determine test database URL ───────────────────────────────────────────────
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:",
)

# For SQLite, enable foreign-key enforcement (disabled by default)
USE_SQLITE = TEST_DATABASE_URL.startswith("sqlite")


@pytest.fixture(scope="session")
def engine():
    """Create a test engine and build all tables once per session."""
    connect_args = {"check_same_thread": False} if USE_SQLITE else {}
    eng = create_engine(TEST_DATABASE_URL, connect_args=connect_args)

    if USE_SQLITE:
        # Enable FK enforcement for SQLite
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine):
    """Yield a transactional test session; roll back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
