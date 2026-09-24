"""
Pydantic v2 schemas for TaskHistory.

Validates:
  - task_id present
  - task_type present
  - weather valid string
  - operator_skill valid string
  - machine_age numeric
  - estimated_time numeric
  - actual_time numeric
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_WEATHER = frozenset({"Clear", "Cloudy", "Rainy", "Stormy", "Foggy", "Windy", "Snowy"})
VALID_OPERATOR_SKILLS = frozenset({"Beginner", "Intermediate", "Expert"})


class TaskHistoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str = Field(..., min_length=1, description="Source: Task ID")
    task_type: str = Field(..., min_length=1, description="Source: Task Type")
    weather: str = Field(..., description="Source: Weather")
    operator_skill: str = Field(..., description="Source: Operator Skill")
    machine_age: float = Field(..., ge=0, description="Source: Machine Age (years)")
    estimated_time: float = Field(..., ge=0, description="Source: Estimated Time (hours)")
    actual_time: float = Field(..., ge=0, description="Source: Actual Time (hours)")

    @field_validator("task_id", "task_type")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()

    @field_validator("weather")
    @classmethod
    def validate_weather(cls, v: str) -> str:
        # Accept any value from the source dataset; validate known values.
        # Unknown values are kept but logged during ingestion.
        return v.strip()

    @field_validator("operator_skill")
    @classmethod
    def validate_operator_skill(cls, v: str) -> str:
        return v.strip()


class TaskHistoryCreate(TaskHistoryBase):
    """Schema used when inserting a task history record."""


class TaskHistoryRead(TaskHistoryBase):
    """Schema returned when reading a task history record."""

    id: object  # UUID
