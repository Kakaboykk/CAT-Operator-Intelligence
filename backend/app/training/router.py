"""
FastAPI router for Training Hub endpoints.
Uses established get_db dependency.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.schemas.training import (
    TrainingModuleResponse,
    TrainingRecommendation,
    OperatorTrainingProgressResponse,
    TrainingHistoryItem,
    QuizSubmission,
    QuizResultResponse
)
from app.training import service, recommendations

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/modules", response_model=List[TrainingModuleResponse])
def get_modules(db: Session = Depends(get_db)):
    """Return all available training modules (without questions)."""
    modules = service.get_all_modules(db)
    # Serialize ensuring questions are excluded in list view
    return [TrainingModuleResponse.model_validate(m) for m in modules]


@router.get("/modules/{module_id}", response_model=TrainingModuleResponse)
def get_module(module_id: UUID, db: Session = Depends(get_db)):
    """
    Return a specific module including its questions.
    The response schema TrainingQuestionPublic explicitly excludes correct_answer and explanation.
    """
    module = service.get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.get("/recommendations/{operator_id}", response_model=List[TrainingRecommendation])
def get_recommendations(operator_id: str, db: Session = Depends(get_db)):
    """Return deterministic training recommendations for an operator."""
    return recommendations.get_recommendations_for_operator(db, operator_id)


@router.get("/progress/{operator_id}", response_model=OperatorTrainingProgressResponse)
def get_progress(operator_id: str, db: Session = Depends(get_db)):
    """Return an operator's high-level training progress."""
    recs = recommendations.get_recommendations_for_operator(db, operator_id)
    return service.get_progress(db, operator_id, len(recs))


@router.post("/modules/{module_id}/start")
def start_module(module_id: UUID, operator_id: str, db: Session = Depends(get_db)):
    """Mark a module as started (IN_PROGRESS) for an operator."""
    module = service.get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    service.start_module(db, operator_id, module_id)
    return {"status": "started"}


@router.post("/modules/{module_id}/quiz", response_model=QuizResultResponse)
def submit_quiz(module_id: UUID, operator_id: str, submission: QuizSubmission, db: Session = Depends(get_db)):
    """
    Submit a quiz attempt.
    The server handles grading and atomically saves the attempt and progress.
    Returns the score and explanations for each question.
    """
    try:
        return service.grade_quiz(db, operator_id, module_id, submission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{operator_id}", response_model=List[TrainingHistoryItem])
def get_history(operator_id: str, db: Session = Depends(get_db)):
    """Return completed modules (history) for an operator."""
    return service.get_history(db, operator_id)
