"""
Tests for Phase 4 ML logic (Dataset construction, leakage prevention, modeling).
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from app.ml.dataset import get_train_test_split
from app.ml.train import train_and_evaluate
from app.ml import config

@pytest.fixture
def mock_dataset():
    # Construct a dataset that is sorted chronologically
    df = pd.DataFrame([
        {
            "task_id": "1",
            "task_datetime": datetime(2026, 1, 1, 10, 0),
            "estimated_time": 4.0,
            "actual_time": 5.0,
            "task_type": "Digging",
            "weather": "Clear",
            "operator_skill": "Expert",
            "machine_age": 5.0,
            "operator_id": "OP1",
            "machine_id": "MAC1",
            "operator_historical_avg_time": np.nan,
            "operator_historical_incident_count": 0,
            "machine_historical_fault_count": 0
        },
        {
            "task_id": "2",
            "task_datetime": datetime(2026, 1, 2, 10, 0),
            "estimated_time": 6.0,
            "actual_time": 7.0,
            "task_type": "Loading",
            "weather": "Rainy",
            "operator_skill": "Expert",
            "machine_age": 5.0,
            "operator_id": "OP1",
            "machine_id": "MAC1",
            "operator_historical_avg_time": 5.0, # Leakage safe (Only uses task 1)
            "operator_historical_incident_count": 0,
            "machine_historical_fault_count": 0
        },
        {
            "task_id": "3",
            "task_datetime": datetime(2026, 1, 3, 10, 0),
            "estimated_time": 5.0,
            "actual_time": 5.0,
            "task_type": "Digging",
            "weather": "Clear",
            "operator_skill": "Beginner",
            "machine_age": 1.0,
            "operator_id": "OP2",
            "machine_id": "MAC2",
            "operator_historical_avg_time": np.nan,
            "operator_historical_incident_count": 0,
            "machine_historical_fault_count": 0
        },
        {
            "task_id": "4",
            "task_datetime": datetime(2026, 1, 4, 10, 0),
            "estimated_time": 8.0,
            "actual_time": 10.0,
            "task_type": "Loading",
            "weather": "Clear",
            "operator_skill": "Expert",
            "machine_age": 5.0,
            "operator_id": "OP1",
            "machine_id": "MAC1",
            "operator_historical_avg_time": 6.0, # Leakage safe (Task 1 + Task 2) / 2
            "operator_historical_incident_count": 0,
            "machine_historical_fault_count": 0
        },
        {
            "task_id": "5",
            "task_datetime": datetime(2026, 1, 5, 10, 0),
            "estimated_time": 4.0,
            "actual_time": 4.0,
            "task_type": "Digging",
            "weather": "Rainy",
            "operator_skill": "Beginner",
            "machine_age": 1.0,
            "operator_id": "OP2",
            "machine_id": "MAC2",
            "operator_historical_avg_time": 5.0, # Leakage safe (Task 3)
            "operator_historical_incident_count": 0,
            "machine_historical_fault_count": 0
        }
    ])
    return df

def test_chronological_split(mock_dataset):
    train_df, test_df = get_train_test_split(mock_dataset, train_ratio=0.8)
    
    assert len(train_df) == 4
    assert len(test_df) == 1
    
    train_end = train_df.iloc[-1]['task_datetime']
    test_start = test_df.iloc[0]['task_datetime']
    
    assert train_end < test_start

def test_missing_value_handling_in_training(mock_dataset):
    train_df, test_df = get_train_test_split(mock_dataset, train_ratio=0.8)
    # The first task for each operator has NaN for historical average.
    # The pipeline should handle it without crashing.
    model, metrics, importances = train_and_evaluate(train_df, test_df)
    
    # We should get a valid pipeline back
    assert model is not None
    assert 'Random Forest' in metrics
    
    # Assert metrics are calculated
    assert metrics['Random Forest']['MAE'] >= 0
    assert metrics['Random Forest']['RMSE'] >= 0
    
    # Feature importances exist
    assert not importances.empty

def test_feature_importance_extracted(mock_dataset):
    train_df, test_df = get_train_test_split(mock_dataset, train_ratio=0.8)
    _, _, importances = train_and_evaluate(train_df, test_df)
    
    # Should have numerical + one-hot encoded categories
    assert len(importances) > len(config.NUMERICAL_FEATURES)
    assert 'estimated_time' in importances['feature'].values
