"""
Layer 2: Anomaly Detection
"""
from typing import Dict, Any

from app.detection import config


def calculate_z_score(value: float, mean: float, std: float) -> float:
    """Calculates z-score. Avoids division by zero."""
    if std == 0:
        return 0.0
    return (value - mean) / std


def detect_anomalies(
    session_total_idle: float,
    session_total_load: float,
    baseline_mean_idle: float,
    baseline_std_idle: float,
    baseline_mean_load: float,
    baseline_std_load: float
) -> Dict[str, Any]:
    """
    Compares session totals against the operator's historical baseline.
    """
    idle_z = calculate_z_score(session_total_idle, baseline_mean_idle, baseline_std_idle)
    load_z = calculate_z_score(session_total_load, baseline_mean_load, baseline_std_load)

    idle_anomaly = idle_z > config.Z_SCORE_THRESHOLD
    load_anomaly = load_z > config.Z_SCORE_THRESHOLD

    return {
        "idle_z": idle_z,
        "load_z": load_z,
        "idle_anomaly": idle_anomaly,
        "load_anomaly": load_anomaly
    }
