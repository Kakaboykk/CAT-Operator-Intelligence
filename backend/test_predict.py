import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath("c:/Users/priti/Downloads/caterpillar/backend"))

from app.core.database import SessionLocal
from app.models.daily_task import DailyTaskSchedule
from app.models.task_history import TaskHistory
from app.models.incident import Incident
from app.models.machine_fault import MachineFault
from app.ml.predict import TaskPredictionService
import numpy as np
from datetime import datetime

def test():
    db = SessionLocal()
    operator_id = "OP1003"
    
    task_sched = db.query(DailyTaskSchedule).filter(
        DailyTaskSchedule.operator_id == operator_id,
        DailyTaskSchedule.task_status.in_(["UPCOMING", "CURRENT"])
    ).order_by(DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).first()
    
    if not task_sched:
        print("No task schedule found.")
        return
        
    print(f"Task found: {task_sched.task.task_type} at {task_sched.scheduled_date} {task_sched.scheduled_time}")
    
    t_time = datetime.combine(task_sched.scheduled_date, task_sched.scheduled_time)
    print(f"t_time: {t_time}")
    
    # Past tasks
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
    print(f"Operator past avg time: {op_avg_time}")
    
    # Past incidents
    past_incidents = db.query(Incident.timestamp).filter(
        Incident.operator_id == operator_id
    ).all()
    # Handle timezone naive/aware based on DB
    op_inc_count = sum(1 for i in past_incidents if i.timestamp.replace(tzinfo=None) < t_time)
    print(f"Operator incident count: {op_inc_count}")
    
    # Past faults
    past_faults = db.query(DailyTaskSchedule.scheduled_date, DailyTaskSchedule.scheduled_time).join(
        MachineFault, MachineFault.task_id == DailyTaskSchedule.task_id
    ).filter(
        DailyTaskSchedule.machine_id == task_sched.machine_id,
        MachineFault.machine_status != 'NORMAL'
    ).all()
    
    mac_fault_count = sum(1 for f in past_faults if datetime.combine(f.scheduled_date, f.scheduled_time) < t_time)
    print(f"Machine fault count: {mac_fault_count}")
    
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
    print("Features:", task_features)
    
    predictor = TaskPredictionService()
    res = predictor.predict(task_features)
    print("Prediction:", res)
    
    db.close()

if __name__ == "__main__":
    test()
