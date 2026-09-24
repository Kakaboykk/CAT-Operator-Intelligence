"""
Configuration for synthetic data generation.
Defines base parameters for operators, machines, tasks, and faults.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class OperatorProfile:
    op_id: str
    skill: str
    idle_mean: float
    idle_std: float
    load_cycles_mean: float
    load_cycles_std: float
    unfastened_prob: float
    anomaly_type: str | None = None
    anomaly_prob: float = 0.0


@dataclass
class MachineProfile:
    machine_id: str
    age: float


@dataclass
class TaskProfile:
    task_type: str
    estimated_mean: float
    estimated_std: float


@dataclass
class FaultProfile:
    fault_type: str
    downtime_mean: float
    downtime_std: float


# ── Configured Profiles ───────────────────────────────────────────────────────

OPERATORS = [
    # OP1001: Normal
    OperatorProfile("OP1001", "Expert", idle_mean=15.0, idle_std=2.0, load_cycles_mean=12.0, load_cycles_std=2.0, unfastened_prob=0.01),
    # OP1002: Normal, slightly higher idle
    OperatorProfile("OP1002", "Intermediate", idle_mean=18.0, idle_std=3.0, load_cycles_mean=10.0, load_cycles_std=3.0, unfastened_prob=0.02),
    # OP1003: High Idling Anomaly
    OperatorProfile("OP1003", "Beginner", idle_mean=15.0, idle_std=3.0, load_cycles_mean=10.0, load_cycles_std=2.0, unfastened_prob=0.05, anomaly_type="high_idling", anomaly_prob=0.25),
    # OP1004: Unusual Load Cycles Anomaly
    OperatorProfile("OP1004", "Intermediate", idle_mean=14.0, idle_std=2.0, load_cycles_mean=11.0, load_cycles_std=2.0, unfastened_prob=0.01, anomaly_type="high_load_cycles", anomaly_prob=0.25),
    # OP1005: Normal
    OperatorProfile("OP1005", "Expert", idle_mean=12.0, idle_std=1.5, load_cycles_mean=14.0, load_cycles_std=2.0, unfastened_prob=0.0),
]

MACHINES = [
    MachineProfile("EXC001", age=2.5),
    MachineProfile("EXC002", age=5.0),
    MachineProfile("EXC003", age=8.0),
    MachineProfile("LDR001", age=1.5),
    MachineProfile("LDR002", age=10.0),
]

TASKS = [
    TaskProfile("Earth Excavation", estimated_mean=4.0, estimated_std=1.0),
    TaskProfile("Trenching", estimated_mean=6.0, estimated_std=1.5),
    TaskProfile("Material Loading", estimated_mean=2.5, estimated_std=0.5),
    TaskProfile("Grading", estimated_mean=8.0, estimated_std=2.0),
    TaskProfile("Demolition", estimated_mean=5.0, estimated_std=1.5),
]

FAULTS = [
    FaultProfile("Hydraulic Fault", downtime_mean=15.0, downtime_std=3.0),
    FaultProfile("Engine Fault", downtime_mean=30.0, downtime_std=5.0),
    FaultProfile("Transmission Fault", downtime_mean=45.0, downtime_std=10.0),
    FaultProfile("Electrical Fault", downtime_mean=20.0, downtime_std=4.0),
    FaultProfile("Cooling System Fault", downtime_mean=25.0, downtime_std=5.0),
]

WEATHER_CONDITIONS = ["Clear", "Cloudy", "Rainy", "Windy"]
WEATHER_PROBABILITIES = [0.5, 0.3, 0.1, 0.1]
