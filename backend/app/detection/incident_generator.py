"""
Layer 5: Incident Generator
"""
import uuid
from typing import Dict, Any, Optional

def determine_event_type(
    seatbelt_violations: int,
    idle_anomaly: bool,
    load_anomaly: bool
) -> str:
    """
    Determines the primary event type based on the contributing factors.
    """
    factors_count = 0
    if seatbelt_violations > 0:
        factors_count += 1
    if idle_anomaly:
        factors_count += 1
    if load_anomaly:
        factors_count += 1
        
    if factors_count > 1:
        return "COMBINED_RISK"
    elif seatbelt_violations > 0:
        return "SEATBELT_VIOLATION"
    elif idle_anomaly:
        return "IDLE_ANOMALY"
    elif load_anomaly:
        return "LOAD_ANOMALY"
    else:
        return "UNKNOWN"


def generate_description(
    event_type: str,
    risk_factors: list[str]
) -> str:
    """
    Generates a human-readable explanation based on the event type and factors.
    """
    factors_str = "; ".join(risk_factors)
    
    if event_type == "COMBINED_RISK":
        return f"Combined risk detected: {factors_str}."
    elif event_type == "SEATBELT_VIOLATION":
        return f"Seatbelt violation detected: {factors_str}."
    elif event_type == "IDLE_ANOMALY":
        return f"Idle anomaly detected: {factors_str}."
    elif event_type == "LOAD_ANOMALY":
        return f"Load anomaly detected: {factors_str}."
    
    return "Unknown safety event detected."


def create_incident_record(
    session_key: tuple[str, str, str],
    timestamp,
    seatbelt_violations: int,
    idle_anomaly: bool,
    load_anomaly: bool,
    severity: str,
    risk_factors: list[str]
) -> Optional[Dict[str, Any]]:
    """
    Constructs the incident dictionary for database insertion.
    Returns None if severity is None.
    """
    if not severity:
        return None

    operator_id, machine_id, _ = session_key
    event_type = determine_event_type(seatbelt_violations, idle_anomaly, load_anomaly)
    description = generate_description(event_type, risk_factors)

    return {
        "incident_id": uuid.uuid4(), # Incident uses standard UUIDs (not deterministic seeded) since it's an output of Phase 3, but maybe we should make it deterministic for tests? The prompt just said "Use existing incident table".
        "timestamp": timestamp,
        "operator_id": operator_id,
        "machine_id": machine_id,
        "event_type": event_type,
        "severity": severity,
        "description": description,
        "status": "Active"
    }
