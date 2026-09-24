"""
Pydantic v2 schemas for MachineFault.

Validates:
  - task_id valid (optional reference)
  - machine_status valid string
  - fault_type valid string (optional when operational)
  - downtime numeric and non-negative
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_MACHINE_STATUSES = frozenset({"Operational", "Fault", "Maintenance", "Offline"})


class MachineFaultBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str | None = Field(None, description="Source: Task ID (optional)")
    machine_status: str = Field(..., description="Source: Machine Status")
    fault_type: str | None = Field(None, description="Source: Fault Type (null when operational)")
    downtime: float = Field(..., ge=0, description="Source: Downtime (minutes, must be >= 0)")

    @field_validator("machine_status")
    @classmethod
    def validate_machine_status(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("machine_status must not be blank")
        return stripped

    @field_validator("fault_type")
    @classmethod
    def validate_fault_type(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip() or None
        return v


class MachineFaultCreate(MachineFaultBase):
    """Schema used when inserting a machine fault record."""


class MachineFaultRead(MachineFaultBase):
    """Schema returned when reading a machine fault record."""

    id: object  # UUID
