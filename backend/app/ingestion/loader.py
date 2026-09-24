"""
app/ingestion/loader.py

Real company data ingestion pipeline.

Flow:
  Company CSV
    ↓ Column validation
    ↓ Data type validation
    ↓ Transformation / mapping (source column name → internal name)
    ↓ Pydantic schema validation
    ↓ Database insertion (duplicate-safe)
    ↓ Validation report

Rules:
  - Required columns must be present; missing columns → abort with clear error.
  - Missing values are reported, not silently invented or dropped.
  - Malformed rows are collected and reported; valid rows still load.
  - Duplicates (identified by natural key) are skipped with a warning.
  - No synthetic data is generated here.

Source column → internal column mappings are defined explicitly per dataset.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.task_history import TaskHistory
from app.models.telemetry import Telemetry
from app.schemas.task_history import TaskHistoryCreate
from app.schemas.telemetry import TelemetryCreate

logger = logging.getLogger(__name__)

# ── Column mappings ───────────────────────────────────────────────────────────
# Source CSV column name → internal (snake_case) field name.

TELEMETRY_COLUMN_MAP: dict[str, str] = {
    "Timestamp": "timestamp",
    "Machine ID": "machine_id",
    "Operator ID": "operator_id",
    "Engine Hours": "engine_hours",
    "Fuel Used": "fuel_used",
    "Load Cycles": "load_cycles",
    "Idling Time": "idling_time",
    "Seatbelt Status": "seatbelt_status",
    "Safety Alert Triggered": "safety_alert_triggered",
}

TASK_HISTORY_COLUMN_MAP: dict[str, str] = {
    "Task ID": "task_id",
    "Machine ID": "machine_id",
    "Operator ID": "operator_id",
    "Task Type": "task_type",
    "Weather": "weather",
    "Operator Skill": "operator_skill",
    "Machine Age": "machine_age",
    "Estimated Time": "estimated_time",
    "Actual Time": "actual_time",
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    """Summary report produced by each loader function."""

    dataset_name: str
    rows_read: int = 0
    rows_inserted: int = 0
    rows_skipped_duplicate: int = 0
    rows_skipped_invalid: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    def log_summary(self) -> None:
        logger.info(
            "[%s] read=%d inserted=%d dup_skipped=%d invalid_skipped=%d errors=%d",
            self.dataset_name,
            self.rows_read,
            self.rows_inserted,
            self.rows_skipped_duplicate,
            self.rows_skipped_invalid,
            len(self.errors),
        )
        for err in self.errors:
            logger.warning("[%s] Row %s: %s", self.dataset_name, err.get("row"), err.get("error"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_columns(df: pd.DataFrame, column_map: dict[str, str], dataset_name: str) -> None:
    """Raise ValueError if any required source column is missing."""
    missing = [col for col in column_map if col not in df.columns]
    if missing:
        raise ValueError(
            f"[{dataset_name}] Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )


def _rename_columns(df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    """Rename source columns to internal names; drop unrecognised columns."""
    return df.rename(columns=column_map)[list(column_map.values())]


# ── Telemetry loader ──────────────────────────────────────────────────────────

def load_telemetry_csv(csv_path: str, db: Session) -> IngestionResult:
    """
    Load the company Telemetry CSV into the telemetry table.

    Args:
        csv_path: Absolute or relative path to the company CSV file.
        db:       Active SQLAlchemy session.

    Returns:
        IngestionResult with load statistics and error details.
    """
    result = IngestionResult(dataset_name="Telemetry")

    # 1. Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise RuntimeError(f"Cannot read telemetry CSV at '{csv_path}': {exc}") from exc

    result.rows_read = len(df)
    logger.info("[Telemetry] Read %d rows from '%s'", result.rows_read, csv_path)

    # 2. Validate required columns
    _validate_columns(df, TELEMETRY_COLUMN_MAP, "Telemetry")

    # 3. Rename to internal names
    df = _rename_columns(df, TELEMETRY_COLUMN_MAP)

    # 4. Parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    # 5. Coerce numeric fields
    for col in ("engine_hours", "fuel_used", "idling_time"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["load_cycles"] = pd.to_numeric(df["load_cycles"], errors="coerce").astype("Int64")

    # 6. Coerce boolean
    bool_map = {
        True: True, False: False,
        "true": True, "false": False,
        "yes": True, "no": False,
        "1": True, "0": False,
        1: True, 0: False,
    }
    df["safety_alert_triggered"] = df["safety_alert_triggered"].map(
        lambda v: bool_map.get(str(v).strip().lower(), None)
        if not pd.isna(v) else None
    )

    # 7. Row-by-row validation and insertion
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_label = f"index={idx}"

        # Check for missing required values
        missing_fields = [k for k, v in row_dict.items() if v is None or (isinstance(v, float) and pd.isna(v))]
        if missing_fields:
            result.rows_skipped_invalid += 1
            result.errors.append({
                "row": row_label,
                "error": f"Missing/null values in required fields: {missing_fields}",
            })
            continue

        # Pydantic validation
        try:
            validated = TelemetryCreate(**row_dict)
        except Exception as exc:
            result.rows_skipped_invalid += 1
            result.errors.append({"row": row_label, "error": str(exc)})
            continue

        # Insert (no natural unique key on telemetry — all rows insert)
        try:
            orm_obj = Telemetry(**validated.model_dump())
            db.add(orm_obj)
            db.flush()
            result.rows_inserted += 1
        except IntegrityError as exc:
            db.rollback()
            result.rows_skipped_duplicate += 1
            result.errors.append({"row": row_label, "error": f"IntegrityError: {exc.orig}"})

    db.commit()
    result.log_summary()
    return result


# ── Task History loader ───────────────────────────────────────────────────────

def load_task_history_csv(csv_path: str, db: Session) -> IngestionResult:
    """
    Load the company Task History CSV into the task_history table.

    Duplicate task_id values are skipped with a warning.

    Args:
        csv_path: Absolute or relative path to the company CSV file.
        db:       Active SQLAlchemy session.

    Returns:
        IngestionResult with load statistics and error details.
    """
    result = IngestionResult(dataset_name="TaskHistory")

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise RuntimeError(f"Cannot read task history CSV at '{csv_path}': {exc}") from exc

    result.rows_read = len(df)
    logger.info("[TaskHistory] Read %d rows from '%s'", result.rows_read, csv_path)

    _validate_columns(df, TASK_HISTORY_COLUMN_MAP, "TaskHistory")
    df = _rename_columns(df, TASK_HISTORY_COLUMN_MAP)

    # Coerce numeric fields
    for col in ("machine_age", "estimated_time", "actual_time"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Build a set of existing task_ids for duplicate detection
    existing_ids: set[str] = {
        row[0] for row in db.query(TaskHistory.task_id).all()
    }

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_label = f"index={idx}"

        missing_fields = [k for k, v in row_dict.items() if v is None or (isinstance(v, float) and pd.isna(v))]
        if missing_fields:
            result.rows_skipped_invalid += 1
            result.errors.append({
                "row": row_label,
                "error": f"Missing/null values in required fields: {missing_fields}",
            })
            continue

        try:
            validated = TaskHistoryCreate(**row_dict)
        except Exception as exc:
            result.rows_skipped_invalid += 1
            result.errors.append({"row": row_label, "error": str(exc)})
            continue

        # Duplicate check on business key
        if validated.task_id in existing_ids:
            result.rows_skipped_duplicate += 1
            logger.debug("[TaskHistory] Skipping duplicate task_id='%s'", validated.task_id)
            continue

        try:
            orm_obj = TaskHistory(**validated.model_dump())
            db.add(orm_obj)
            db.flush()
            existing_ids.add(validated.task_id)
            result.rows_inserted += 1
        except IntegrityError as exc:
            db.rollback()
            result.rows_skipped_duplicate += 1
            result.errors.append({"row": row_label, "error": f"IntegrityError: {exc.orig}"})

    db.commit()
    result.log_summary()
    return result
