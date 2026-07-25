import pandas as pd
import numpy as np
import shap

def get_explainer(calibrated_model):
    """
    Given a CalibratedClassifierCV model wrapping XGBoost (from Phase 3),
    extract the first underlying XGBoost model to serve as a fast approximation
    for SHAP driver extraction.
    
    NOTE: Because TreeExplainer works on this underlying uncalibrated XGBoost 
    estimator, the SHAP values explain that raw model's output (often in log-odds 
    or raw probability scale), NOT the final isotonic-calibrated probability shown 
    in the /predict endpoint. Therefore, SHAP contributions and the final calibrated 
    probability will not be directly on the same scale, but the ranking of drivers 
    remains highly accurate.
    """
    # The calibrated_model is a CalibratedClassifierCV
    # We extract the first calibrated classifier's underlying estimator (XGBoost)
    if hasattr(calibrated_model, "calibrated_classifiers_"):
        base_estimator = calibrated_model.calibrated_classifiers_[0].estimator
    else:
        # Fallback if it's already a base estimator
        base_estimator = calibrated_model
        
    return shap.TreeExplainer(base_estimator)

def get_top_drivers(explainer, X_row: pd.DataFrame, top_n: int = 3):
    """
    Calculates SHAP values for a single customer (or batch) and returns the top N
    feature drivers by absolute magnitude, including their directional impact.
    
    CONFIRMATION: As verified in Phase 3 and enforced in the feature preparation, 
    no synthetic user_logs features (e.g., 'num_25', 'total_secs') are passed 
    into this X_row, meaning the explanations here represent genuine behavioral signals.
    """
    # Calculate SHAP values
    shap_values = explainer.shap_values(X_row)
    
    # If a single row was passed, it returns a 1D array. If multiple, 2D array.
    # Handle single row specifically for this helper function.
    if len(shap_values.shape) == 1 or shap_values.shape[0] == 1:
        vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
        row_features = X_row.iloc[0] if len(X_row.shape) > 1 else X_row
        feature_names = X_row.columns
        
        # Combine feature names, their shap values, and actual values
        drivers = []
        for i in range(len(feature_names)):
            drivers.append((feature_names[i], vals[i], row_features.iloc[i]))
            
        # Sort by absolute SHAP value (magnitude of impact) descending
        drivers.sort(key=lambda x: abs(x[1]), reverse=True)
        
        top_drivers = []
        for name, shap_val, val in drivers[:top_n]:
            # Positive shap_val pushes probability higher (increases risk)
            direction = "High" if shap_val > 0 else "Low"
            top_drivers.append(f"{name} ({direction})")
            
        return top_drivers
    else:
        # Batch processing
        results = []
        for idx in range(shap_values.shape[0]):
            vals = shap_values[idx]
            row_features = X_row.iloc[idx]
            feature_names = X_row.columns
            
            drivers = []
            for i in range(len(feature_names)):
                drivers.append((feature_names[i], vals[i], row_features.iloc[i]))
            
            drivers.sort(key=lambda x: abs(x[1]), reverse=True)
            
            top_drivers = []
            for name, shap_val, val in drivers[:top_n]:
                direction = "High" if shap_val > 0 else "Low"
                top_drivers.append(f"{name} ({direction})")
                
            results.append(top_drivers)
            
        return results

def prepare_features_for_model(df: pd.DataFrame, is_single_row=False) -> pd.DataFrame:
    """
    Helper function to enforce the exact feature set expected by the model.
    Drops ID columns and synthetic leak features, converting strings to categories.
    """
    X = df.copy()
    
    # Drop identifiers and target if present
    if 'msno' in X.columns:
        X = X.drop(columns=['msno'])
    if 'is_churn' in X.columns:
        X = X.drop(columns=['is_churn'])
        
    synthetic_cols = [
        'total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 
        'log_days', 'avg_secs_per_day', 'percent_complete', 'daily_unq_songs', 
        'engagement_trend_total_secs', 'engagement_trend_num_unq'
    ]
    X = X.drop(columns=[c for c in synthetic_cols if c in X.columns])
    
    CATEGORICAL_COLS = ['city', 'gender', 'age_clean', 'registered_via_clean', 'payment_method_id']
    for col in CATEGORICAL_COLS:
        if col in X.columns:
            X[col] = X[col].astype('category')
            
    num_cols = [c for c in X.columns if c not in CATEGORICAL_COLS]
    X[num_cols] = X[num_cols].fillna(0)
    
    # Optional: order columns exactly as they appeared in training to prevent xgboost feature name mismatch
    # In practice, XGBoost DataFrame predict takes care of this as long as the names match,
    # but we can do a strict ordering if we have the metadata (optional here, relied on metadata loaded in app).
    
    return X
