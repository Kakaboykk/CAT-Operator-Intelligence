import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath("c:/Users/priti/Downloads/caterpillar/backend"))

from app.core.database import SessionLocal
from app.models.daily_task import DailyTaskSchedule
from app.models.task_history import TaskHistory

db = SessionLocal()
schedules = db.query(DailyTaskSchedule).all()
print("Schedules found:", len(schedules))
for s in schedules[:5]:
    print(s.operator_id, s.task_status, s.scheduled_date, s.scheduled_time)

tasks = db.query(TaskHistory).all()
print("Tasks found:", len(tasks))
db.close()
