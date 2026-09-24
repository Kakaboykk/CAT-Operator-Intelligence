"""
Tests for Phase 2 Synthetic Data Generation.
"""
import pytest
from sqlalchemy import text
from app.data_generation.generator import SyntheticDataGenerator
from app.models.task_history import TaskHistory
from app.models.telemetry import Telemetry
from app.models.machine_fault import MachineFault
from app.models.daily_task import DailyTaskSchedule
from app.models.incident import Incident
from app.data_generation.db_operations import reset_phase2_data, bulk_insert_generated_data

def test_deterministic_generation():
    """Verify that using the same seed produces exactly the same data."""
    gen1 = SyntheticDataGenerator(seed=42, days=5)
    t1, f1, s1, tel1 = gen1.generate()
    
    gen2 = SyntheticDataGenerator(seed=42, days=5)
    t2, f2, s2, tel2 = gen2.generate()
    
    assert len(t1) == len(t2)
    assert len(f1) == len(f2)
    assert len(s1) == len(s2)
    assert len(tel1) == len(tel2)
    
    # Check IDs
    assert t1[0].id == t2[0].id
    assert tel1[0].id == tel2[0].id

def test_different_seeds_produce_different_data():
    gen1 = SyntheticDataGenerator(seed=42, days=2)
    t1, _, _, _ = gen1.generate()
    
    gen2 = SyntheticDataGenerator(seed=43, days=2)
    t2, _, _, _ = gen2.generate()
    
    assert t1[0].id != t2[0].id

def test_generation_insertion_db(db):
    """Test generating and inserting to the DB, ensuring no orphan FKs and basic properties."""
    # Start clean
    reset_phase2_data(db)
    
    gen = SyntheticDataGenerator(seed=99, days=3)
    tasks, faults, schedules, telemetries = gen.generate()
    
    all_records = tasks + faults + schedules + telemetries
    bulk_insert_generated_data(db, all_records)
    
    # Check rows inserted
    assert db.query(TaskHistory).count() == len(tasks)
    assert db.query(MachineFault).count() == len(faults)
    assert db.query(DailyTaskSchedule).count() == len(schedules)
    assert db.query(Telemetry).count() == len(telemetries)
    
    # 12. Check Incident is empty
    assert db.query(Incident).count() == 0

    # Ensure engine_hours is non-negative and growing
    machine_tels = db.query(Telemetry).filter_by(machine_id="EXC001").order_by(Telemetry.timestamp).all()
    if machine_tels:
        assert machine_tels[0].engine_hours >= 0
        if len(machine_tels) > 1:
            assert machine_tels[-1].engine_hours > machine_tels[0].engine_hours

def test_causal_delay():
    """Verify that faults increase actual time over estimated time."""
    gen = SyntheticDataGenerator(seed=42, days=30)
    tasks, faults, schedules, telemetries = gen.generate()
    
    faults_by_task = {f.task_id: f for f in faults}
    
    faulted_tasks = []
    normal_tasks = []
    for t in tasks:
        f = faults_by_task.get(t.task_id)
        if f and f.machine_status == "Fault":
            faulted_tasks.append(t)
        else:
            normal_tasks.append(t)
            
    # Calculate average variance
    faulted_var = sum(t.actual_time - t.estimated_time for t in faulted_tasks) / len(faulted_tasks)
    normal_var = sum(t.actual_time - t.estimated_time for t in normal_tasks) / len(normal_tasks)
    
    assert faulted_var > normal_var
