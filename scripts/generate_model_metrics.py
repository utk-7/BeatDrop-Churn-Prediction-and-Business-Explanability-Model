import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix
from sklearn.calibration import calibration_curve

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import explain

def generate_metrics():
    model_path = 'models/xgboost_model_v0.2.0.joblib'
    data_path = 'data/processed/customer_features.parquet'
    output_path = 'models/model_metrics.json'
    
    if not os.path.exists(model_path) or not os.path.exists(data_path):
        print("Model or data not found. Ensure models/ and data/processed/ exist.")
        return
        
    print("Loading model and data...")
    model = joblib.load(model_path)
    df = pd.read_parquet(data_path)
    
    X = explain.prepare_features_for_model(df)
    
    if 'is_churn' not in df.columns:
        print("Warning: 'is_churn' not found in dataset. Using dummy data for demonstration.")
        y = np.random.randint(0, 2, size=len(X))
    else:
        y = df['is_churn']
        
    print("Predicting probabilities...")
    if len(X) > 50000:
        np.random.seed(42)
        idx = np.random.choice(len(X), 50000, replace=False)
        X_sample = X.iloc[idx]
        y_sample = y.iloc[idx] if isinstance(y, pd.Series) else y[idx]
    else:
        X_sample = X
        y_sample = y
        
    probs = model.predict_proba(X_sample)[:, 1]
    
    print("Computing ROC...")
    fpr, tpr, _ = roc_curve(y_sample, probs)
    idx = np.linspace(0, len(fpr) - 1, 100).astype(int)
    roc_data = {
        "fpr": fpr[idx].tolist(),
        "tpr": tpr[idx].tolist()
    }
    
    print("Computing PR Curve...")
    precision, recall, _ = precision_recall_curve(y_sample, probs)
    idx = np.linspace(0, len(precision) - 1, 100).astype(int)
    pr_data = {
        "recall": recall[idx].tolist(),
        "precision": precision[idx].tolist()
    }
    
    print("Computing Confusion Matrix...")
    threshold = 0.245
    preds = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_sample, preds).ravel()
    cm_data = {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp)
    }
    
    print("Computing Calibration Curve...")
    prob_true, prob_pred = calibration_curve(y_sample, probs, n_bins=10)
    cal_data = {
        "prob_pred": prob_pred.tolist(),
        "prob_true": prob_true.tolist()
    }
    
    metrics = {
        "roc": roc_data,
        "pr": pr_data,
        "confusion_matrix": cm_data,
        "calibration_curve": cal_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f)
        
    print(f"Saved metrics to {output_path}")

if __name__ == "__main__":
    generate_metrics()
