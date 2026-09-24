"""
Pydantic schemas for Phase 5 Training APIs.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID

class TrainingQuestionPublic(BaseModel):
    """
    Public representation of a question (NO correct_answer or explanation).
    """
    question_id: UUID
    question_text: str
    options: List[str]
    
    model_config = ConfigDict(from_attributes=True)

class TrainingModuleResponse(BaseModel):
    """
    Response schema for a training module overview.
    """
    module_id: UUID
    title: str
    category: str
    description: str
    duration_minutes: int
    difficulty: str
    questions: Optional[List[TrainingQuestionPublic]] = None
    
    model_config = ConfigDict(from_attributes=True)

class QuizSubmission(BaseModel):
    """
    Operator's answers for a quiz.
    Maps question_id (UUID as string) to selected answer string.
    """
    answers: Dict[str, str]

class QuizGradedQuestion(BaseModel):
    """
    Result for a single question after grading.
    """
    question_id: UUID
    is_correct: bool
    selected_answer: str
    correct_answer: str
    explanation: str

class QuizResultResponse(BaseModel):
    """
    The final graded result returned to the client.
    """
    score: int  # 0 to 100 percentage
    passed: bool
    results: List[QuizGradedQuestion]

class TrainingRecommendation(BaseModel):
    module: TrainingModuleResponse
    reason: str
    priority: str

class OperatorTrainingProgressResponse(BaseModel):
    completed: int
    in_progress: int
    recommended: int
    training_time_minutes: int

class TrainingHistoryItem(BaseModel):
    module_title: str
    date: datetime
    score: int
    status: str
