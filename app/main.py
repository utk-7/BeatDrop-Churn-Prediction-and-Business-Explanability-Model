import os
import sys
import yaml
import json
import joblib
import logging
import pandas as pd
import numpy as np
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import business_impact
import explain
from app import schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load configurations
    with open('config/thresholds.yaml', 'r') as f:
        thresholds_cfg = yaml.safe_load(f)
        app_state['thresholds'] = thresholds_cfg['risk_tiers']
        
    with open('config/business_params.yaml', 'r') as f:
        app_state['business_params'] = yaml.safe_load(f)
        
    with open('config/api_config.yaml', 'r') as f:
        app_state['api_config'] = yaml.safe_load(f)['api']
        
    with open('models/xgboost_metadata.json', 'r') as f:
        app_state['model_metadata'] = json.load(f)
        
    # Load Model
    logger.info("Loading model...")
    model_path = 'models/xgboost_model_v0.2.0.joblib'
    if not os.path.exists(model_path):
        raise RuntimeError(f"Model file not found at {model_path}")
    model = joblib.load(model_path)
    app_state['model'] = model
    
    # Initialize Explainer
    logger.info("Initializing SHAP explainer...")
    app_state['explainer'] = explain.get_explainer(model)
    
    # Load dataset into memory
    logger.info("Loading customer dataset into memory...")
    feature_table_path = "data/processed/customer_features.parquet"
    model_path = "models/xgboost_model_v0.2.0.joblib"
    
    app_state['artifacts_missing'] = False
    
    if not os.path.exists(feature_table_path) or not os.path.exists(model_path):
        logger.warning("ML artifacts (model/parquet) not found! Running in degraded mode.")
        app_state['artifacts_missing'] = True
        app_state['customers_df'] = pd.DataFrame()
        app_state['user_logs_df'] = pd.DataFrame()
        yield
        app_state.clear()
        return

    logger.info(f"Loading data from {feature_table_path}...")
    df = pd.read_parquet(feature_table_path)
    
    # Store df for quick lookups later (indexed by msno for fast retrieval)
    app_state['customers_df'] = df.set_index('msno')
    
    # Sanity Check & Precomputation
    logger.info("Precomputing model features and predictions for the entire dataset (~970k rows)...")
    X_full = explain.prepare_features_for_model(df)
    probs = model.predict_proba(X_full)[:, 1]
    df['churn_probability'] = probs
    
    logger.info("Precomputing business impact for the entire dataset (vectorized)...")
    config = app_state['business_params']
    # Vectorized CLV
    if 'actual_amount_paid' in df.columns:
        df['estimated_clv'] = df['actual_amount_paid'] * config['business_impact']['avg_customer_lifespan_months']
    else:
        df['estimated_clv'] = config['business_impact']['default_monthly_revenue'] * config['business_impact']['avg_customer_lifespan_months']
        
    # Vectorized EV
    success_rate = config['business_impact']['retention_success_rate']
    cost_pct = config['business_impact']['discount_cost_percentage']
    df['expected_value'] = (df['churn_probability'] * success_rate * df['estimated_clv']) - (cost_pct * df['estimated_clv'])
    
    # Store back to app_state
    app_state['customers_df'] = df.set_index('msno')
    logger.info(f"Successfully attached precomputed columns. Dataframe shape: {app_state['customers_df'].shape}")
    logger.info(f"Final columns: {list(app_state['customers_df'].columns)}")
    
    # Global SHAP Precomputation
    logger.info("Precomputing global SHAP values...")
    sample_size = min(5000, len(X_full))
    X_sample = X_full.sample(n=sample_size, random_state=42)
    shap_vals = app_state['explainer'].shap_values(X_sample)
    
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    mean_shap = shap_vals.mean(axis=0)
    
    global_drivers = []
    feature_names = X_sample.columns
    for i in range(len(feature_names)):
        global_drivers.append({
            "feature": feature_names[i],
            "impact": float(mean_abs_shap[i]),
            "direction": "High" if mean_shap[i] > 0 else "Low"
        })
    global_drivers.sort(key=lambda x: x["impact"], reverse=True)
    app_state['global_shap'] = global_drivers
    
    # Load User Logs
    logger.info("Loading user logs...")
    logs_path = 'data/raw/user_logs.csv'
    if os.path.exists(logs_path):
        app_state['user_logs_df'] = pd.read_csv(logs_path)
    else:
        app_state['user_logs_df'] = pd.DataFrame()
    
    high_th = app_state['thresholds']['high']['min_prob']
    med_th = app_state['thresholds']['medium']['min_prob']
    
    high_count = (probs >= high_th).sum()
    med_count = ((probs >= med_th) & (probs < high_th)).sum()
    total = len(probs)
    
    high_pct = (high_count / total) * 100
    med_pct = (med_count / total) * 100
    
    logger.info(f"Population Risk Distribution: High={high_pct:.2f}%, Medium={med_pct:.2f}%")
        
    yield
    # Cleanup on shutdown
    app_state.clear()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan, title="Beat Drop API")

allowed_origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
if os.getenv("ALLOWED_ORIGIN"):
    origin = os.getenv("ALLOWED_ORIGIN").strip().rstrip("/")
    allowed_origins.append(origin)

logger.info(f"Configured CORS Allowed Origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_risk_tier(prob: float) -> str:
    if prob >= app_state['thresholds']['high']['min_prob']:
        return 'High'
    elif prob >= app_state['thresholds']['medium']['min_prob']:
        return 'Medium'
    return 'Low'

def is_low_confidence(customer_row: pd.Series) -> bool:
    tenure_days = customer_row.get('days_since_registration', 0)
    return pd.isna(tenure_days) or tenure_days < app_state['api_config']['low_confidence_threshold_days']


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_version": app_state['model_metadata'].get('model_version'),
        "feature_pipeline_version": app_state['model_metadata'].get('feature_pipeline_version'),
        "thresholds_loaded": True
    }


@app.get("/customers/sample")
def get_sample_customers():
    df = app_state['customers_df']
    # Return 50 random msno strings for autocomplete
    sample = df.sample(n=min(50, len(df)), random_state=42)
    return {"msnos": sample.index.tolist()}


@app.get("/customers/{msno}", response_model=schemas.CustomerProfileResponse)
def get_customer(msno: str):
    df = app_state['customers_df']
    if msno not in df.index:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.loc[msno]
    # Handle NaNs gracefully by converting to None for optional fields if needed
    row_dict = row.replace({np.nan: None}).to_dict()
    row_dict['msno'] = msno
    return row_dict


@app.get("/customers/{msno}/usage-history")
def get_customer_usage(msno: str):
    """
    Returns the daily streaming usage history for a customer (if available in synthetic logs).
    """
    if 'user_logs_df' not in app_state or app_state['user_logs_df'].empty:
        return {"history": []}
        
    df = app_state['user_logs_df']
    customer_logs = df[df['msno'] == msno]
    
    if len(customer_logs) == 0:
        return {"history": []}
        
    history = []
    # Sort by date
    customer_logs = customer_logs.sort_values(by='date')
    for _, row in customer_logs.iterrows():
        date_str = str(row['date'])
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
        history.append({
            "date": date_str,
            "total_secs": float(row['total_secs']),
            "num_unq": int(row['num_unq'])
        })
        
    return {"history": history}


@app.get("/customers/{msno}/predict", response_model=schemas.PredictResponse)
def predict_customer(msno: str):
    df = app_state['customers_df']
    if msno not in df.index:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.loc[msno]
    
    # Convert to DataFrame for model
    row_df = pd.DataFrame([row])
    X = explain.prepare_features_for_model(row_df)
    
    prob = float(app_state['model'].predict_proba(X)[0, 1])
    risk_tier = get_risk_tier(prob)
    
    clv = business_impact.estimate_clv(row, app_state['business_params'])
    ev = business_impact.calculate_expected_value(prob, clv, app_state['business_params'])
    
    return {
        "msno": msno,
        "churn_probability": prob,
        "risk_tier": risk_tier,
        "estimated_clv": clv,
        "expected_value": ev,
        "low_confidence": is_low_confidence(row)
    }


@app.post("/predict/batch", response_model=schemas.BatchPredictResponse)
def predict_batch(request: schemas.BatchPredictRequest):
    msnos = request.msno_list
    max_batch = app_state['api_config']['max_batch_size']
    
    if not msnos:
        raise HTTPException(status_code=400, detail="Empty msno list")
    if len(msnos) > max_batch:
        raise HTTPException(status_code=400, detail=f"Batch size exceeds maximum of {max_batch}")
        
    df = app_state['customers_df']
    results = []
    
    for msno in msnos:
        if msno not in df.index:
            results.append({
                "msno": msno,
                "success": False,
                "error_message": "Customer not found"
            })
            continue
            
        row = df.loc[msno]
        row_df = pd.DataFrame([row])
        X = explain.prepare_features_for_model(row_df)
        
        try:
            prob = float(app_state['model'].predict_proba(X)[0, 1])
            risk_tier = get_risk_tier(prob)
            clv = business_impact.estimate_clv(row, app_state['business_params'])
            ev = business_impact.calculate_expected_value(prob, clv, app_state['business_params'])
            
            results.append({
                "msno": msno,
                "success": True,
                "churn_probability": prob,
                "risk_tier": risk_tier,
                "estimated_clv": clv,
                "expected_value": ev,
                "low_confidence": is_low_confidence(row)
            })
        except Exception as e:
            logger.error(f"Error predicting for msno {msno}: {str(e)}")
            results.append({
                "msno": msno,
                "success": False,
                "error_message": "Internal error during prediction"
            })
            
    return {"results": results}


@app.get("/customers/{msno}/explain", response_model=schemas.ExplainResponse)
def explain_customer(msno: str):
    df = app_state['customers_df']
    if msno not in df.index:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.loc[msno]
    row_df = pd.DataFrame([row])
    X = explain.prepare_features_for_model(row_df)
    
    top_n = app_state['api_config']['shap_top_n']
    top_drivers = explain.get_top_drivers(app_state['explainer'], X, top_n)
    
    return {
        "msno": msno,
        "top_drivers": top_drivers
    }


@app.get("/customers/{msno}/suggested-action", response_model=schemas.SuggestedActionResponse)
def get_suggested_action(msno: str):
    df = app_state['customers_df']
    if msno not in df.index:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.loc[msno]
    row_df = pd.DataFrame([row])
    X = explain.prepare_features_for_model(row_df)
    
    # 1. Get prediction to determine tier
    prob = float(app_state['model'].predict_proba(X)[0, 1])
    risk_tier = get_risk_tier(prob)
    
    # 2. Get real SHAP drivers
    top_n = app_state['api_config']['shap_top_n']
    top_drivers = explain.get_top_drivers(app_state['explainer'], X, top_n)
    
    # 3. Call business logic
    action = business_impact.suggested_retention_action(risk_tier, top_drivers, app_state['business_params'])
    
    return {
        "msno": msno,
        "risk_tier": risk_tier,
        "suggested_action": action,
        "top_drivers_used": top_drivers
    }


@app.get("/cohort/stats", response_model=schemas.CohortStatsResponse)
def get_cohort_stats(plan_type: Optional[int] = Query(None), tenure_bucket: Optional[str] = Query(None)):
    """
    Very basic aggregate stats. 
    In a real app, this would use a database. We will simulate by predicting on a subset.
    """
    df = app_state['customers_df']
    
    if app_state.get('artifacts_missing', False) or 'churn_probability' not in df.columns:
        return {
            "total_customers": 0,
            "churn_rate": 0.0,
            "risk_tier_distribution": {"High": 0.0, "Medium": 0.0, "Low": 0.0}
        }
        
    # Optimize: Use numpy arrays for fast masking instead of full DataFrame copies
    probs = df['churn_probability'].values
    
    if plan_type is not None or tenure_bucket is not None:
        mask = np.ones(len(df), dtype=bool)
        if plan_type is not None:
            mask &= (df['payment_plan_days'] == plan_type).values
            
        if tenure_bucket is not None:
            if tenure_bucket == "new":
                mask &= (df['days_since_registration'] < 30).values
            elif tenure_bucket == "old":
                mask &= (df['days_since_registration'] >= 30).values
                
        probs = probs[mask]
        
    if len(probs) == 0:
        return {
            "total_customers": 0,
            "churn_rate": 0.0,
            "risk_tier_distribution": {"High": 0.0, "Medium": 0.0, "Low": 0.0}
        }
        
    high_th = app_state['thresholds']['high']['min_prob']
    med_th = app_state['thresholds']['medium']['min_prob']
    
    churn_rate = np.mean(probs)
    
    high_count = (probs >= high_th).sum()
    med_count = ((probs >= med_th) & (probs < high_th)).sum()
    low_count = (probs < med_th).sum()
    total = len(probs)
    
    return {
        "total_customers": total,
        "churn_rate": float(churn_rate),
        "risk_tier_distribution": {
            "High": float(high_count / total),
            "Medium": float(med_count / total),
            "Low": float(low_count / total)
        }
    }


@app.get("/model/performance")
def get_model_performance():
    # Load precomputed metric arrays
    metrics_path = 'models/model_metrics.json'
    curves = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            curves = json.load(f)
            
    # Include global shap
    global_drivers = app_state.get('global_shap', [])[:15]
            
    return {
        "model_version": "0.2.0",
        "calibration": "Isotonic (CalibratedClassifierCV, cv=3)",
        "metrics": {
            "pr_auc": 0.4134,
            "brier_score": 0.0657,
            "f1_score": 0.3255
        },
        "curves": curves,
        "global_shap": global_drivers
    }


@app.get("/business-impact/top-actions", response_model=schemas.TopActionsResponse)
def get_top_actions(
    top_n: int = Query(10, le=100),
    discount_cost: Optional[float] = Query(None),
    retention_rate: Optional[float] = Query(None),
    plan_type: Optional[int] = Query(None),
    tenure_bucket: Optional[str] = Query(None),
    diversify: Optional[bool] = Query(False)
):
    df = app_state['customers_df']
    
    if app_state.get('artifacts_missing', False) or 'churn_probability' not in df.columns:
        return {"actions": []}
        
    # Filter dataset using fast numpy masking if segment filters provided
    if plan_type is not None or tenure_bucket is not None:
        mask = np.ones(len(df), dtype=bool)
        if plan_type is not None:
            mask &= (df['payment_plan_days'] == plan_type).values
            
        if tenure_bucket is not None:
            if tenure_bucket == "new":
                mask &= (df['days_since_registration'] < 30).values
            elif tenure_bucket == "old":
                mask &= (df['days_since_registration'] >= 30).values
                
        # Optimize: Only copy the columns we need from the filtered subset
        sample_df = df.iloc[mask][['churn_probability', 'estimated_clv', 'expected_value', 'days_since_registration']].copy()
    else:
        sample_df = df[['churn_probability', 'estimated_clv', 'expected_value', 'days_since_registration']].copy()
    
    custom_params = app_state['business_params'].copy()
    
    if discount_cost is not None or retention_rate is not None:
        if discount_cost is not None:
            custom_params['business_impact']['discount_cost_percentage'] = discount_cost
        if retention_rate is not None:
            custom_params['business_impact']['retention_success_rate'] = retention_rate
            
        success_rate = retention_rate if retention_rate is not None else custom_params['business_impact'].get('retention_success_rate', 0.3)
        cost_pct = discount_cost if discount_cost is not None else custom_params['business_impact'].get('discount_cost_percentage', 0.05)
        
        sample_df['expected_value'] = (sample_df['churn_probability'] * success_rate * sample_df['estimated_clv']) - (cost_pct * sample_df['estimated_clv'])
        
    sample_df['msno'] = sample_df.index
    
    if diversify:
        # 1. Top 4 High-Risk, Highest EV
        high_th = app_state['thresholds']['high']['min_prob']
        med_th = app_state['thresholds']['medium']['min_prob']
        
        top_high = sample_df[sample_df['churn_probability'] >= high_th].nlargest(4, 'expected_value')
        
        # 2. Top 3 Medium-Risk
        top_med = sample_df[(sample_df['churn_probability'] >= med_th) & (sample_df['churn_probability'] < high_th)].nlargest(3, 'expected_value')
        
        # 3. Top 3 Low-Risk, New (< 180 days)
        top_low_new = sample_df[(sample_df['churn_probability'] < med_th) & (sample_df['days_since_registration'] < 180)].nlargest(3, 'expected_value')
        
        top_df = pd.concat([top_high, top_med, top_low_new])
        
        # Fallback if we didn't find enough
        if len(top_df) < top_n:
            remaining = top_n - len(top_df)
            used_msnos = top_df.index
            fillers = sample_df[~sample_df.index.isin(used_msnos)].nlargest(remaining, 'expected_value')
            top_df = pd.concat([top_df, fillers])
    else:
        top_df = sample_df.nlargest(top_n, 'expected_value')
    
    ranked_df = business_impact.build_prioritized_action_list(top_df, custom_params)
    
    customers = []
    for _, row in ranked_df.iterrows():
        customers.append({
            "msno": row['msno'],
            "expected_value": row['expected_value'],
            "churn_probability": row['churn_probability'],
            "estimated_clv": row['estimated_clv']
        })
        
    return {
        "customers": customers,
        "assumptions_used": custom_params['business_impact']
    }


@app.get("/model/global-shap")
def get_global_shap():
    """
    Returns the precomputed global SHAP drivers across the dataset.
    """
    if 'global_shap' not in app_state:
        raise HTTPException(status_code=503, detail="Global SHAP data not yet computed")
    return {"drivers": app_state['global_shap'][:15]}


@app.get("/customers/sample")
def get_customer_sample(limit: int = 50):
    """
    Returns a sample of valid MSNOs that do not contain path-breaking URL characters 
    (like '/') to make testing and frontend search autocomplete easier.
    """
    df = app_state['customers_df']
    safe_msnos = [m for m in df.index if '/' not in m][:limit]
    return {"msnos": safe_msnos}


@app.post("/customers/{msno}/simulate", response_model=schemas.PredictResponse)
def simulate_customer(msno: str, req: schemas.SimulateRequest):
    """
    Simulates a new churn probability for a customer given feature overrides.
    """
    df = app_state['customers_df']
    if msno not in df.index:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.loc[msno].copy()
    
    # Apply overrides
    if req.plan_list_price is not None:
        row['plan_list_price'] = req.plan_list_price
    if req.payment_plan_days is not None:
        row['payment_plan_days'] = req.payment_plan_days
    if req.is_auto_renew is not None:
        row['is_auto_renew'] = req.is_auto_renew
    if req.days_since_registration is not None:
        row['days_since_registration'] = req.days_since_registration
        
    # Convert to DataFrame for model
    row_df = pd.DataFrame([row])
    X = explain.prepare_features_for_model(row_df)
    
    prob = float(app_state['model'].predict_proba(X)[0, 1])
    risk_tier = get_risk_tier(prob)
    
    clv = business_impact.estimate_clv(row, app_state['business_params'])
    ev = business_impact.calculate_expected_value(prob, clv, app_state['business_params'])
    
    return {
        "msno": msno,
        "churn_probability": prob,
        "risk_tier": risk_tier,
        "estimated_clv": clv,
        "expected_value": ev,
        "low_confidence": is_low_confidence(row)
    }


