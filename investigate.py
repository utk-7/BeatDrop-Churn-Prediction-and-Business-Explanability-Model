import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, roc_auc_score
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
import matplotlib.pyplot as plt
import os
import sys
import yaml

def load_data():
    df = pd.read_parquet("data/processed/customer_features.parquet")
    X = df.drop(columns=['msno', 'is_churn'])
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = X[col].astype('category')
    y = df['is_churn']
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

def evaluate(y_true, y_prob):
    pr_auc = average_precision_score(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)
    preds = (y_prob > 0.5).astype(int)
    f1 = f1_score(y_true, preds)
    return pr_auc, brier, f1

def main():
    os.makedirs('investigation', exist_ok=True)
    X_train, X_test, y_train, y_test = load_data()
    
    # LOAD MODEL
    bst = joblib.load("models/xgboost_model_v0.1.0.joblib")
    dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True)
    y_prob_orig = bst.predict(dtest)
    orig_pr_auc, orig_brier, orig_f1 = evaluate(y_test, y_prob_orig)

    print("--- 1. SYNTHETIC DATA LEAKAGE ---")
    print("Nature of Leakage: The user_logs data is synthetic. In EDA, it was observed that for the first ~25% of the data, the synthetic generation logic cleanly aligned engagement trends with the target variable, meaning 'churned' users had artificially generated perfectly declining logs, and 'retained' had steady logs. This isn't target label mixing, but a 'too-perfect' synthetic behavioral signal that makes the model over-perform compared to real data.")
    
    scores = bst.get_score(importance_type='gain')
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:15]
    
    # Known synthetic features from user_logs
    synthetic_cols = ['total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 
                      'log_days', 'avg_secs_per_day', 'percent_complete', 'daily_unq_songs', 
                      'engagement_trend_total_secs', 'engagement_trend_num_unq']
    
    print("\nTop 15 Features by Gain:")
    for feat, gain in sorted_scores:
        is_synth = "SYNTHETIC" if feat in synthetic_cols else "REAL"
        print(f" - {feat}: {gain:.2f} ({is_synth})")
        
    print("\nRetraining without synthetic features...")
    X_train_real = X_train.drop(columns=[c for c in synthetic_cols if c in X_train.columns])
    X_test_real = X_test.drop(columns=[c for c in synthetic_cols if c in X_test.columns])
    
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)
    
    # Train proxy model (using standard good params)
    dtrain_real = xgb.DMatrix(X_train_real, label=y_train, enable_categorical=True)
    dtest_real = xgb.DMatrix(X_test_real, label=y_test, enable_categorical=True)
    
    params = {
        'objective': 'binary:logistic', 'eval_metric': 'aucpr', 'tree_method': 'hist',
        'enable_categorical': True, 'scale_pos_weight': scale_pos_weight,
        'learning_rate': 0.05, 'max_depth': 6, 'subsample': 0.8, 'colsample_bytree': 0.8, 'random_state': 42
    }
    
    bst_real = xgb.train(params, dtrain_real, num_boost_round=150, evals=[(dtest_real, 'test')], early_stopping_rounds=20, verbose_eval=False)
    y_prob_real = bst_real.predict(dtest_real)
    real_pr_auc, real_brier, real_f1 = evaluate(y_test, y_prob_real)
    
    print(f"Original PR-AUC: {orig_pr_auc:.4f} | Real-only PR-AUC: {real_pr_auc:.4f}")
    print(f"Original F1:     {orig_f1:.4f} | Real-only F1:     {real_f1:.4f}")
    print(f"Original Brier:  {orig_brier:.4f} | Real-only Brier:  {real_brier:.4f}")

    print("\n--- 2. RISK TIER THRESHOLDS ---")
    print("The percentiles were computed over the FULL test set (churned + retained).")
    
    high_threshold = np.percentile(y_prob_orig, 90)
    med_threshold = np.percentile(y_prob_orig, 70)
    
    n_total = len(y_prob_orig)
    n_high = np.sum(y_prob_orig > high_threshold)
    n_med = np.sum((y_prob_orig > med_threshold) & (y_prob_orig <= high_threshold))
    n_low = np.sum(y_prob_orig <= med_threshold)
    
    print(f"Thresholds -> High: >{high_threshold:.4f}, Medium: >{med_threshold:.4f}")
    print(f"High Risk Customer Count: {n_high} ({(n_high/n_total)*100:.1f}%)")
    print(f"Medium Risk Customer Count: {n_med} ({(n_med/n_total)*100:.1f}%)")
    print(f"Low Risk Customer Count: {n_low} ({(n_low/n_total)*100:.1f}%)")
    print(f"Since we know real churn is ~5.8%, placing 30% of all users in Medium+High risk flags WAY too many people, leading to high false positives and wasted retention budget.")
    
    plt.figure(figsize=(8,4))
    plt.hist(y_prob_orig, bins=50, alpha=0.7)
    plt.axvline(high_threshold, color='r', linestyle='dashed', linewidth=1, label='High (90th pct)')
    plt.axvline(med_threshold, color='orange', linestyle='dashed', linewidth=1, label='Med (70th pct)')
    plt.title("Distribution of Predicted Probabilities (Full Test Set)")
    plt.legend()
    plt.savefig('investigation/prob_hist.png')

    print("\n--- 3. MODEL CALIBRATION ---")
    prob_true, prob_pred = calibration_curve(y_test, y_prob_orig, n_bins=10)
    plt.figure(figsize=(8,6))
    plt.plot(prob_pred, prob_true, marker='o', label='XGBoost Original')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    
    # Assess calibration
    print("Calibration Curve (Binned):")
    for pt, pp in zip(prob_true, prob_pred):
        print(f"  Pred Prob: {pp:.3f} -> Actual Churn Rate: {pt:.3f}")
        
    print("\nApplying Isotonic Regression (CalibratedClassifierCV proxy) on holdout probabilities...")
    # To properly simulate this without a huge retrain, we use 5-fold CV to get out-of-fold predictions on train set to fit Isotonic
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(y_train))
    
    for train_idx, val_idx in skf.split(X_train, y_train):
        dtr = xgb.DMatrix(X_train.iloc[train_idx], label=y_train.iloc[train_idx], enable_categorical=True)
        dva = xgb.DMatrix(X_train.iloc[val_idx], label=y_train.iloc[val_idx], enable_categorical=True)
        b = xgb.train(params, dtr, num_boost_round=100)
        oof_preds[val_idx] = b.predict(dva)
        
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(oof_preds, y_train)
    y_prob_calibrated = iso.predict(y_prob_orig)
    
    cal_pr_auc, cal_brier, cal_f1 = evaluate(y_test, y_prob_calibrated)
    print(f"Uncalibrated Brier: {orig_brier:.4f}")
    print(f"Calibrated Brier (Isotonic): {cal_brier:.4f}")
    
    prob_true_cal, prob_pred_cal = calibration_curve(y_test, y_prob_calibrated, n_bins=10)
    plt.plot(prob_pred_cal, prob_true_cal, marker='x', label='XGBoost Calibrated (Isotonic)')
    plt.legend()
    plt.title("Calibration Curve")
    plt.savefig('investigation/calibration_curve.png')

if __name__ == "__main__":
    main()
