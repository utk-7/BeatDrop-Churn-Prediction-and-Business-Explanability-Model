import pytest
import numpy as np
import pandas as pd
import joblib
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from train import load_and_prepare_data

def test_scale_pos_weight_dynamic():
    # Test that scale_pos_weight is correctly computed
    X_train, X_test, y_train, y_test, msno_train, msno_test, scale_pos_weight = load_and_prepare_data("data/processed/customer_features.parquet")
    
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    expected_spw = neg_count / pos_count if pos_count > 0 else 1.0
    
    assert np.isclose(scale_pos_weight, expected_spw)
    assert scale_pos_weight > 1.0 # given 9% churn, it should be > 1

def test_model_loading_and_predict_proba():
    model_path = "models/xgboost_model_v0.1.0.joblib"
    if not os.path.exists(model_path):
        pytest.skip(f"Model file {model_path} not found. Run src/train.py first.")
        
    model = joblib.load(model_path)
    assert model is not None
    
    X_train, X_test, y_train, y_test, msno_train, msno_test, scale_pos_weight = load_and_prepare_data("data/processed/customer_features.parquet")
    
    # Predict on a small batch
    import xgboost as xgb
    dtest = xgb.DMatrix(X_test.head(10), enable_categorical=True)
    preds = model.predict(dtest)
    
    assert len(preds) == 10
    assert all(0.0 <= p <= 1.0 for p in preds)
