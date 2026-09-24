"""
ORM models for Phase 5: Operator Training Hub
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrainingModule(Base):
    """
    One row = one available training module.
    """
    __tablename__ = "training_module"

    module_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key for the training module"
    )
    title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    difficulty = Column(String(50), nullable=False)
    
    questions = relationship("TrainingQuestion", back_populates="module", cascade="all, delete-orphan")
    progress_records = relationship("OperatorTrainingProgress", back_populates="module")


class TrainingQuestion(Base):
    """
    One row = one quiz question for a module.
    """
    __tablename__ = "training_question"

    question_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("training_module.module_id", ondelete="CASCADE"),
        nullable=False
    )
    question_text = Column(Text, nullable=False)
    # Storing options as JSON array
    options = Column(JSON, nullable=False)
    # The exact string matching one of the options
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)

    module = relationship("TrainingModule", back_populates="questions")


class OperatorTrainingProgress(Base):
    """
    Summary row of an operator's progress on a specific module.
    """
    __tablename__ = "operator_training_progress"

    progress_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    operator_id = Column(String(100), nullable=False, index=True)
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("training_module.module_id", ondelete="CASCADE"),
        nullable=False
    )
    status = Column(String(50), nullable=False, default="NOT_STARTED", comment="NOT_STARTED, IN_PROGRESS, COMPLETED")
    best_score = Column(Integer, nullable=False, default=0)
    attempt_count = Column(Integer, nullable=False, default=0)
    first_started_at = Column(DateTime(timezone=True), nullable=True)
    last_completed_at = Column(DateTime(timezone=True), nullable=True)

    module = relationship("TrainingModule", back_populates="progress_records")
    attempts = relationship("OperatorTrainingAttempt", back_populates="progress", cascade="all, delete-orphan")


class OperatorTrainingAttempt(Base):
    """
    Append-only log of quiz attempts.
    """
    __tablename__ = "operator_training_attempt"

    attempt_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    progress_id = Column(
        UUID(as_uuid=True),
        ForeignKey("operator_training_progress.progress_id", ondelete="CASCADE"),
        nullable=False
    )
    score = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    progress = relationship("OperatorTrainingProgress", back_populates="attempts")
