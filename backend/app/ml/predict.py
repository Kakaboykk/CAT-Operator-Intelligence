"""
Inference service for Task Duration Prediction.
"""
import pandas as pd
from typing import Dict, Any

from app.ml.train import load_model
from app.ml import config

class TaskPredictionService:
    def __init__(self, model_path: str = config.MODEL_ARTIFACT_PATH):
        self.model = load_model(model_path)
        
    def predict(self, task_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accepts a dictionary of features and returns a predicted task duration.
        """
        # Convert to single-row DataFrame
        df = pd.DataFrame([task_features])
        
        # Predict
        predicted_duration = self.model.predict(df)[0]
        
        # Extract feature importances to provide explanation context
        # (This uses the pre-trained global feature importances, as tree paths for single instances are complex)
        rf_model = self.model.named_steps['regressor']
        cat_encoder = self.model.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
        cat_features = cat_encoder.get_feature_names_out(config.CATEGORICAL_FEATURES)
        
        all_features = config.NUMERICAL_FEATURES + list(cat_features)
        importances = rf_model.feature_importances_
        
        # We can find the top features for this specific prediction by looking at the highest global importance features
        # that are actually active/present for this instance.
        
        # To do this correctly, we transform the single row
        transformed_row = self.model.named_steps['preprocessor'].transform(df)
        if hasattr(transformed_row, 'toarray'):
            transformed_row = transformed_row.toarray()[0]
        else:
            transformed_row = transformed_row[0]
            
        # Multiply global importance by the actual feature value (standardized/one-hot)
        # to approximate local contribution (a simple proxy for SHAP)
        local_contributions = np.abs(transformed_row * importances)
        
        importance_df = pd.DataFrame({
            'feature': all_features,
            'contribution': local_contributions
        }).sort_values('contribution', ascending=False)
        
        top_factors = importance_df.head(3)['feature'].tolist()
        
        return {
            "predicted_duration": float(predicted_duration),
            "unit": "hours",
            "model": "RandomForestRegressor",
            "important_features": top_factors
        }

# Import numpy here for the prediction logic
import numpy as np
