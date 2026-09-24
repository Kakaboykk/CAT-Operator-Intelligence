"""
Execution script to build dataset, train models, evaluate, and save artifact.
"""
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.ml.dataset import build_dataset, get_train_test_split
from app.ml.train import train_and_evaluate, save_model
from app.ml.predict import TaskPredictionService
from app.ml import config

def main():
    print("PHASE 4: ML INTELLIGENCE & TASK-TIME PREDICTION")
    print("-------------------------------------------------")
    
    with SessionLocal() as db:
        print("1. Constructing leakage-safe dataset from DB...")
        df = build_dataset(db)
        
    if df.empty:
        print("Error: No data available to build dataset.")
        return
        
    print(f"Total tasks processed: {len(df)}")
    
    print("\n2. Performing chronological split...")
    train_df, test_df = get_train_test_split(df, config.TRAIN_RATIO)
    
    print(f"Training samples: {len(train_df)}")
    print(f"Testing samples: {len(test_df)}")
    print(f"Train end timestamp: {train_df.iloc[-1]['task_datetime']}")
    print(f"Test start timestamp: {test_df.iloc[0]['task_datetime']}")
    
    print("\n3. Training Models & Evaluating...")
    rf_pipeline, metrics, importances = train_and_evaluate(train_df, test_df)
    
    print("\nEvaluation Metrics Comparison:")
    print(f"{'Model':<25} | {'MAE':<10} | {'RMSE':<10} | {'R2':<10}")
    print("-" * 65)
    for model_name, m in metrics.items():
        print(f"{model_name:<25} | {m['MAE']:<10.4f} | {m['RMSE']:<10.4f} | {m['R2']:<10.4f}")
        
    print("\n4. Feature Importance (Random Forest Top 5):")
    for i, row in importances.head(5).iterrows():
        print(f"  {row['feature']:<35} : {row['importance']:.4f}")
        
    print("\n5. Saving Model Artifact...")
    os.makedirs(os.path.dirname(config.MODEL_ARTIFACT_PATH), exist_ok=True)
    save_model(rf_pipeline, config.MODEL_ARTIFACT_PATH)
    print(f"Model saved to: {config.MODEL_ARTIFACT_PATH}")
    
    print("\n6. Example Inference...")
    predictor = TaskPredictionService()
    
    # Grab the first row of test set for inference
    example_row = test_df.iloc[0]
    sample_features = {
        "estimated_time": example_row["estimated_time"],
        "task_type": example_row["task_type"],
        "weather": example_row["weather"],
        "operator_skill": example_row["operator_skill"],
        "machine_age": example_row["machine_age"],
        "operator_id": example_row["operator_id"],
        "machine_id": example_row["machine_id"],
        "operator_historical_avg_time": example_row["operator_historical_avg_time"],
        "operator_historical_incident_count": example_row["operator_historical_incident_count"],
        "machine_historical_fault_count": example_row["machine_historical_fault_count"]
    }
    
    res = predictor.predict(sample_features)
    print(f"Input estimated_time: {sample_features['estimated_time']} hours")
    print(f"Actual actual_time: {example_row['actual_time']} hours")
    print(f"Predicted duration: {res['predicted_duration']:.2f} {res['unit']}")
    print(f"Important factors context: {', '.join(res['important_features'])}")
    
    print("\nPhase 4 ML pipeline executed successfully.")

if __name__ == "__main__":
    main()
