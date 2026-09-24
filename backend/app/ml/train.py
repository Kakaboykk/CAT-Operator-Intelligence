"""
Model definition, training pipeline, and evaluation metrics.
"""
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

from app.ml import config

def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Constructs the sklearn preprocessing pipeline for numerical and categorical features.
    """
    numeric_transformer = Pipeline(steps=[
        # Use median for missing values (like operator's first task where history is NaN)
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, config.NUMERICAL_FEATURES),
            ('cat', categorical_transformer, config.CATEGORICAL_FEATURES)
        ])
    
    return preprocessor

def train_and_evaluate(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """
    Trains models, evaluates them, and returns metrics + best model.
    """
    X_train = train_df[config.NUMERICAL_FEATURES + config.CATEGORICAL_FEATURES]
    y_train = train_df[config.TARGET_COLUMN]
    
    X_test = test_df[config.NUMERICAL_FEATURES + config.CATEGORICAL_FEATURES]
    y_test = test_df[config.TARGET_COLUMN]

    # Baseline 1: Estimated Time
    baseline_preds = X_test['estimated_time']
    baseline_metrics = {
        'MAE': mean_absolute_error(y_test, baseline_preds),
        'RMSE': np.sqrt(mean_squared_error(y_test, baseline_preds)),
        'R2': r2_score(y_test, baseline_preds)
    }

    # Pipeline setup
    preprocessor = build_preprocessing_pipeline()

    # Model 2: Linear Regression
    lr_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                  ('regressor', LinearRegression())])
    lr_pipeline.fit(X_train, y_train)
    lr_preds = lr_pipeline.predict(X_test)
    lr_metrics = {
        'MAE': mean_absolute_error(y_test, lr_preds),
        'RMSE': np.sqrt(mean_squared_error(y_test, lr_preds)),
        'R2': r2_score(y_test, lr_preds)
    }

    # Model 3: Random Forest Regressor
    rf_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                  ('regressor', RandomForestRegressor(n_estimators=100, random_state=config.RANDOM_STATE))])
    rf_pipeline.fit(X_train, y_train)
    rf_preds = rf_pipeline.predict(X_test)
    rf_metrics = {
        'MAE': mean_absolute_error(y_test, rf_preds),
        'RMSE': np.sqrt(mean_squared_error(y_test, rf_preds)),
        'R2': r2_score(y_test, rf_preds)
    }

    # Extract feature importances
    rf_model = rf_pipeline.named_steps['regressor']
    
    # Get feature names after one-hot encoding
    cat_encoder = rf_pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
    cat_features = cat_encoder.get_feature_names_out(config.CATEGORICAL_FEATURES)
    
    all_features = config.NUMERICAL_FEATURES + list(cat_features)
    importances = rf_model.feature_importances_
    
    feature_importance_df = pd.DataFrame({
        'feature': all_features,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    metrics = {
        'Baseline': baseline_metrics,
        'Linear Regression': lr_metrics,
        'Random Forest': rf_metrics
    }
    
    return rf_pipeline, metrics, feature_importance_df

def save_model(model: Pipeline, path: str):
    joblib.dump(model, path)

def load_model(path: str) -> Pipeline:
    return joblib.load(path)
