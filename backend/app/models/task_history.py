"""
ORM model: TaskHistory

Source dataset: Company Task History CSV
Column mapping (source → internal):
  Task ID        → task_id
  Task Type      → task_type
  Weather        → weather
  Operator Skill → operator_skill
  Machine Age    → machine_age
  Estimated Time → estimated_time
  Actual Time    → actual_time

IMPORTANT:
  Do NOT add ML predictions, predicted_duration, or confidence
  intervals to this table. Those belong to Phase 4.
"""

import uuid

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TaskHistory(Base):
    """
    One row = one completed task record from the company dataset.

    Contains ONLY the real company-provided fields.
    """

    __tablename__ = "task_history"

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Surrogate primary key (UUID v4)",
    )

    # ── Source: "Task ID" ─────────────────────────────────────────────────────
    task_id = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Source field: Task ID — business task identifier",
    )

    # ── Source: "Task Type" ───────────────────────────────────────────────────
    task_type = Column(
        String(200),
        nullable=False,
        comment="Source field: Task Type — category of work performed",
    )

    # ── Source: "Weather" ─────────────────────────────────────────────────────
    weather = Column(
        String(100),
        nullable=False,
        comment="Source field: Weather — conditions during the task",
    )

    # ── Source: "Operator Skill" ──────────────────────────────────────────────
    operator_skill = Column(
        String(100),
        nullable=False,
        comment="Source field: Operator Skill — e.g. 'Beginner', 'Intermediate', 'Expert'",
    )

    # ── Source: "Machine Age" ─────────────────────────────────────────────────
    machine_age = Column(
        Float,
        nullable=False,
        comment="Source field: Machine Age — age of the machine in years",
    )

    # ── Source: "Estimated Time" ──────────────────────────────────────────────
    estimated_time = Column(
        Float,
        nullable=False,
        comment="Source field: Estimated Time — planned task duration (hours)",
    )

    # ── Source: "Actual Time" ─────────────────────────────────────────────────
    actual_time = Column(
        Float,
        nullable=False,
        comment="Source field: Actual Time — real task duration (hours)",
    )

    def __repr__(self) -> str:
        return (
            f"<TaskHistory id={self.id} task_id={self.task_id} "
            f"type={self.task_type}>"
        )
