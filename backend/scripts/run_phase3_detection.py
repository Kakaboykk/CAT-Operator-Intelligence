"""
Execution Script for Phase 3 Detection.
"""
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.incident import Incident
from app.services.telemetry_service import fetch_and_group_telemetry, build_operator_baselines
from app.detection.anomaly_detection import detect_anomalies
from app.detection.risk_scoring import calculate_risk_score
from app.detection.severity import get_severity
from app.detection.incident_generator import create_incident_record

def main():
    print("PHASE 3 DETECTION")
    print("-----------------")
    
    with SessionLocal() as db:
        # 1. Fetch & Group Telemetry
        sessions = fetch_and_group_telemetry(db)
        print(f"Sessions evaluated: {len(sessions)}")
        
        # Count total raw telemetry processed
        telemetry_count = sum(len(s.records) for s in sessions.values())
        print(f"Telemetry records processed: {telemetry_count}")
        
        # 2. Build Baselines
        baselines = build_operator_baselines(sessions)
        
        # Tracking stats
        stats = {
            "seatbelt_violations": 0,
            "idle_anomalies": 0,
            "load_anomalies": 0,
            "combined_risk": 0,
            "incidents_generated": 0,
            "duplicates_skipped": 0,
            "severity": {
                "Low": 0,
                "Medium": 0,
                "High": 0,
                "Critical": 0
            }
        }
        
        # 3. Process each session
        new_incidents = []
        for session_key, session in sessions.items():
            baseline = baselines[session.operator_id]
            
            # Anomaly Detection
            anomaly_res = detect_anomalies(
                session_total_idle=session.total_idle,
                session_total_load=session.total_load_cycles,
                baseline_mean_idle=baseline.mean_idle,
                baseline_std_idle=baseline.std_idle,
                baseline_mean_load=baseline.mean_load,
                baseline_std_load=baseline.std_load
            )
            
            # Risk Scoring
            risk_res = calculate_risk_score(
                seatbelt_violations=session.seatbelt_violations,
                idle_z=anomaly_res["idle_z"],
                load_z=anomaly_res["load_z"]
            )
            
            # Severity Mapping
            severity = get_severity(risk_res["risk_score"])
            
            if severity:
                # Update stats
                if session.seatbelt_violations > 0:
                    stats["seatbelt_violations"] += 1
                if anomaly_res["idle_anomaly"]:
                    stats["idle_anomalies"] += 1
                if anomaly_res["load_anomaly"]:
                    stats["load_anomalies"] += 1
                
                # Check for combined risk
                factors_present = sum([
                    1 if session.seatbelt_violations > 0 else 0,
                    1 if anomaly_res["idle_anomaly"] else 0,
                    1 if anomaly_res["load_anomaly"] else 0
                ])
                if factors_present > 1:
                    stats["combined_risk"] += 1

                # Generate Incident
                incident_dict = create_incident_record(
                    session_key=session.session_key,
                    timestamp=session.representative_timestamp,
                    seatbelt_violations=session.seatbelt_violations,
                    idle_anomaly=anomaly_res["idle_anomaly"],
                    load_anomaly=anomaly_res["load_anomaly"],
                    severity=severity,
                    risk_factors=risk_res["risk_factors"]
                )
                
                # Deduplication Check (Database Safe)
                # Has an incident already been created for this operator, machine, and day?
                # The prompt asks for an application-level check + DB safe strategy.
                # Since we don't want to modify the DB schema, we query the DB to see if an incident exists
                # around this timestamp for this operator and machine.
                # We can check by DATE(timestamp) if the DB supports it, but since timestamp is DateTime,
                # we can just fetch existing incidents and check.
                
                # Using SQLAlchemy to check if an incident exists for this operator, machine on this date
                # We do this simply by comparing the date of the timestamp
                start_of_day = session.session_date
                end_of_day = start_of_day
                
                # We use string matching or cast in DB. Safest is Python-side check for this exact session
                # or a simple DB query. Let's do a simple DB query for the exact operator and machine
                existing = db.query(Incident).filter(
                    Incident.operator_id == session.operator_id,
                    Incident.machine_id == session.machine_id
                ).all()
                
                duplicate_found = False
                for ex in existing:
                    if ex.timestamp.date() == session.session_date:
                        duplicate_found = True
                        break
                        
                if duplicate_found:
                    stats["duplicates_skipped"] += 1
                else:
                    new_incident = Incident(**incident_dict)
                    new_incidents.append(new_incident)
                    stats["incidents_generated"] += 1
                    stats["severity"][severity] += 1
                    
        # 4. Insert Incidents
        if new_incidents:
            db.add_all(new_incidents)
            db.commit()
            
        print("")
        print(f"Seatbelt violations: {stats['seatbelt_violations']}")
        print(f"Idle anomalies: {stats['idle_anomalies']}")
        print(f"Load anomalies: {stats['load_anomalies']}")
        print(f"Combined-risk sessions: {stats['combined_risk']}")
        print("")
        print(f"Incidents generated: {stats['incidents_generated']}")
        print(f"Duplicates skipped: {stats['duplicates_skipped']}")
        print("")
        print("Severity:")
        print(f"LOW: {stats['severity']['Low']}")
        print(f"MEDIUM: {stats['severity']['Medium']}")
        print(f"HIGH: {stats['severity']['High']}")
        print(f"CRITICAL: {stats['severity']['Critical']}")


if __name__ == "__main__":
    main()
