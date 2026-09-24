import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from app.main import app
from app.core.database import Base, get_db
from app.models.daily_task import DailyTaskSchedule
from app.models.task_history import TaskHistory
from app.models.incident import Incident
from app.models.machine_fault import MachineFault
from unittest.mock import patch, MagicMock

# Create a test client
client = TestClient(app)

def test_dashboard_status_no_task():
    # If there is no task for the operator, the endpoint should return no ETA fields.
    response = client.get("/api/dashboard/NON_EXISTENT_OP")
    assert response.status_code == 200
    data = response.json()
    assert data["operator_id"] == "NON_EXISTENT_OP"
    assert data["current_task_title"] is None
    assert data["scheduled_start_time"] is None
    assert data["predicted_duration_minutes"] is None
    assert data["expected_finish_time"] is None
    assert data["task_timing_status"] is None

@patch("app.dashboard.router.TaskPredictionService")
def test_dashboard_status_with_task_and_prediction(MockTaskPredictionService, db):
    # Setup mock predictor
    mock_instance = MockTaskPredictionService.return_value
    mock_instance.predict.return_value = {
        "predicted_duration": 1.5, # 1.5 hours = 90 minutes
        "unit": "hours",
        "model": "Mock",
        "important_features": []
    }
    
    # Create test data
    op_id = "OP_TEST"
    
    task_hist = TaskHistory(
        task_id="TASK-999",
        machine_id="MACH-1",
        operator_id=op_id,
        task_type="Testing",
        weather="Clear",
        operator_skill="Expert",
        machine_age=2.0,
        estimated_time=1.0, # 1 hour = 60 minutes
        actual_time=1.0
    )
    db.add(task_hist)
    
    sched = DailyTaskSchedule(
        task_id="TASK-999",
        operator_id=op_id,
        machine_id="MACH-1",
        scheduled_date=datetime.date(2026, 10, 1),
        scheduled_time=datetime.time(10, 30),
        task_status="CURRENT"
    )
    db.add(sched)
    db.commit()
    
    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: db
    
    response = client.get(f"/api/dashboard/{op_id}")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["operator_id"] == op_id
    assert data["current_task_title"] == "Testing"
    assert data["scheduled_start_time"] == "10:30"
    
    # ETA fields
    assert data["planned_duration_minutes"] == 60
    assert data["predicted_duration_minutes"] == 90
    assert data["duration_difference_minutes"] == 30 # 90 - 60
    
    # expected_finish = 10:30 + 90 min = 12:00
    assert data["expected_finish_time"] == "12:00"
    assert data["task_timing_status"] == "LONGER_THAN_PLANNED"
    
    # Verify mock was called
    mock_instance.predict.assert_called_once()
    
    # Verify no data leakage in args passed to predict
    call_args = mock_instance.predict.call_args[0][0]
    assert "actual_time" not in call_args
    assert call_args["estimated_time"] == 1.0
    assert call_args["task_type"] == "Testing"
    assert call_args["operator_id"] == op_id

