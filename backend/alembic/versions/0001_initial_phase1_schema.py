"""Phase 1 initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-09-24 00:00:00.000000 UTC

Creates:
  - telemetry
  - task_history
  - machine_fault
  - incident
  - daily_task_schedule
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── task_history ──────────────────────────────────────────────────────────
    # Created first because machine_fault and daily_task_schedule reference it.
    op.create_table(
        "task_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Surrogate primary key (UUID v4)",
        ),
        sa.Column(
            "task_id",
            sa.String(100),
            nullable=False,
            unique=True,
            comment="Source field: Task ID — business task identifier",
        ),
        sa.Column("task_type", sa.String(200), nullable=False),
        sa.Column("weather", sa.String(100), nullable=False),
        sa.Column("operator_skill", sa.String(100), nullable=False),
        sa.Column("machine_age", sa.Float(), nullable=False),
        sa.Column("estimated_time", sa.Float(), nullable=False),
        sa.Column("actual_time", sa.Float(), nullable=False),
    )
    op.create_index("ix_task_history_task_id", "task_history", ["task_id"])

    # ── telemetry ─────────────────────────────────────────────────────────────
    op.create_table(
        "telemetry",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Surrogate primary key (UUID v4)",
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("machine_id", sa.String(100), nullable=False),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("engine_hours", sa.Float(), nullable=False),
        sa.Column("fuel_used", sa.Float(), nullable=False),
        sa.Column("load_cycles", sa.Integer(), nullable=False),
        sa.Column("idling_time", sa.Float(), nullable=False),
        sa.Column("seatbelt_status", sa.String(50), nullable=False),
        sa.Column("safety_alert_triggered", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_telemetry_timestamp", "telemetry", ["timestamp"])
    op.create_index("ix_telemetry_machine_id", "telemetry", ["machine_id"])
    op.create_index("ix_telemetry_operator_id", "telemetry", ["operator_id"])

    # ── machine_fault ─────────────────────────────────────────────────────────
    op.create_table(
        "machine_fault",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Surrogate primary key (UUID v4)",
        ),
        sa.Column(
            "task_id",
            sa.String(100),
            sa.ForeignKey("task_history.task_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("machine_status", sa.String(100), nullable=False),
        sa.Column("fault_type", sa.String(200), nullable=True),
        sa.Column("downtime", sa.Float(), nullable=False, server_default="0"),
        sa.CheckConstraint("downtime >= 0", name="ck_machine_fault_downtime_non_negative"),
    )
    op.create_index("ix_machine_fault_task_id", "machine_fault", ["task_id"])

    # ── incident ──────────────────────────────────────────────────────────────
    op.create_table(
        "incident",
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Specification field: Incident ID",
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operator_id", sa.String(100), nullable=True),
        sa.Column("machine_id", sa.String(100), nullable=True),
        sa.Column("event_type", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="Open"),
    )
    op.create_index("ix_incident_timestamp", "incident", ["timestamp"])
    op.create_index("ix_incident_operator_id", "incident", ["operator_id"])
    op.create_index("ix_incident_machine_id", "incident", ["machine_id"])

    # ── daily_task_schedule ───────────────────────────────────────────────────
    op.create_table(
        "daily_task_schedule",
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="Specification field: Schedule ID",
        ),
        sa.Column(
            "task_id",
            sa.String(100),
            sa.ForeignKey("task_history.task_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("operator_id", sa.String(100), nullable=False),
        sa.Column("machine_id", sa.String(100), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.Time(), nullable=False),
        sa.Column(
            "task_status",
            sa.String(50),
            nullable=False,
            server_default="Scheduled",
        ),
    )
    op.create_index("ix_daily_task_schedule_task_id", "daily_task_schedule", ["task_id"])
    op.create_index("ix_daily_task_schedule_operator_id", "daily_task_schedule", ["operator_id"])
    op.create_index("ix_daily_task_schedule_machine_id", "daily_task_schedule", ["machine_id"])
    op.create_index("ix_daily_task_schedule_scheduled_date", "daily_task_schedule", ["scheduled_date"])


def downgrade() -> None:
    op.drop_table("daily_task_schedule")
    op.drop_table("incident")
    op.drop_table("machine_fault")
    op.drop_table("telemetry")
    op.drop_table("task_history")
