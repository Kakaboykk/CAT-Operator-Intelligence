"""
app/models/__init__.py

Exports all ORM models so that Alembic's autogenerate can discover them
via a single import of this package.
"""

from app.models.daily_task import DailyTaskSchedule
from app.models.incident import Incident
from app.models.machine_fault import MachineFault
from app.models.task_history import TaskHistory
from app.models.telemetry import Telemetry

__all__ = [
    "Telemetry",
    "TaskHistory",
    "MachineFault",
    "Incident",
    "DailyTaskSchedule",
]
