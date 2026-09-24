"""
Layer 1: Deterministic Safety Rules
"""
from typing import Dict, Any, List

def evaluate_seatbelt_violations(telemetry_records: List[Any]) -> Dict[str, Any]:
    """
    Evaluates raw telemetry records for a single logical session to determine seatbelt violations.
    Expects a list of objects that have a 'seatbelt_status' attribute.
    """
    violations = 0
    for record in telemetry_records:
        if getattr(record, "seatbelt_status", None) == 'Unfastened':
            violations += 1

    return {
        "seatbelt_violations": violations,
        "seatbelt_violation_detected": violations > 0
    }
