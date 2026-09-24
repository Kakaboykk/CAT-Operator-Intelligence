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
    safety_status: Optional[str] = None
