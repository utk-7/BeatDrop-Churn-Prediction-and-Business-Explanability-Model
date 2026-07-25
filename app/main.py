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
    data_path = 'data/processed/customer_features.parquet'
    if not os.path.exists(data_path):
        raise RuntimeError(f"Data file not found at {data_path}")
    
    df = pd.read_parquet(data_path)
    # Store with msno as index for fast O(1) lookups
    app_state['customers_df'] = df.set_index('msno')
    
    # Sanity Check
    logger.info("Running startup sanity check...")
    X_full = explain.prepare_features_for_model(df)
    probs = model.predict_proba(X_full)[:, 1]
    
    high_th = app_state['thresholds']['high']['min_prob']
    med_th = app_state['thresholds']['medium']['min_prob']
    
    high_count = (probs >= high_th).sum()
    med_count = ((probs >= med_th) & (probs < high_th)).sum()
    total = len(probs)
    
    high_pct = (high_count / total) * 100
    med_pct = (med_count / total) * 100
    
    logger.info(f"Population Risk Distribution: High={high_pct:.2f}%, Medium={med_pct:.2f}%")
    if abs(high_pct - 5.0) > 2.0 or abs(med_pct - 10.0) > 5.0: # Expecting ~5% high, ~15% medium (which is 10% medium strictly) wait, threshold config says: "Top 5% to 15% risk" meaning medium is 10%.
        logger.warning(f"Sanity Check Warning: Risk tiers significantly deviate from intended 5%/15% split. High={high_pct:.2f}%, Medium={med_pct:.2f}%")
        
    yield
    # Cleanup on shutdown
    app_state.clear()


app = FastAPI(lifespan=lifespan, title="Beat Drop API")


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
    
    # Filters
    mask = pd.Series(True, index=df.index)
    if plan_type is not None:
        mask = mask & (df['payment_plan_days'] == plan_type)
        
    if tenure_bucket is not None:
        if tenure_bucket == "new":
            mask = mask & (df['days_since_registration'] < 30)
        elif tenure_bucket == "old":
            mask = mask & (df['days_since_registration'] >= 30)
            
    filtered_df = df[mask]
    if len(filtered_df) == 0:
        return {
            "total_customers": 0,
            "churn_rate": 0.0,
            "risk_tier_distribution": {"High": 0.0, "Medium": 0.0, "Low": 0.0}
        }
        
    # We will compute predictions on the subset
    # Note: Predicting on a huge subset dynamically is slow, but OK for this prototype phase
    X = explain.prepare_features_for_model(filtered_df)
    probs = app_state['model'].predict_proba(X)[:, 1]
    
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
    # As per prompt, this returns stored Phase 3 evaluation metrics for v0.2.0.
    # In a real setup this might fetch from MLflow. We'll return the documented values.
    return {
        "model_version": "0.2.0",
        "calibration": "Isotonic (CalibratedClassifierCV, cv=3)",
        "metrics": {
            "pr_auc": 0.4134,
            "brier_score": 0.0657,
            "f1_score": 0.3255 # Placeholder or historical
        }
    }


@app.get("/business-impact/top-actions", response_model=schemas.TopActionsResponse)
def get_top_actions(
    top_n: int = Query(10, le=100),
    discount_cost: Optional[float] = Query(None),
    retention_rate: Optional[float] = Query(None)
):
    df = app_state['customers_df']
    
    # For a real implementation, we would precompute EVs. 
    # Here we'll sample the first 5000 rows to keep it fast, or if we have computed all, just rank.
    # Let's predict for 5000 users to ensure response time is reasonable.
    sample_df = df.head(5000).copy()
    
    # Custom business params if provided
    custom_params = app_state['business_params'].copy()
    if discount_cost is not None:
        custom_params['business_impact']['discount_cost_percentage'] = discount_cost
    if retention_rate is not None:
        custom_params['business_impact']['retention_success_rate'] = retention_rate
        
    X = explain.prepare_features_for_model(sample_df)
    sample_df['churn_probability'] = app_state['model'].predict_proba(X)[:, 1]
    
    # Add msno back for output
    sample_df['msno'] = sample_df.index
    
    ranked_df = business_impact.build_prioritized_action_list(sample_df, custom_params)
    
    top_df = ranked_df.head(top_n)
    
    customers = []
    for _, row in top_df.iterrows():
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

