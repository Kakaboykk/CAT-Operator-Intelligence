"""
Layer 4: Severity Mapping
"""
from typing import Optional

from app.detection import config


def get_severity(risk_score: int) -> Optional[str]:
    """
    Maps a computed risk score to a string severity level.
    Returns None if score is 0.
    """
    if risk_score <= 0:
        return None
    if risk_score <= config.LOW_MAX:
        return "Low"
    if risk_score <= config.MEDIUM_MAX:
        return "Medium"
    if risk_score <= config.HIGH_MAX:
        return "High"
    
    return "Critical"
