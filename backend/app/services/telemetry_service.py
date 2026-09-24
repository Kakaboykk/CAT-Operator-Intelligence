"""
Telemetry Service
Handles data fetching and logical session aggregation.
"""
from typing import List, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
import statistics

from app.models.telemetry import Telemetry
from app.detection.safety_rules import evaluate_seatbelt_violations

class LogicalSession:
    def __init__(self, operator_id: str, machine_id: str, session_date: date):
        self.operator_id = operator_id
        self.machine_id = machine_id
        self.session_date = session_date
        
        self.records: List[Telemetry] = []
        self.total_idle = 0.0
        self.total_load_cycles = 0
        self.seatbelt_violations = 0
        
        # We need a timestamp to use for the generated incident
        self.representative_timestamp = None

    def add_record(self, record: Telemetry):
        self.records.append(record)
        self.total_idle += record.idling_time
        self.total_load_cycles += record.load_cycles
        
        if not self.representative_timestamp:
            self.representative_timestamp = record.timestamp

    def finalize(self):
        """Runs rule evaluations on the accumulated records."""
        seatbelt_res = evaluate_seatbelt_violations(self.records)
        self.seatbelt_violations = seatbelt_res["seatbelt_violations"]
        
    @property
    def session_key(self) -> Tuple[str, str, str]:
        return (self.operator_id, self.machine_id, self.session_date.isoformat())


class OperatorBaseline:
    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self.idle_totals: List[float] = []
        self.load_totals: List[int] = []
        
        self.mean_idle = 0.0
        self.std_idle = 0.0
        self.mean_load = 0.0
        self.std_load = 0.0
        
    def add_session(self, session: LogicalSession):
        self.idle_totals.append(session.total_idle)
        self.load_totals.append(session.total_load_cycles)
        
    def calculate(self):
        if len(self.idle_totals) > 0:
            self.mean_idle = statistics.mean(self.idle_totals)
            self.std_idle = statistics.stdev(self.idle_totals) if len(self.idle_totals) > 1 else 0.0
            
        if len(self.load_totals) > 0:
            self.mean_load = statistics.mean(self.load_totals)
            self.std_load = statistics.stdev(self.load_totals) if len(self.load_totals) > 1 else 0.0


def fetch_and_group_telemetry(db: Session) -> Dict[Tuple[str, str, str], LogicalSession]:
    """
    Fetches all telemetry and groups it by (operator_id, machine_id, date).
    """
    records = db.query(Telemetry).order_by(Telemetry.timestamp).all()
    sessions = {}
    
    for record in records:
        # Assumes timestamp is a timezone-aware datetime
        # Converting to local date or UTC date depending on storage. Let's use UTC date.
        rec_date = record.timestamp.date()
        key = (record.operator_id, record.machine_id, rec_date)
        
        if key not in sessions:
            sessions[key] = LogicalSession(record.operator_id, record.machine_id, rec_date)
            
        sessions[key].add_record(record)
        
    for session in sessions.values():
        session.finalize()
        
    return sessions


def build_operator_baselines(sessions: Dict[Any, LogicalSession]) -> Dict[str, OperatorBaseline]:
    """
    Builds historical baselines for each operator using all their sessions.
    """
    baselines: Dict[str, OperatorBaseline] = {}
    
    for session in sessions.values():
        op_id = session.operator_id
        if op_id not in baselines:
            baselines[op_id] = OperatorBaseline(op_id)
            
        baselines[op_id].add_session(session)
        
    for baseline in baselines.values():
        baseline.calculate()
        
    return baselines
