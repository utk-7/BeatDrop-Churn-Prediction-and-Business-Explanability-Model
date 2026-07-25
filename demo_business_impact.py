import pandas as pd
import joblib
import yaml
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
import business_impact

def main():
    print("Loading data...")
    df = pd.read_parquet('data/processed/customer_features.parquet')
    
    # We'll take a larger random sample to guarantee we get High/Medium/Low tiers
    df = df.sample(10000, random_state=42).copy()
    
    print("Loading model and metadata...")
    model = joblib.load('models/xgboost_model_v0.2.0.joblib')
    
    synthetic_cols = [
        'total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq', 
        'log_days', 'avg_secs_per_day', 'percent_complete', 'daily_unq_songs', 
        'engagement_trend_total_secs', 'engagement_trend_num_unq'
    ]
    CATEGORICAL_COLS = ['city', 'gender', 'age_clean', 'registered_via_clean', 'payment_method_id']
    
    X = df.drop(columns=['msno', 'is_churn'])
    X = X.drop(columns=[c for c in synthetic_cols if c in X.columns])
    
    for col in CATEGORICAL_COLS:
        if col in X.columns:
            X[col] = X[col].astype('category')
            
    num_cols = [c for c in X.columns if c not in CATEGORICAL_COLS]
    X[num_cols] = X[num_cols].fillna(0)
    
    print("Predicting probabilities...")
    df['churn_probability'] = model.predict_proba(X)[:, 1]
    
    print("Loading configs...")
    with open('config/business_params.yaml', 'r') as f:
        config = yaml.safe_load(f)
        
    with open('config/thresholds.yaml', 'r') as f:
        thresholds = yaml.safe_load(f)
        
    high_thresh = thresholds['risk_tiers']['high']['min_prob']
    med_thresh = thresholds['risk_tiers']['medium']['min_prob']
    
    def get_risk_tier(prob):
        if prob >= high_thresh:
            return 'High'
        elif prob >= med_thresh:
            return 'Medium'
        return 'Low'
        
    df['risk_tier'] = df['churn_probability'].apply(get_risk_tier)
    
    print("Applying Business Impact logic...")
    # Calculate CLV & EV
    df['estimated_clv'] = df.apply(lambda row: business_impact.estimate_clv(row, config), axis=1)
    df['expected_value'] = df.apply(
        lambda row: business_impact.calculate_expected_value(row['churn_probability'], row['estimated_clv'], config), 
        axis=1
    )
    
    # For demo, pretend 'plan_list_price' is a top SHAP driver for some, 'is_auto_renew' for others
    import random
    random.seed(42)
    def mock_action(row):
        drivers = random.choice([['plan_list_price'], ['is_auto_renew'], None])
        return business_impact.suggested_retention_action(row['risk_tier'], drivers, config)
        
    df['suggested_action'] = df.apply(mock_action, axis=1)
    
    # Extract examples
    high = df[df['risk_tier'] == 'High'].sort_values('expected_value', ascending=False).head(2)
    med = df[df['risk_tier'] == 'Medium'].sort_values('expected_value', ascending=False).head(2)
    low = df[df['risk_tier'] == 'Low'].sort_values('expected_value', ascending=False).head(1)
    
    demo_df = pd.concat([high, med, low])
    
    print("BEAT DROP PHASE 4 DEMONSTRATION")
    print("="*80)
    
    cols = ['msno', 'risk_tier', 'churn_probability', 'estimated_clv', 'expected_value', 'suggested_action']
    
    # Format for readability
    demo_df['churn_probability'] = demo_df['churn_probability'].apply(lambda x: f"{x:.4f}")
    demo_df['estimated_clv'] = demo_df['estimated_clv'].apply(lambda x: f"${x:,.2f}")
    demo_df['expected_value'] = demo_df['expected_value'].apply(lambda x: f"${x:,.2f}")
    
    print(demo_df[cols].to_string(index=False))
    print("="*80)

if __name__ == '__main__':
    main()
