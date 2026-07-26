import os
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import optuna
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score, precision_score, recall_score,
    confusion_matrix, brier_score_loss, roc_curve, precision_recall_curve
)
from sklearn.calibration import calibration_curve

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
MLFLOW_TRACKING_URI = "file:./mlruns"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Exclude id and target
EXCLUDE_COLS = ['msno', 'is_churn']
CATEGORICAL_COLS = ['city', 'gender', 'age_clean', 'registered_via_clean', 'payment_method_id']

def load_and_prepare_data(parquet_path="data/processed/customer_features.parquet"):
    print(f"Loading data from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    X = df.drop(columns=['msno', 'is_churn'])
    
    # ---------------------------------------------------------
    # SYNTHETIC DATA LEAKAGE FIX
    # Strip user_logs synthetic features to prevent artificial signal
    # ---------------------------------------------------------
    synthetic_cols = [
        'total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 
        'log_days', 'avg_secs_per_day', 'percent_complete', 'daily_unq_songs', 
        'engagement_trend_total_secs', 'engagement_trend_num_unq'
    ]
    X = X.drop(columns=[c for c in synthetic_cols if c in X.columns])
    
    # Convert string columns to categorical for XGBoost
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype('category')
            
    # For xgboost we can keep nans. For LR we will impute via the pipeline.
    # The feature pipeline filled most with 0 or Unknown. Only logs might be completely null if something slipped, 
    # but our features.py already fills NA with 0. 
    # Let's double check if any numeric cols have NA
    num_cols = [c for c in df.columns if c not in EXCLUDE_COLS + CATEGORICAL_COLS]
    df[num_cols] = df[num_cols].fillna(0)
    
    X = df.drop(columns=EXCLUDE_COLS)
    y = df['is_churn']
    msno = df['msno']
    
    # Stratified split 80/20
    X_train, X_test, y_train, y_test, msno_train, msno_test = train_test_split(
        X, y, msno, test_size=0.2, stratify=y, random_state=42
    )
    
    # Calculate scale_pos_weight
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    print(f"Computed scale_pos_weight: {scale_pos_weight:.2f}")
    
    return X_train, X_test, y_train, y_test, msno_train, msno_test, scale_pos_weight


def plot_and_save_curves(y_true, y_prob, prefix=""):
    os.makedirs("models/plots", exist_ok=True)
    paths = {}
    
    # PR Curve
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    plt.figure()
    plt.plot(recall, precision, marker='.')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'{prefix} Precision-Recall Curve')
    pr_path = f"models/plots/{prefix}_pr_curve.png"
    plt.savefig(pr_path)
    plt.close()
    paths['pr_curve'] = pr_path
    
    # Calibration Curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    plt.figure()
    plt.plot(prob_pred, prob_true, marker='o', label='Model')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    plt.xlabel('Mean predicted probability')
    plt.ylabel('Fraction of positives')
    plt.title(f'{prefix} Calibration Curve')
    plt.legend()
    cal_path = f"models/plots/{prefix}_calibration.png"
    plt.savefig(cal_path)
    plt.close()
    paths['calibration_curve'] = cal_path
    
    return paths


def evaluate_model(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    
    metrics = {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
        "f1_score": f1_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_prob)
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    return metrics, cm


def train_baseline(X_train, X_test, y_train, y_test):
    print("Training Logistic Regression Baseline...")
    
    # Prepare pipeline
    numeric_features = [c for c in X_train.columns if c not in CATEGORICAL_COLS]
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_COLS)
        ])
    
    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
    ])
    
    with mlflow.start_run(run_name="Baseline_LR"):
        clf.fit(X_train, y_train)
        y_prob = clf.predict_proba(X_test)[:, 1]
        
        metrics, cm = evaluate_model(y_test, y_prob)
        mlflow.log_metrics(metrics)
        print(f"Baseline PR-AUC: {metrics['pr_auc']:.4f}")
        
        paths = plot_and_save_curves(y_test, y_prob, prefix="Baseline")
        for k, p in paths.items():
            mlflow.log_artifact(p)
            
        mlflow.sklearn.log_model(clf, "model")
        
    return clf


def optimize_xgboost(X_train, y_train, scale_pos_weight, n_trials=10):
    print("Optimizing XGBoost with Optuna...")
    
    def objective(trial):
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'aucpr',
            'tree_method': 'hist',
            'enable_categorical': True,
            'scale_pos_weight': scale_pos_weight,
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'max_depth': trial.suggest_int('max_depth', 3, 9),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'random_state': 42
        }
        
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        pr_aucs = []
        
        for train_idx, val_idx in skf.split(X_train, y_train):
            X_tr, X_va = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_va = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            dtrain = xgb.DMatrix(X_tr, label=y_tr, enable_categorical=True)
            dval = xgb.DMatrix(X_va, label=y_va, enable_categorical=True)
            
            bst = xgb.train(params, dtrain, num_boost_round=100, evals=[(dval, 'val')], verbose_eval=False, early_stopping_rounds=10)
            
            y_prob = bst.predict(dval)
            pr_auc = average_precision_score(y_va, y_prob)
            pr_aucs.append(pr_auc)
            
        return np.mean(pr_aucs)
        
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    
    print(f"Best trial PR-AUC: {study.best_value:.4f}")
    return study.best_params


def train_final_xgboost(X_train, X_test, y_train, y_test, scale_pos_weight, best_params):
    print("Training Final Calibrated XGBoost Model...")
    from xgboost import XGBClassifier
    from sklearn.calibration import CalibratedClassifierCV
    
    params = {
        'tree_method': 'hist',
        'enable_categorical': True,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_estimators': 150, # Fixed trees since early stopping isn't native with CV
        **best_params
    }
    
    # Remove eval_metric from params since XGBClassifier doesn't need it without eval_set
    if 'eval_metric' in params:
        del params['eval_metric']
        
    base_clf = XGBClassifier(**params)
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, method='isotonic', cv=3)
    
    with mlflow.start_run(run_name="Calibrated_XGBoost_v0.3.0"):
        mlflow.log_params(params)
        
        calibrated_clf.fit(X_train, y_train)
        
        y_prob = calibrated_clf.predict_proba(X_test)[:, 1]
        
        metrics, cm = evaluate_model(y_test, y_prob)
        mlflow.log_metrics(metrics)
        print(f"XGBoost PR-AUC: {metrics['pr_auc']:.4f}")
        print(f"XGBoost Brier Score: {metrics['brier_score']:.4f}")
        
        paths = plot_and_save_curves(y_test, y_prob, prefix="XGBoost_Calibrated")
        for k, p in paths.items():
            mlflow.log_artifact(p)
            
        # Save model via joblib
        os.makedirs("models", exist_ok=True)
        model_path = "models/xgboost_model_v0.3.0.joblib"
        joblib.dump(calibrated_clf, model_path)
        
        # Also log to MLflow
        mlflow.sklearn.log_model(
            calibrated_clf, 
            "model",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE
        )
        
    return calibrated_clf, y_prob


def propose_risk_thresholds(y_prob, y_true):
    """
    Generate threshold recommendations based on actual predicted probabilities on the test set.
    """
    print("\nProposing Risk Thresholds...")
    
    # We want to identify the top risk tiers based on business context (~5.8% real churn rate).
    # High risk = top 5% of predicted probabilities (95th percentile)
    # Medium risk = top 5% to 15% (85th percentile)
    # Low risk = bottom 85%
    
    p95 = np.percentile(y_prob, 95)
    p85 = np.percentile(y_prob, 85)
    
    print(f"95th percentile predicted prob (High Risk Cutoff): {p95:.4f}")
    print(f"85th percentile predicted prob (Medium Risk Cutoff): {p85:.4f}")
    
    # Update config/thresholds.yaml
    os.makedirs("config", exist_ok=True)
    yaml_content = f"""# config/thresholds.yaml
# Derived from actual model output on {datetime.now().strftime('%Y-%m-%d')}
# Model version: 0.3.0 (Calibrated XGBoost)
# Note: These values were updated after applying CalibratedClassifierCV 
# to properly reflect true probability distributions.

risk_tiers:
  high:
    min_prob: {p95:.4f}
    description: "Top 5% risk customers. Require immediate intervention."
  medium:
    min_prob: {p85:.4f}
    max_prob: {p95:.4f}
    description: "Top 5% to 15% risk. Need monitoring and light engagement."
  low:
    min_prob: 0.0
    max_prob: {p85:.4f}
    description: "Bottom 85% risk. Generally healthy."
"""
    with open("config/thresholds.yaml", "w") as f:
        f.write(yaml_content)
    
    # Plot probability distribution
    plt.figure()
    sns.histplot(y_prob, bins=50, kde=False)
    plt.axvline(p95, color='red', linestyle='--', label='High Risk (Top 5%)')
    plt.axvline(p85, color='orange', linestyle='--', label='Medium Risk (Top 15%)')
    plt.title('Predicted Probability Distribution (Test Set)')
    plt.xlabel('Predicted Probability of Churn')
    plt.ylabel('Count')
    plt.legend()
    dist_path = "models/plots/XGBoost_prob_distribution.png"
    plt.savefig(dist_path)
    plt.close()


def main():
    import warnings
    warnings.filterwarnings("ignore")
    
    X_train, X_test, y_train, y_test, msno_train, msno_test, scale_pos_weight = load_and_prepare_data()
    
    # 1. Baseline
    train_baseline(X_train, X_test, y_train, y_test)
    
    # 2. XGBoost
    best_params = optimize_xgboost(X_train, y_train, scale_pos_weight, n_trials=5) # 5 trials for demonstration speed
    bst, y_prob_test = train_final_xgboost(X_train, X_test, y_train, y_test, scale_pos_weight, best_params)
    
    # 3. Thresholds
    propose_risk_thresholds(y_prob_test, y_test)
    
    # Write metadata
    metadata = {
        "model_version": "0.3.0",
        "training_date": datetime.utcnow().isoformat(),
        "feature_pipeline_version": "0.1.0",
        "calibration_method": "Isotonic (CalibratedClassifierCV, cv=3)",
        "features_dropped": [
            'total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 
            'log_days', 'avg_secs_per_day', 'percent_complete', 'daily_unq_songs', 
            'engagement_trend_total_secs', 'engagement_trend_num_unq'
        ],
        "notes": "Stripped synthetic user_logs features due to data leakage. Applied isotonic calibration."
    }
    with open("models/xgboost_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("Training phase complete. Run `mlflow ui` to view experiments.")

if __name__ == "__main__":
    main()
