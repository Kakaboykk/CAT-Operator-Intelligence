"""
tests/test_ingestion.py

Phase 1 ingestion tests:
  12. Real company data ingestion (CSV loading)
  13. Loaded row counts
  — If source CSVs are unavailable, tests are skipped with a clear message.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.ingestion.loader import (
    IngestionResult,
    load_task_history_csv,
    load_telemetry_csv,
)

# ── Locate source CSV files ───────────────────────────────────────────────────
# Expected to be at the project root (alongside backend/).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

TELEMETRY_CSV = _PROJECT_ROOT / "telemetry.csv"
TASK_HISTORY_CSV = _PROJECT_ROOT / "task_history.csv"

# Also look for common alternative names
for _alt in ("Telemetry.csv", "company_telemetry.csv", "CAT_Telemetry.csv"):
    if (_PROJECT_ROOT / _alt).exists():
        TELEMETRY_CSV = _PROJECT_ROOT / _alt
        break

for _alt in ("TaskHistory.csv", "task_history.csv", "company_task_history.csv", "CAT_Task_History.csv"):
    if (_PROJECT_ROOT / _alt).exists():
        TASK_HISTORY_CSV = _PROJECT_ROOT / _alt
        break


# ── Minimal synthetic CSV fixtures (for pipeline validation, not data fidelity)

TELEMETRY_CSV_CONTENT = """\
Timestamp,Machine ID,Operator ID,Engine Hours,Fuel Used,Load Cycles,Idling Time,Seatbelt Status,Safety Alert Triggered
2024-01-15T08:00:00Z,MACHINE-001,OP-001,1200.5,45.2,8,12.0,Fastened,False
2024-01-15T09:00:00Z,MACHINE-001,OP-001,1201.5,48.0,10,5.0,Fastened,False
2024-01-15T10:00:00Z,MACHINE-002,OP-002,500.0,30.0,5,20.0,Unfastened,True
"""

TASK_HISTORY_CSV_CONTENT = """\
Task ID,Machine ID,Operator ID,Task Type,Weather,Operator Skill,Machine Age,Estimated Time,Actual Time
TASK-001,MACHINE-001,OP-001,Excavation,Clear,Intermediate,3.5,4.0,4.5
TASK-002,MACHINE-002,OP-002,Loading,Rainy,Expert,5.0,2.0,2.8
TASK-003,MACHINE-003,OP-003,Grading,Cloudy,Beginner,1.0,6.0,8.0
"""


# ── Helper: write temp CSV ────────────────────────────────────────────────────

def _write_temp_csv(content: str, suffix: str = ".csv") -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.flush()
    f.close()
    return f.name


# ── Test 12a: Pipeline validation (always runs) ───────────────────────────────

def test_telemetry_ingestion_pipeline(db):
    """Validates the full ingestion pipeline with minimal inline CSV."""
    csv_path = _write_temp_csv(TELEMETRY_CSV_CONTENT)
    try:
        result = load_telemetry_csv(csv_path, db)
        assert result.rows_read == 3
        assert result.rows_inserted == 3
        assert result.rows_skipped_invalid == 0
    finally:
        os.unlink(csv_path)


def test_task_history_ingestion_pipeline(db):
    """Validates the full task history ingestion pipeline."""
    csv_path = _write_temp_csv(TASK_HISTORY_CSV_CONTENT)
    try:
        result = load_task_history_csv(csv_path, db)
        assert result.rows_read == 3
        assert result.rows_inserted == 3
        assert result.rows_skipped_invalid == 0
    finally:
        os.unlink(csv_path)


def test_duplicate_task_history_skipped(db):
    """Loading the same CSV twice should skip duplicates on the second load."""
    csv_path = _write_temp_csv(TASK_HISTORY_CSV_CONTENT)
    try:
        r1 = load_task_history_csv(csv_path, db)
        r2 = load_task_history_csv(csv_path, db)
        assert r1.rows_inserted == 3
        assert r2.rows_inserted == 0
        assert r2.rows_skipped_duplicate == 3
    finally:
        os.unlink(csv_path)


def test_invalid_seatbelt_row_skipped(db):
    """A row with an invalid seatbelt_status is skipped and reported."""
    bad_csv = TELEMETRY_CSV_CONTENT + (
        "2024-01-15T11:00:00Z,MACHINE-003,OP-003,600.0,20.0,3,5.0,Unknown,False\n"
    )
    csv_path = _write_temp_csv(bad_csv)
    try:
        result = load_telemetry_csv(csv_path, db)
        assert result.rows_read == 4
        assert result.rows_inserted == 3
        assert result.rows_skipped_invalid == 1
        assert len(result.errors) == 1
    finally:
        os.unlink(csv_path)


def test_missing_column_raises(db):
    """A CSV missing required columns raises a ValueError immediately."""
    bad_csv = "Machine ID,Operator ID\nM1,O1\n"
    csv_path = _write_temp_csv(bad_csv)
    try:
        with pytest.raises(ValueError, match="Missing required columns"):
            load_telemetry_csv(csv_path, db)
    finally:
        os.unlink(csv_path)


# ── Test 12b & 13: Real company CSV loading (skipped if files unavailable) ────

@pytest.mark.skipif(
    not TELEMETRY_CSV.exists(),
    reason=f"Real telemetry CSV not found at {TELEMETRY_CSV}",
)
def test_real_telemetry_csv_loads(db):
    """Load the real company telemetry CSV and verify row counts > 0."""
    result = load_telemetry_csv(str(TELEMETRY_CSV), db)
    assert result.rows_read > 0, "Real CSV appears to be empty"
    assert result.rows_inserted > 0, (
        f"No rows inserted. Errors: {result.errors[:5]}"
    )
    print(
        f"\n[REAL DATA] Telemetry: read={result.rows_read} "
        f"inserted={result.rows_inserted} "
        f"invalid={result.rows_skipped_invalid}"
    )


@pytest.mark.skipif(
    not TASK_HISTORY_CSV.exists(),
    reason=f"Real task history CSV not found at {TASK_HISTORY_CSV}",
)
def test_real_task_history_csv_loads(db):
    """Load the real company task history CSV and verify row counts > 0."""
    result = load_task_history_csv(str(TASK_HISTORY_CSV), db)
    assert result.rows_read > 0, "Real CSV appears to be empty"
    assert result.rows_inserted > 0, (
        f"No rows inserted. Errors: {result.errors[:5]}"
    )
    print(
        f"\n[REAL DATA] TaskHistory: read={result.rows_read} "
        f"inserted={result.rows_inserted} "
        f"invalid={result.rows_skipped_invalid}"
    )
