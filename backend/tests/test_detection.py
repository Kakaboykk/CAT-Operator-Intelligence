"""
Tests for Phase 3 Detection Logic.
"""
from datetime import date
import uuid

from app.detection.safety_rules import evaluate_seatbelt_violations
from app.detection.anomaly_detection import detect_anomalies
from app.detection.risk_scoring import calculate_risk_score
from app.detection.severity import get_severity
from app.detection.incident_generator import determine_event_type, generate_description, create_incident_record

class MockTelemetry:
    def __init__(self, seatbelt_status: str):
        self.seatbelt_status = seatbelt_status

def test_seatbelt_rule_zero():
    records = [MockTelemetry("Fastened"), MockTelemetry("Fastened")]
    res = evaluate_seatbelt_violations(records)
    assert res["seatbelt_violations"] == 0
    assert not res["seatbelt_violation_detected"]

def test_seatbelt_rule_multiple():
    records = [MockTelemetry("Unfastened"), MockTelemetry("Fastened"), MockTelemetry("Unfastened")]
    res = evaluate_seatbelt_violations(records)
    assert res["seatbelt_violations"] == 2
    assert res["seatbelt_violation_detected"]

def test_z_score_calculation():
    # Value 10, mean 5, std 2.5 => z = 2.0
    res = detect_anomalies(10.0, 0, 5.0, 2.5, 0, 1)
    assert res["idle_z"] == 2.0
    assert not res["idle_anomaly"] # threshold is > 2.0
    
    # Value 11, mean 5, std 2.5 => z = 2.4
    res = detect_anomalies(11.0, 0, 5.0, 2.5, 0, 1)
    assert res["idle_z"] == 2.4
    assert res["idle_anomaly"]

def test_zero_standard_deviation_safe():
    res = detect_anomalies(10.0, 0, 5.0, 0.0, 0, 0.0)
    assert res["idle_z"] == 0.0
    assert res["load_z"] == 0.0

def test_risk_scoring():
    # Seatbelt only (2 violations * 15 = 30)
    res = calculate_risk_score(2, 0.0, 0.0)
    assert res["risk_score"] == 30
    assert len(res["risk_factors"]) == 1
    
    # Idle anomaly only (z=2.5 => +5)
    res = calculate_risk_score(0, 2.5, 0.0)
    assert res["risk_score"] == 5
    
    # High Load anomaly only (z=3.5 => +10)
    res = calculate_risk_score(0, 0.0, 3.5)
    assert res["risk_score"] == 10
    
    # Combined risk: 1 seatbelt (15), High idle (10), Normal load (0) = 25
    res = calculate_risk_score(1, 3.5, 1.0)
    assert res["risk_score"] == 25
    assert len(res["risk_factors"]) == 2

def test_ensure_penalties_dont_stack():
    # If idle_z > 3.0, only +10 is applied, not +15
    res = calculate_risk_score(0, 3.5, 0.0)
    assert res["risk_score"] == 10 # Not 15

def test_severity_mapping():
    assert get_severity(0) is None
    assert get_severity(5) == "Low"
    assert get_severity(10) == "Medium"
    assert get_severity(25) == "High"
    assert get_severity(45) == "Critical"

def test_event_type_selection():
    assert determine_event_type(1, False, False) == "SEATBELT_VIOLATION"
    assert determine_event_type(0, True, False) == "IDLE_ANOMALY"
    assert determine_event_type(0, False, True) == "LOAD_ANOMALY"
    assert determine_event_type(1, True, False) == "COMBINED_RISK"
    assert determine_event_type(1, True, True) == "COMBINED_RISK"
    assert determine_event_type(0, False, False) == "UNKNOWN"

def test_description_generation():
    desc = generate_description("COMBINED_RISK", ["1 seatbelt violation(s)", "Idle time anomalous (z=2.50)"])
    assert "Combined risk detected" in desc
    assert "1 seatbelt violation" in desc
    
def test_create_incident_record():
    # Zero risk -> severity None -> no record
    record = create_incident_record(("OP1", "M1", "2026-09-24"), "ts", 0, False, False, None, [])
    assert record is None
    
    record = create_incident_record(("OP1", "M1", "2026-09-24"), "ts", 2, False, False, "High", ["2 seatbelts"])
    assert record["operator_id"] == "OP1"
    assert record["event_type"] == "SEATBELT_VIOLATION"
    assert record["severity"] == "High"
