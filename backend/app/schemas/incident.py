"""
Pydantic v2 schemas for Incident.

Validates:
  - incident_id unique (enforced at DB level)
  - timestamp valid
  - operator_id valid where provided
  - machine_id valid where provided
  - severity valid
  - status valid
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_SEVERITIES = frozenset({"Low", "Medium", "High", "Critical"})
VALID_STATUSES = frozenset({"Open", "Acknowledged", "Resolved"})


class IncidentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(..., description="Specification: Timestamp")
    operator_id: str | None = Field(None, description="Specification: Operator ID")
    machine_id: str | None = Field(None, description="Specification: Machine ID")
    event_type: str = Field(..., min_length=1, description="Specification: Event Type")
    severity: str = Field(..., description="Specification: Severity")
    description: str | None = Field(None, description="Specification: Description")
    status: str = Field(default="Open", description="Specification: Status")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(
                f"severity must be one of {sorted(VALID_SEVERITIES)}, got '{v}'"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(VALID_STATUSES)}, got '{v}'"
            )
        return v

    @field_validator("operator_id", "machine_id")
    @classmethod
    def validate_optional_id(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("ID field must not be blank if provided")
        return v.strip() if v else v


class IncidentCreate(IncidentBase):
    """Schema used when inserting a new incident."""


class IncidentRead(IncidentBase):
    """Schema returned when reading an incident."""

    incident_id: uuid.UUID
