"""
Pydantic v2 schemas for DailyTaskSchedule.

Validates:
  - schedule_id unique (enforced at DB level)
  - task_id valid
  - operator_id valid
  - machine_id valid
  - scheduled_date valid
  - scheduled_time valid
  - task_status valid
"""

import uuid
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_TASK_STATUSES = frozenset({"Scheduled", "In Progress", "Completed", "Cancelled"})


class DailyTaskScheduleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str = Field(..., min_length=1, description="Specification: Task ID")
    operator_id: str = Field(..., min_length=1, description="Specification: Operator ID")
    machine_id: str = Field(..., min_length=1, description="Specification: Machine ID")
    scheduled_date: date = Field(..., description="Specification: Scheduled Date")
    scheduled_time: time = Field(..., description="Specification: Scheduled Time")
    task_status: str = Field(
        default="Scheduled", description="Specification: Task Status"
    )

    @field_validator("task_id", "operator_id", "machine_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()

    @field_validator("task_status")
    @classmethod
    def validate_task_status(cls, v: str) -> str:
        if v not in VALID_TASK_STATUSES:
            raise ValueError(
                f"task_status must be one of {sorted(VALID_TASK_STATUSES)}, got '{v}'"
            )
        return v


class DailyTaskScheduleCreate(DailyTaskScheduleBase):
    """Schema used when inserting a new schedule entry."""


class DailyTaskScheduleRead(DailyTaskScheduleBase):
    """Schema returned when reading a schedule entry."""

    schedule_id: uuid.UUID
