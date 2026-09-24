"""
ORM model: MachineFault

Schema specification (Phase 1 — Data Foundation only).
Column mapping (source → internal):
  Task ID        → task_id
  Machine Status → machine_status
  Fault Type     → fault_type
  Downtime       → downtime

IMPORTANT — Phase 1 scope:
  This is DATA FOUNDATION ONLY.
  Do NOT implement:
    - fault prediction
    - ML fault detection
    - automatic fault inference
    - fault severity intelligence
    - fault diagnosis
  The schema supports both normal-operation and fault-event rows.
  Example hard-coded events (e.g. Hydraulic Fault → 15 min) belong
  to Phase 2 synthetic-data generation, NOT here.
"""

import uuid

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MachineFault(Base):
    """
    One row = one machine fault or normal-operation record.

    References TaskHistory.task_id via a string foreign key so that
    faults can be associated with a specific task context.
    """

    __tablename__ = "machine_fault"

    __table_args__ = (
        CheckConstraint("downtime >= 0", name="ck_machine_fault_downtime_non_negative"),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Surrogate primary key (UUID v4)",
    )

    # ── Source: "Task ID" ─────────────────────────────────────────────────────
    # References TaskHistory.task_id (string business key, not UUID PK).
    # Nullable to allow fault records that arrive before task data is loaded.
    task_id = Column(
        String(100),
        ForeignKey("task_history.task_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source field: Task ID — links to task_history.task_id",
    )

    # ── Source: "Machine Status" ──────────────────────────────────────────────
    machine_status = Column(
        String(100),
        nullable=False,
        comment="Source field: Machine Status — e.g. 'Operational', 'Fault', 'Maintenance'",
    )

    # ── Source: "Fault Type" ──────────────────────────────────────────────────
    fault_type = Column(
        String(200),
        nullable=True,
        comment="Source field: Fault Type — null when machine_status is 'Operational'",
    )

    # ── Source: "Downtime" ────────────────────────────────────────────────────
    downtime = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Source field: Downtime — minutes of machine downtime (0 if operational)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    task = relationship(
        "TaskHistory",
        foreign_keys=[task_id],
        primaryjoin="MachineFault.task_id == TaskHistory.task_id",
        backref="machine_faults",
    )

    def __repr__(self) -> str:
        return (
            f"<MachineFault id={self.id} task_id={self.task_id} "
            f"status={self.machine_status} fault={self.fault_type}>"
        )
