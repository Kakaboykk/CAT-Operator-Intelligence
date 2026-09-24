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
from app.models.task_history import TaskHistory
from app.schemas.dashboard import DashboardStatusResponse
from app.ml.predict import TaskPredictionService
import numpy as np
from datetime import datetime, timedelta

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
        DailyTaskSchedule.task_status.in_(["UPCOMING", "CURRENT"])
    ).order_by(DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).first()
    
    if task_sched and task_sched.task:
        resp.current_task_title = task_sched.task.task_type
        resp.current_task_time = f"{task_sched.scheduled_date} {task_sched.scheduled_time}"
        
        # Calculate ETA
        t_time = datetime.combine(task_sched.scheduled_date, task_sched.scheduled_time)
        resp.scheduled_start_time = t_time.strftime("%H:%M")
        
        # Past tasks for operator
        past_schedules = db.query(TaskHistory.actual_time, DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).join(
            DailyTaskSchedule, TaskHistory.task_id == DailyTaskSchedule.task_id
        ).filter(
            TaskHistory.operator_id == operator_id
        ).all()
        
        past_times = []
        for pt in past_schedules:
            dt = datetime.combine(pt.scheduled_date, pt.scheduled_time)
            if dt < t_time:
                past_times.append(pt.actual_time)
        
        op_avg_time = sum(past_times) / len(past_times) if past_times else np.nan
        
        # Past incidents for operator
        past_incidents = db.query(Incident.timestamp).filter(
            Incident.operator_id == operator_id
        ).all()
        op_inc_count = sum(1 for i in past_incidents if i.timestamp.replace(tzinfo=None) < t_time)
        
        # Past faults for machine
        past_faults = db.query(DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).join(
            MachineFault, MachineFault.task_id == DailyTaskSchedule.task_id
        ).filter(
            DailyTaskSchedule.machine_id == task_sched.machine_id,
            MachineFault.machine_status != 'NORMAL'
        ).all()
        mac_fault_count = sum(1 for f in past_faults if datetime.combine(f.scheduled_date, f.scheduled_time) < t_time)
        
        task_features = {
            "estimated_time": task_sched.task.estimated_time,
            "task_type": task_sched.task.task_type,
            "weather": task_sched.task.weather,
            "operator_skill": task_sched.task.operator_skill,
            "machine_age": task_sched.task.machine_age,
            "operator_id": task_sched.operator_id,
            "machine_id": task_sched.machine_id,
            "operator_historical_avg_time": op_avg_time,
            "operator_historical_incident_count": op_inc_count,
            "machine_historical_fault_count": mac_fault_count,
        }
        
        try:
            predictor = TaskPredictionService()
            pred_res = predictor.predict(task_features)
            predicted_duration_hours = pred_res["predicted_duration"]
            predicted_duration_minutes = max(0, int(round(predicted_duration_hours * 60)))
            
            planned_duration_minutes = int(round(task_sched.task.estimated_time * 60))
            expected_finish_time = t_time + timedelta(minutes=predicted_duration_minutes)
            
            resp.planned_duration_minutes = planned_duration_minutes
            resp.predicted_duration_minutes = predicted_duration_minutes
            resp.expected_finish_time = expected_finish_time.strftime("%H:%M")
            
            duration_diff = predicted_duration_minutes - planned_duration_minutes
            resp.duration_difference_minutes = duration_diff
            
            if duration_diff > 0:
                resp.task_timing_status = "LONGER_THAN_PLANNED"
            elif duration_diff < 0:
                resp.task_timing_status = "SHORTER_THAN_PLANNED"
            else:
                resp.task_timing_status = "ON_PLAN"
                
        except Exception as e:
            # If model fails, leave fields as None (null in JSON)
            print(f"Prediction error: {e}")
        
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
            if machine_fault.machine_status in ("DEGRADED", "UNAVAILABLE"):
                resp.fault_type = machine_fault.fault_type
                resp.machine_downtime_minutes = int(round(machine_fault.downtime_minutes))
        else:
            resp.machine_status = "NORMAL"
            
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
