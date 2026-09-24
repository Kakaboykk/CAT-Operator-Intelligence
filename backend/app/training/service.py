"""
Service layer for Training Hub.
Handles CRUD and Quiz Grading transactions.
"""
from typing import List, Dict, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.training import (
    TrainingModule, 
    TrainingQuestion, 
    OperatorTrainingProgress, 
    OperatorTrainingAttempt
)
from app.models.incident import Incident
from app.schemas.training import (
    QuizSubmission, 
    QuizResultResponse, 
    QuizGradedQuestion, 
    TrainingHistoryItem,
    OperatorTrainingProgressResponse
)


def get_all_modules(db: Session) -> List[TrainingModule]:
    return db.query(TrainingModule).all()


def get_module_by_id(db: Session, module_id: UUID) -> TrainingModule:
    return db.query(TrainingModule).filter(TrainingModule.module_id == module_id).first()


def start_module(db: Session, operator_id: str, module_id: UUID) -> OperatorTrainingProgress:
    """
    Mark a module as IN_PROGRESS if not already started.
    """
    progress = db.query(OperatorTrainingProgress).filter(
        OperatorTrainingProgress.operator_id == operator_id,
        OperatorTrainingProgress.module_id == module_id
    ).first()

    if not progress:
        progress = OperatorTrainingProgress(
            operator_id=operator_id,
            module_id=module_id,
            status="IN_PROGRESS",
            first_started_at=datetime.now(timezone.utc)
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    elif progress.status == "NOT_STARTED":
        progress.status = "IN_PROGRESS"
        progress.first_started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(progress)
        
    return progress


def grade_quiz(db: Session, operator_id: str, module_id: UUID, submission: QuizSubmission) -> QuizResultResponse:
    """
    Grade the quiz server-side and safely save the attempt/progress in a single transaction.
    """
    # Find all questions for this module
    questions = db.query(TrainingQuestion).filter(TrainingQuestion.module_id == module_id).all()
    if not questions:
        raise ValueError("Module has no questions")

    correct_count = 0
    results = []

    # Grade each question
    for q in questions:
        q_id_str = str(q.question_id)
        selected = submission.answers.get(q_id_str, "")
        is_correct = (selected == q.correct_answer)
        if is_correct:
            correct_count += 1
            
        results.append(
            QuizGradedQuestion(
                question_id=q.question_id,
                is_correct=is_correct,
                selected_answer=selected,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            )
        )

    score_pct = int((correct_count / len(questions)) * 100)
    passed = score_pct >= 80  # Assume 80% is passing

    # TRANSACTIONAL SAVE
    # Ensure progress record exists
    progress = db.query(OperatorTrainingProgress).filter(
        OperatorTrainingProgress.operator_id == operator_id,
        OperatorTrainingProgress.module_id == module_id
    ).first()

    if not progress:
        progress = OperatorTrainingProgress(
            operator_id=operator_id,
            module_id=module_id,
            first_started_at=datetime.now(timezone.utc)
        )
        db.add(progress)

    # Append-only attempt log
    attempt = OperatorTrainingAttempt(
        progress=progress,
        score=score_pct,
        started_at=progress.first_started_at or datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    db.add(attempt)

    # Update summary row
    progress.attempt_count += 1
    if score_pct > progress.best_score:
        progress.best_score = score_pct

    if passed:
        progress.status = "COMPLETED"
        progress.last_completed_at = datetime.now(timezone.utc)

    # Single commit ensures attempt and progress are atomically saved together
    db.commit()

    return QuizResultResponse(
        score=score_pct,
        passed=passed,
        results=results
    )


def get_progress(db: Session, operator_id: str, recommended_count: int) -> OperatorTrainingProgressResponse:
    records = db.query(OperatorTrainingProgress).filter(OperatorTrainingProgress.operator_id == operator_id).all()
    
    completed = 0
    in_progress = 0
    
    for r in records:
        if r.status == "COMPLETED":
            completed += 1
        elif r.status == "IN_PROGRESS":
            in_progress += 1
            
    # Calculate estimated training time based on completed modules
    time_minutes = 0
    if completed > 0:
        completed_modules = db.query(TrainingModule).filter(
            TrainingModule.module_id.in_([r.module_id for r in records if r.status == "COMPLETED"])
        ).all()
        time_minutes = sum([m.duration_minutes for m in completed_modules])
        
    return OperatorTrainingProgressResponse(
        completed=completed,
        in_progress=in_progress,
        recommended=recommended_count,
        training_time_minutes=time_minutes
    )


def get_history(db: Session, operator_id: str) -> List[TrainingHistoryItem]:
    records = db.query(OperatorTrainingProgress).filter(
        OperatorTrainingProgress.operator_id == operator_id,
        OperatorTrainingProgress.status == "COMPLETED"
    ).all()
    
    history = []
    for r in records:
        if r.module:
            history.append(
                TrainingHistoryItem(
                    module_title=r.module.title,
                    date=r.last_completed_at,
                    score=r.best_score,
                    status=r.status
                )
            )
            
    # Sort descending by date
    history.sort(key=lambda x: x.date, reverse=True)
    return history
