"""
Phase 4 ML Configuration.
"""

# Train / Test split ratio
TRAIN_RATIO = 0.8

# Reproducibility
RANDOM_STATE = 42

# Target definition
TARGET_COLUMN = "actual_time"

# Features categorization for preprocessing
NUMERICAL_FEATURES = [
    "estimated_time",
    "machine_age",
    "operator_historical_avg_time",
    "operator_historical_incident_count",
    "machine_historical_fault_count"
]

CATEGORICAL_FEATURES = [
    "task_type",
    "weather",
    "operator_skill",
    "operator_id",
    "machine_id"
]

# Model artifact path
MODEL_ARTIFACT_PATH = "model_artifacts/task_duration_model.joblib"
