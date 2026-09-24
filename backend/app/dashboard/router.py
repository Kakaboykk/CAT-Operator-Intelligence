"""
FastAPI router for Dashboard Shell backend.
Fetches real data from existing DB tables.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.daily_task import DailyTaskSchedule
from app.models.machine_fault import MachineFault
from app.models.incident import Incident
from app.schemas.dashboard import DashboardStatusResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/{operator_id}", response_model=DashboardStatusResponse)
def get_dashboard_status(operator_id: str, db: Session = Depends(get_db)):
    """
    Returns real fetched data for the dashboard shell.
    """
    resp = DashboardStatusResponse(operator_id=operator_id)
    
    # 1. Current Task (from daily_task_schedule)
    # We look for a scheduled or in-progress task for this operator
    task_sched = db.query(DailyTaskSchedule).filter(
        DailyTaskSchedule.operator_id == operator_id,
        DailyTaskSchedule.task_status.in_(["Scheduled", "In Progress"])
    ).order_by(DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).first()
    
    if task_sched and task_sched.task:
        resp.current_task_title = task_sched.task.task_type
        resp.current_task_time = f"{task_sched.scheduled_date} {task_sched.scheduled_time}"
        
        # 2. Machine Status (from machine_fault for the assigned machine)
        # Find the latest fault record for this machine_id's tasks
        # (This is an approximation using the current task's machine context)
        # In a real system, we'd query by machine_id, but machine_fault maps to task_id.
        # So we check if the current task has a fault:
        machine_fault = db.query(MachineFault).filter(
            MachineFault.task_id == task_sched.task_id
        ).order_by(desc(MachineFault.id)).first()
        
        if machine_fault:
            resp.machine_status = machine_fault.machine_status
        else:
            resp.machine_status = "Operational"
            
    # 3. Safety Status (from incident)
    # Get the highest severity incident from the operator's history
    incident = db.query(Incident).filter(
        Incident.operator_id == operator_id
    ).order_by(
        # In a strict DB we'd use a case statement for severity ranking, 
        # but for simplicity we just grab the most recent.
        desc(Incident.timestamp)
    ).first()
    
    if incident:
        resp.safety_status = incident.severity
    else:
        resp.safety_status = "Excellent"
        
    return resp
