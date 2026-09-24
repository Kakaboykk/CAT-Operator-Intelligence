"""
ORM model: DailyTaskSchedule

Column mapping (specification → internal):
  Schedule ID    → schedule_id
  Task ID        → task_id
  Operator ID    → operator_id
  Machine ID     → machine_id
  Scheduled Date → scheduled_date
  Scheduled Time → scheduled_time
  Task Status    → task_status

Purpose:
  Represents the CAT operator's scheduled daily work.
  Later phases will use this to populate "Today's Tasks" and
  "Current Task" on the operator interface.

Phase 1 scope:
  - Schema defined.
  - Relationships/references defined.
  - Fields validated.
  - Ready for data insertion by later phases.
  - Do NOT build dashboard or task-assignment UI here.
"""

import uuid

from sqlalchemy import Column, Date, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DailyTaskSchedule(Base):
    """
    One row = one scheduled task slot in an operator's daily schedule.
    """

    __tablename__ = "daily_task_schedule"

    # ── Primary key (also maps to "Schedule ID") ──────────────────────────────
    schedule_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Specification field: Schedule ID — unique schedule entry",
    )

    # ── Source: "Task ID" ─────────────────────────────────────────────────────
    # String FK referencing task_history.task_id
    task_id = Column(
        String(100),
        ForeignKey("task_history.task_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Specification field: Task ID — links to task_history.task_id",
    )

    # ── Source: "Operator ID" ─────────────────────────────────────────────────
    operator_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Specification field: Operator ID",
    )

    # ── Source: "Machine ID" ──────────────────────────────────────────────────
    machine_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Specification field: Machine ID",
    )

    # ── Source: "Scheduled Date" ──────────────────────────────────────────────
    scheduled_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Specification field: Scheduled Date — calendar date of the task",
    )

    # ── Source: "Scheduled Time" ──────────────────────────────────────────────
    scheduled_time = Column(
        Time,
        nullable=False,
        comment="Specification field: Scheduled Time — start time of the task",
    )

    # ── Source: "Task Status" ─────────────────────────────────────────────────
    task_status = Column(
        String(50),
        nullable=False,
        default="Scheduled",
        comment=(
            "Specification field: Task Status — "
            "e.g. 'Scheduled', 'In Progress', 'Completed', 'Cancelled'"
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    task = relationship(
        "TaskHistory",
        foreign_keys=[task_id],
        primaryjoin="DailyTaskSchedule.task_id == TaskHistory.task_id",
        backref="schedule_entries",
    )

    def __repr__(self) -> str:
        return (
            f"<DailyTaskSchedule schedule_id={self.schedule_id} "
            f"task_id={self.task_id} operator={self.operator_id} "
            f"date={self.scheduled_date} status={self.task_status}>"
        )
