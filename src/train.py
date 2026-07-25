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
    
    # Cast categorical columns to category dtype for XGBoost
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
    print("Training Final XGBoost Model...")
    
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'aucpr',
        'tree_method': 'hist',
        'enable_categorical': True,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        **best_params
    }
    
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True)
    
    with mlflow.start_run(run_name="Final_XGBoost"):
        mlflow.log_params(params)
        
        bst = xgb.train(params, dtrain, num_boost_round=200, evals=[(dtest, 'test')], early_stopping_rounds=20, verbose_eval=False)
        
        y_prob = bst.predict(dtest)
        
        metrics, cm = evaluate_model(y_test, y_prob)
        mlflow.log_metrics(metrics)
        print(f"XGBoost PR-AUC: {metrics['pr_auc']:.4f}")
        print(f"XGBoost Brier Score: {metrics['brier_score']:.4f}")
        
        paths = plot_and_save_curves(y_test, y_prob, prefix="XGBoost")
        for k, p in paths.items():
            mlflow.log_artifact(p)
            
        # Feature importance
        fscore = bst.get_score(importance_type='gain')
        mlflow.log_dict(fscore, "feature_importance_gain.json")
        
        # Save model via joblib
        os.makedirs("models", exist_ok=True)
        model_path = "models/xgboost_model_v0.1.0.joblib"
        joblib.dump(bst, model_path)
        
        # Also log to MLflow
        mlflow.xgboost.log_model(bst, "model")
        
    return bst, y_prob


def propose_risk_thresholds(y_prob, y_true):
    """
    Generate threshold recommendations based on actual predicted probabilities on the test set.
    """
    print("\nProposing Risk Thresholds...")
    
    # We want to identify the top risk tiers. 
    # High risk = top 10% of predicted probabilities
    # Medium risk = 10% to 30% percentile
    # Low risk = bottom 70%
    
    p90 = np.percentile(y_prob, 90)
    p70 = np.percentile(y_prob, 70)
    
    print(f"90th percentile predicted prob (High Risk Cutoff): {p90:.4f}")
    print(f"70th percentile predicted prob (Medium Risk Cutoff): {p70:.4f}")
    
    # Update config/thresholds.yaml
    os.makedirs("config", exist_ok=True)
    yaml_content = f"""# config/thresholds.yaml
# Derived from actual model output on {datetime.now().strftime('%Y-%m-%d')}
# Model version: 0.1.0 (XGBoost)
# Note: These values replace the placeholder 0.3/0.6 guesses.

risk_tiers:
  high:
    min_prob: {p90:.4f}
    description: "Top 10% risk customers. Require immediate intervention."
  medium:
    min_prob: {p70:.4f}
    max_prob: {p90:.4f}
    description: "70th to 90th percentile risk. Need monitoring and light engagement."
  low:
    min_prob: 0.0
    max_prob: {p70:.4f}
    description: "Bottom 70% risk. Generally healthy."
"""
    with open("config/thresholds.yaml", "w") as f:
        f.write(yaml_content)
    
    # Plot probability distribution
    plt.figure()
    sns.histplot(y_prob, bins=50, kde=False)
    plt.axvline(p90, color='red', linestyle='--', label='High Risk')
    plt.axvline(p70, color='orange', linestyle='--', label='Medium Risk')
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
        "model_version": "0.1.0",
        "training_date": datetime.utcnow().isoformat(),
        "feature_pipeline_version": "0.1.0", # from Phase 2
        "notes": "WARNING: Engagement trend features heavily rely on synthetic data. Re-validate their importance when real logs are used."
    }
    with open("models/xgboost_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("Training phase complete. Run `mlflow ui` to view experiments.")

if __name__ == "__main__":
    main()
