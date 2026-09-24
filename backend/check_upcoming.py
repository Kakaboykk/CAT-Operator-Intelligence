import sys
import os

sys.path.insert(0, os.path.abspath("c:/Users/priti/Downloads/caterpillar/backend"))
from app.core.database import SessionLocal
from app.models.daily_task import DailyTaskSchedule

db = SessionLocal()
s = db.query(DailyTaskSchedule).filter(DailyTaskSchedule.task_status.in_(["UPCOMING", "CURRENT"])).all()
for x in s:
    print(x.operator_id, x.task_status)
db.close()
