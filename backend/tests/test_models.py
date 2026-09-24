"""
tests/test_models.py

Phase 1 model tests:
  1. Database connection / table creation
  2. Valid telemetry record
  3. Valid task-history record
  4. Valid machine-fault record
  5. Valid incident record
  6. Valid daily-task schedule record
  7. Required-field validation (Pydantic)
  8. Invalid data rejection
  9. Foreign-key / reference integrity
  10. Duplicate handling (task_id unique constraint)
  11. Downtime non-negative constraint
"""

import uuid
from datetime import date, datetime, time, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.models.daily_task import DailyTaskSchedule
from app.models.incident import Incident
from app.models.machine_fault import MachineFault
from app.models.task_history import TaskHistory
from app.models.telemetry import Telemetry
from app.schemas.daily_task import DailyTaskScheduleCreate
from app.schemas.incident import IncidentCreate
from app.schemas.machine_fault import MachineFaultCreate
from app.schemas.task_history import TaskHistoryCreate
from app.schemas.telemetry import TelemetryCreate


# ── Helpers ───────────────────────────────────────────────────────────────────

NOW = datetime.now(tz=timezone.utc)


def make_telemetry(**overrides) -> dict:
    base = {
        "timestamp": NOW,
        "machine_id": "MACHINE-001",
        "operator_id": "OP-001",
        "engine_hours": 1234.5,
        "fuel_used": 50.0,
        "load_cycles": 10,
        "idling_time": 15.0,
        "seatbelt_status": "Fastened",
        "safety_alert_triggered": False,
    }
    base.update(overrides)
    return base


def make_task_history(**overrides) -> dict:
    base = {
        "task_id": f"TASK-{uuid.uuid4().hex[:6]}",
        "task_type": "Excavation",
        "weather": "Clear",
        "operator_skill": "Intermediate",
        "machine_age": 3.5,
        "estimated_time": 4.0,
        "actual_time": 4.5,
    }
    base.update(overrides)
    return base


def insert_task(db, **overrides) -> TaskHistory:
    data = make_task_history(**overrides)
    obj = TaskHistory(**TaskHistoryCreate(**data).model_dump())
    db.add(obj)
    db.flush()
    return obj


# ── Test 1: Table creation ─────────────────────────────────────────────────────

def test_all_tables_exist(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for expected in [
        "telemetry",
        "task_history",
        "machine_fault",
        "incident",
        "daily_task_schedule",
    ]:
        assert expected in tables, f"Expected table '{expected}' not found; got {tables}"


# ── Test 2: Valid telemetry record ────────────────────────────────────────────

def test_valid_telemetry_insert(db):
    data = make_telemetry()
    obj = Telemetry(**TelemetryCreate(**data).model_dump())
    db.add(obj)
    db.flush()

    fetched = db.query(Telemetry).filter_by(id=obj.id).first()
    assert fetched is not None
    assert fetched.machine_id == "MACHINE-001"
    assert fetched.seatbelt_status == "Fastened"
    assert fetched.safety_alert_triggered is False


# ── Test 3: Valid task history record ─────────────────────────────────────────

def test_valid_task_history_insert(db):
    task_id = f"TASK-{uuid.uuid4().hex[:6]}"
    data = make_task_history(task_id=task_id)
    obj = TaskHistory(**TaskHistoryCreate(**data).model_dump())
    db.add(obj)
    db.flush()

    fetched = db.query(TaskHistory).filter_by(task_id=task_id).first()
    assert fetched is not None
    assert fetched.task_type == "Excavation"
    assert fetched.weather == "Clear"


# ── Test 4: Valid machine fault record ────────────────────────────────────────

def test_valid_machine_fault_insert(db):
    task = insert_task(db)
    data = {
        "task_id": task.task_id,
        "machine_status": "Fault",
        "fault_type": "Hydraulic Leak",
        "downtime": 30.0,
    }
    obj = MachineFault(**MachineFaultCreate(**data).model_dump())
    db.add(obj)
    db.flush()

    fetched = db.query(MachineFault).filter_by(id=obj.id).first()
    assert fetched is not None
    assert fetched.downtime == 30.0
    assert fetched.machine_status == "Fault"


def test_machine_fault_operational_no_fault_type(db):
    data = {
        "task_id": None,
        "machine_status": "Operational",
        "fault_type": None,
        "downtime": 0.0,
    }
    obj = MachineFault(**MachineFaultCreate(**data).model_dump())
    db.add(obj)
    db.flush()
    assert obj.id is not None


# ── Test 5: Valid incident record ─────────────────────────────────────────────

def test_valid_incident_insert(db):
    data = {
        "timestamp": NOW,
        "operator_id": "OP-001",
        "machine_id": "MACHINE-001",
        "event_type": "Seatbelt Violation",
        "severity": "High",
        "description": "Operator did not fasten seatbelt.",
        "status": "Open",
    }
    schema = IncidentCreate(**data)
    obj = Incident(**schema.model_dump())
    db.add(obj)
    db.flush()

    fetched = db.query(Incident).filter_by(incident_id=obj.incident_id).first()
    assert fetched is not None
    assert fetched.severity == "High"
    assert fetched.status == "Open"


# ── Test 6: Valid daily task schedule record ───────────────────────────────────

def test_valid_daily_task_schedule_insert(db):
    task = insert_task(db)
    data = {
        "task_id": task.task_id,
        "operator_id": "OP-001",
        "machine_id": "MACHINE-001",
        "scheduled_date": date.today(),
        "scheduled_time": time(8, 0),
        "task_status": "Scheduled",
    }
    schema = DailyTaskScheduleCreate(**data)
    obj = DailyTaskSchedule(**schema.model_dump())
    db.add(obj)
    db.flush()

    fetched = db.query(DailyTaskSchedule).filter_by(schedule_id=obj.schedule_id).first()
    assert fetched is not None
    assert fetched.task_status == "Scheduled"


# ── Test 7 & 8: Required-field validation / invalid data rejection ─────────────

def test_telemetry_missing_machine_id_rejected():
    with pytest.raises(ValidationError):
        TelemetryCreate(**make_telemetry(machine_id=""))


def test_telemetry_invalid_seatbelt_status_rejected():
    with pytest.raises(ValidationError):
        TelemetryCreate(**make_telemetry(seatbelt_status="Unknown"))


def test_telemetry_negative_engine_hours_rejected():
    with pytest.raises(ValidationError):
        TelemetryCreate(**make_telemetry(engine_hours=-1.0))


def test_telemetry_negative_fuel_rejected():
    with pytest.raises(ValidationError):
        TelemetryCreate(**make_telemetry(fuel_used=-5.0))


def test_task_history_missing_task_id_rejected():
    with pytest.raises(ValidationError):
        TaskHistoryCreate(**make_task_history(task_id=""))


def test_machine_fault_negative_downtime_rejected():
    with pytest.raises(ValidationError):
        MachineFaultCreate(
            task_id=None,
            machine_status="Fault",
            fault_type="Engine",
            downtime=-1.0,
        )


def test_incident_invalid_severity_rejected():
    with pytest.raises(ValidationError):
        IncidentCreate(
            timestamp=NOW,
            event_type="Test",
            severity="SuperHigh",
            status="Open",
        )


def test_incident_invalid_status_rejected():
    with pytest.raises(ValidationError):
        IncidentCreate(
            timestamp=NOW,
            event_type="Test",
            severity="Low",
            status="Pending",
        )


def test_daily_task_invalid_status_rejected():
    with pytest.raises(ValidationError):
        DailyTaskScheduleCreate(
            task_id="T1",
            operator_id="OP-1",
            machine_id="M-1",
            scheduled_date=date.today(),
            scheduled_time=time(9, 0),
            task_status="Running",
        )


# ── Test 9: FK integrity ───────────────────────────────────────────────────────

def test_daily_task_schedule_fk_integrity(db):
    """DailyTaskSchedule.task_id must reference an existing task_history.task_id."""
    obj = DailyTaskSchedule(
        schedule_id=uuid.uuid4(),
        task_id="NONEXISTENT-TASK",
        operator_id="OP-1",
        machine_id="M-1",
        scheduled_date=date.today(),
        scheduled_time=time(9, 0),
        task_status="Scheduled",
    )
    db.add(obj)
    with pytest.raises(IntegrityError):
        db.flush()


# ── Test 10: Duplicate task_id ────────────────────────────────────────────────

def test_duplicate_task_id_rejected(db):
    """task_history.task_id has a UNIQUE constraint."""
    task_id = f"DUP-{uuid.uuid4().hex[:6]}"
    obj1 = TaskHistory(**TaskHistoryCreate(**make_task_history(task_id=task_id)).model_dump())
    obj2 = TaskHistory(**TaskHistoryCreate(**make_task_history(task_id=task_id)).model_dump())
    db.add(obj1)
    db.flush()
    db.add(obj2)
    with pytest.raises(IntegrityError):
        db.flush()


# ── Test 11: Non-negative downtime constraint ──────────────────────────────────

def test_downtime_non_negative_db_constraint(db, engine):
    """Verify the CHECK constraint fires at the DB level (PostgreSQL only)."""
    import os
    if os.environ.get("TEST_DATABASE_URL", "").startswith("postgresql"):
        obj = MachineFault(
            id=uuid.uuid4(),
            machine_status="Fault",
            downtime=-5.0,
        )
        db.add(obj)
        with pytest.raises(IntegrityError):
            db.flush()
    else:
        pytest.skip("CHECK constraint enforcement requires PostgreSQL")
