"""
ORM model: Telemetry

Source dataset: Company Telemetry CSV
Column mapping (source → internal):
  Timestamp              → timestamp
  Machine ID             → machine_id
  Operator ID            → operator_id
  Engine Hours           → engine_hours
  Fuel Used              → fuel_used
  Load Cycles            → load_cycles
  Idling Time            → idling_time
  Seatbelt Status        → seatbelt_status
  Safety Alert Triggered → safety_alert_triggered
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Telemetry(Base):
    """
    One row = one telemetry reading from a CAT machine operator session.

    This table contains ONLY real company-provided fields.
    Do NOT add synthetic or ML-generated fields here.
    """

    __tablename__ = "telemetry"

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Surrogate primary key (UUID v4)",
    )

    # ── Source: "Timestamp" ───────────────────────────────────────────────────
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Source field: Timestamp",
    )

    # ── Source: "Machine ID" ──────────────────────────────────────────────────
    machine_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Source field: Machine ID",
    )

    # ── Source: "Operator ID" ─────────────────────────────────────────────────
    operator_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Source field: Operator ID",
    )

    # ── Source: "Engine Hours" ────────────────────────────────────────────────
    engine_hours = Column(
        Float,
        nullable=False,
        comment="Source field: Engine Hours — cumulative engine run-time in hours",
    )

    # ── Source: "Fuel Used" ───────────────────────────────────────────────────
    fuel_used = Column(
        Float,
        nullable=False,
        comment="Source field: Fuel Used — fuel consumed (litres or unit from source)",
    )

    # ── Source: "Load Cycles" ─────────────────────────────────────────────────
    load_cycles = Column(
        Integer,
        nullable=False,
        comment="Source field: Load Cycles — number of load/dump cycles",
    )

    # ── Source: "Idling Time" ─────────────────────────────────────────────────
    idling_time = Column(
        Float,
        nullable=False,
        comment="Source field: Idling Time — idle duration in minutes",
    )

    # ── Source: "Seatbelt Status" ─────────────────────────────────────────────
    seatbelt_status = Column(
        String(50),
        nullable=False,
        comment="Source field: Seatbelt Status — e.g. 'Fastened', 'Unfastened'",
    )

    # ── Source: "Safety Alert Triggered" ─────────────────────────────────────
    safety_alert_triggered = Column(
        Boolean,
        nullable=False,
        comment="Source field: Safety Alert Triggered — True/False",
    )

    def __repr__(self) -> str:
        return (
            f"<Telemetry id={self.id} machine={self.machine_id} "
            f"operator={self.operator_id} ts={self.timestamp}>"
        )
