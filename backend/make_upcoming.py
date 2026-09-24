import sys
import os

sys.path.insert(0, os.path.abspath("c:/Users/priti/Downloads/caterpillar/backend"))
from app.core.database import SessionLocal
from app.models.daily_task import DailyTaskSchedule

db = SessionLocal()
s = db.query(DailyTaskSchedule).filter(DailyTaskSchedule.operator_id == "OP1003").first()
if s:
    s.task_status = "UPCOMING"
    db.commit()
    print("Updated", s.operator_id, "to UPCOMING")
else:
    print("Not found")
db.close()
