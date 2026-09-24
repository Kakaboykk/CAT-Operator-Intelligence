"""
Pydantic v2 schemas for Telemetry.

Validates:
  - timestamp valid
  - machine_id present
  - operator_id present
  - engine_hours numeric
  - fuel_used numeric
  - load_cycles numeric
  - idling_time numeric
  - seatbelt_status valid string
  - safety_alert_triggered valid boolean
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid seatbelt status values accepted from source data.
VALID_SEATBELT_STATUSES = frozenset({"Fastened", "Unfastened"})


class TelemetryBase(BaseModel):
    """Fields common to create and read schemas."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(..., description="Source: Timestamp")
    machine_id: str = Field(..., min_length=1, description="Source: Machine ID")
    operator_id: str = Field(..., min_length=1, description="Source: Operator ID")
    engine_hours: float = Field(..., ge=0, description="Source: Engine Hours (hours)")
    fuel_used: float = Field(..., ge=0, description="Source: Fuel Used")
    load_cycles: int = Field(..., ge=0, description="Source: Load Cycles")
    idling_time: float = Field(..., ge=0, description="Source: Idling Time (minutes)")
    seatbelt_status: str = Field(..., description="Source: Seatbelt Status")
    safety_alert_triggered: bool = Field(
        ..., description="Source: Safety Alert Triggered"
    )

    @field_validator("seatbelt_status")
    @classmethod
    def validate_seatbelt_status(cls, v: str) -> str:
        if v not in VALID_SEATBELT_STATUSES:
            raise ValueError(
                f"seatbelt_status must be one of {sorted(VALID_SEATBELT_STATUSES)}, "
                f"got '{v}'"
            )
        return v

    @field_validator("machine_id", "operator_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class TelemetryCreate(TelemetryBase):
    """Schema used when inserting a new telemetry record."""


class TelemetryRead(TelemetryBase):
    """Schema returned when reading a telemetry record."""

    id: object  # UUID
