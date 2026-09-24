"""
Configuration for Phase 3 Detection thresholds and penalties.
"""

# Z-Score Anomaly Thresholds
Z_SCORE_THRESHOLD = 2.0
Z_SCORE_HIGH_THRESHOLD = 3.0

# Penalties
SEATBELT_PENALTY = 15

IDLE_ANOMALY_PENALTY = 5
IDLE_HIGH_ANOMALY_PENALTY = 10

LOAD_ANOMALY_PENALTY = 5
LOAD_HIGH_ANOMALY_PENALTY = 10

# Severity mapping thresholds (Risk scores)
LOW_MAX = 9
MEDIUM_MAX = 19
HIGH_MAX = 39
# 40+ is CRITICAL
