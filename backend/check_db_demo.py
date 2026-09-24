from app.core.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
q = """SELECT s.task_id, s.operator_id, s.machine_id, s.task_status, f.machine_status, f.fault_type, f.downtime_minutes FROM daily_task_schedule s JOIN machine_fault f ON f.task_id = s.task_id WHERE s.task_status = 'CURRENT' AND f.machine_status IN ('DEGRADED', 'UNAVAILABLE')"""
result = db.execute(text(q)).fetchall()
for r in result:
    print(r)
