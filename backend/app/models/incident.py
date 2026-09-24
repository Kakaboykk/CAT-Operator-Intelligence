"""
ORM model: Incident

Phase 1 — Schema only.
Column mapping (specification → internal):
  Incident ID  → incident_id
  Timestamp    → timestamp
  Operator ID  → operator_id
  Machine ID   → machine_id
  Event Type   → event_type
  Severity     → severity
  Description  → description
  Status       → status

IMPORTANT — Phase 1 scope:
  This table is schema-only.
  Do NOT automatically create incidents.
  Do NOT implement the seatbelt rule.
  Do NOT implement weather severity adjustment.
  Do NOT implement alert generation.
  Phase 3 will write records into this table.
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Incident(Base):
    """
    One row = one safety/operational incident record.

    Ready for Phase 3 to write records; Phase 1 only defines the schema.
    """

    __tablename__ = "incident"

    # ── Primary key (also maps to "Incident ID") ──────────────────────────────
    incident_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Specification field: Incident ID — unique incident identifier",
    )

    # ── Source: "Timestamp" ───────────────────────────────────────────────────
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Specification field: Timestamp — when the incident occurred",
    )

    # ── Source: "Operator ID" ─────────────────────────────────────────────────
    operator_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Specification field: Operator ID — may be null if not yet identified",
    )

    # ── Source: "Machine ID" ──────────────────────────────────────────────────
    machine_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Specification field: Machine ID — may be null if not yet identified",
    )

    # ── Source: "Event Type" ──────────────────────────────────────────────────
    event_type = Column(
        String(200),
        nullable=False,
        comment="Specification field: Event Type — category of event",
    )

    # ── Source: "Severity" ────────────────────────────────────────────────────
    severity = Column(
        String(50),
        nullable=False,
        comment="Specification field: Severity — e.g. 'Low', 'Medium', 'High', 'Critical'",
    )

    # ── Source: "Description" ─────────────────────────────────────────────────
    description = Column(
        Text,
        nullable=True,
        comment="Specification field: Description — free-text event description",
    )

    # ── Source: "Status" ──────────────────────────────────────────────────────
    status = Column(
        String(50),
        nullable=False,
        default="Active",
        comment="Specification field: Status — e.g. 'Active', 'Resolved', 'Historical'",
    )

    def __repr__(self) -> str:
        return (
            f"<Incident incident_id={self.incident_id} "
            f"event_type={self.event_type} severity={self.severity} "
            f"status={self.status}>"
        )
