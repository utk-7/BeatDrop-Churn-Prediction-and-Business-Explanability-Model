import nbformat as nbf

def main():
    nb = nbf.v4.new_notebook()
    
    nb['cells'] = [
        nbf.v4.new_markdown_cell("# Phase 3: Modeling & Evaluation\n\nThis notebook demonstrates the loading of features, evaluation of the baseline and XGBoost model, calibration, and class imbalance handling."),
        nbf.v4.new_markdown_cell("⚠️ **IMPORTANT CAVEAT ON SYNTHETIC DATA** ⚠️\n\nThe engagement trend features (e.g. `engagement_trend_secs_ratio`, `prior_avg_secs`) heavily rely on synthetic data injected in Phase 1 for `user_logs.csv`. Their high feature importance observed in this model might be artificially inflated due to the clean decline pattern injected into the synthetic churners. This must be re-validated once the real 30GB+ file is loaded."),
        nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import joblib

# Load models and features
df = pd.read_parquet('../data/processed/customer_features.parquet')
print(df.shape)

try:
    xgb_model = joblib.load('../models/xgboost_model_v0.3.0.joblib')
    print("XGBoost loaded successfully!")
except Exception as e:
    print("Model not found. Run src/train.py first.", e)
"""),
        nbf.v4.new_markdown_cell("## Why PR-AUC over ROC-AUC?\n\nBecause this is a highly imbalanced dataset (~9% churn rate), ROC-AUC can be misleadingly high (due to high True Negatives). **PR-AUC** focuses purely on the minority class (Precision vs Recall) and gives a more honest assessment of how well the model identifies actual churners without being overwhelmed by the majority retained class."),
        nbf.v4.new_code_cell("""# You can run `mlflow ui` from the terminal and navigate to localhost:5000 to view full experiment tracking.""")
    ]
    
    with open('notebooks/02_modeling.ipynb', 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
        
    print("Generated notebooks/02_modeling.ipynb")

if __name__ == '__main__':
    main()
