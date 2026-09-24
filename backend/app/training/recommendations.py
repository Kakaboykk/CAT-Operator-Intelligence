"""
Deterministic Recommendation Engine.
Links Phase 3 Incidents to Phase 5 Training Modules.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.incident import Incident
from app.models.training import TrainingModule
from app.schemas.training import TrainingRecommendation, TrainingModuleResponse

def get_recommendations_for_operator(db: Session, operator_id: str) -> List[TrainingRecommendation]:
    """
    Evaluates Phase 3 incidents to deterministically recommend training.
    """
    recommendations = []
    
    # Check for Seatbelt Violations
    seatbelt_count = db.query(Incident).filter(
        Incident.operator_id == operator_id,
        Incident.event_type == 'SEATBELT_VIOLATION'
    ).count()
    
    if seatbelt_count > 0:
        # Find the Seatbelt Safety module
        module = db.query(TrainingModule).filter(
            TrainingModule.category == 'Seatbelt Safety'
        ).first()
        
        if module:
            # Determine Priority based on count or severity
            priority = "HIGH" if seatbelt_count > 2 else "MEDIUM"
            
            # Serialize for response
            module_resp = TrainingModuleResponse.model_validate(module)
            # Ensure questions aren't included in the overview recommendation
            module_resp.questions = None
            
            rec = TrainingRecommendation(
                module=module_resp,
                reason=f"{seatbelt_count} recorded seatbelt violations during recent operating sessions.",
                priority=priority
            )
            recommendations.append(rec)
            
    # Future expandability for Idle-Time Management, Safe Machine Operation, etc.
    # would follow the exact same deterministic pattern here.
    
    return recommendations
