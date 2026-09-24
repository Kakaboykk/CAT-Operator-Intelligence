"""
Pydantic schemas for Phase 5 Dashboard APIs.
"""
from pydantic import BaseModel
from typing import Optional

class DashboardStatusResponse(BaseModel):
    """
    Combines Real data for the Dashboard Shell.
    """
    operator_id: str
    current_task_title: Optional[str] = None
    current_task_time: Optional[str] = None
    machine_status: Optional[str] = None
    fault_type: Optional[str] = None
    machine_downtime_minutes: Optional[int] = None
    safety_status: Optional[str] = None
    
    # Task + ETA functionality fields
    scheduled_start_time: Optional[str] = None
    planned_duration_minutes: Optional[int] = None
    predicted_duration_minutes: Optional[int] = None
    expected_finish_time: Optional[str] = None
    duration_difference_minutes: Optional[int] = None
    task_timing_status: Optional[str] = None
