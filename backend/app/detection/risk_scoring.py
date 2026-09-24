"""
Layer 3: Risk Scoring
"""
from typing import Dict, Any, List

from app.detection import config


def calculate_risk_score(
    seatbelt_violations: int,
    idle_z: float,
    load_z: float
) -> Dict[str, Any]:
    """
    Computes a cumulative risk score and generates a list of risk factors.
    Returns highest applicable penalty for anomalies.
    """
    risk_score = 0
    factors = []

    # 1. Seatbelt Risk
    if seatbelt_violations > 0:
        penalty = seatbelt_violations * config.SEATBELT_PENALTY
        risk_score += penalty
        factors.append(f"{seatbelt_violations} seatbelt violation(s)")

    # 2. Idle Anomaly Risk
    if idle_z > config.Z_SCORE_HIGH_THRESHOLD:
        risk_score += config.IDLE_HIGH_ANOMALY_PENALTY
        factors.append(f"Idle time highly anomalous (z={idle_z:.2f})")
    elif idle_z > config.Z_SCORE_THRESHOLD:
        risk_score += config.IDLE_ANOMALY_PENALTY
        factors.append(f"Idle time anomalous (z={idle_z:.2f})")

    # 3. Load Anomaly Risk
    if load_z > config.Z_SCORE_HIGH_THRESHOLD:
        risk_score += config.LOAD_HIGH_ANOMALY_PENALTY
        factors.append(f"Load cycles highly anomalous (z={load_z:.2f})")
    elif load_z > config.Z_SCORE_THRESHOLD:
        risk_score += config.LOAD_ANOMALY_PENALTY
        factors.append(f"Load cycles anomalous (z={load_z:.2f})")

    return {
        "risk_score": risk_score,
        "risk_factors": factors
    }
