import pandas as pd
import numpy as np
from datetime import datetime
import yaml

FEATURE_PIPELINE_VERSION = "0.1.0"

def load_config(config_path="config/feature_config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def build_demographic_features(members_df: pd.DataFrame, base_msno_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build demographic features for a specific set of users.
    Handles gender imputation, age bucketing, and registered_via rollup.
    """
    config = load_config()['feature_pipeline']
    min_age = config['age_bounds']['min_valid']
    max_age = config['age_bounds']['max_valid']
    reg_via_freq = config['registered_via_min_freq']
    
    df = pd.merge(base_msno_df, members_df, on='msno', how='left')
    
    # 1. Gender -> "Unknown" instead of null
    df['gender'] = df['gender'].fillna('Unknown')
    
    # 2. Age (bd) -> Bucket invalid ages
    def clean_age(age):
        if pd.isna(age) or age < min_age or age > max_age:
            return "Unknown/Invalid"
        return str(int(age))
        
    df['age_clean'] = df['bd'].apply(clean_age)
    
    # 3. registered_via rollup
    # We compute frequencies across the entire members_df passed to us
    freq = members_df['registered_via'].value_counts(normalize=True)
    valid_categories = freq[freq >= reg_via_freq].index
    
    def clean_reg_via(cat):
        if pd.isna(cat):
            return "Unknown"
        if cat in valid_categories:
            return str(int(cat))
        return "Other"
        
    df['registered_via_clean'] = df['registered_via'].apply(clean_reg_via)
    
    # Select only output features
    cols = ['msno', 'city', 'gender', 'age_clean', 'registered_via_clean']
    
    # Replace any remaining numerical nans in city
    df['city'] = df['city'].fillna(-1).astype(int).astype(str)
    df['city'] = df['city'].replace('-1', 'Unknown')
    
    return df[cols]


def build_transaction_features(transactions_df: pd.DataFrame, base_msno_df: pd.DataFrame, reference_date=None) -> pd.DataFrame:
    """
    Build transaction history features.
    Relies on transactions_df already being filtered <= reference_date.
    """
    ref_dt = pd.to_datetime(reference_date) if reference_date else pd.to_datetime('today')
    
    # Get last transaction per msno (transactions_df should already be deduplicated daily, 
    # but we take the absolute latest here)
    last_trans = transactions_df.sort_values('transaction_date').groupby('msno').tail(1)
    
    # Aggregate stats over history
    hist_stats = transactions_df.groupby('msno').agg(
        num_plan_changes=('plan_list_price', lambda x: (x.diff() != 0).sum() - 1 if len(x) > 1 else 0),
        num_payment_methods=('payment_method_id', 'nunique'),
        num_cancellations=('is_cancel', 'sum')
    ).reset_index()
    
    # Merge on base
    df = pd.merge(base_msno_df, last_trans, on='msno', how='left')
    df = pd.merge(df, hist_stats, on='msno', how='left')
    
    # Defaults for missing
    df['plan_list_price'] = df['plan_list_price'].fillna(0)
    df['payment_plan_days'] = df['payment_plan_days'].fillna(0)
    df['is_auto_renew'] = df['is_auto_renew'].fillna(0)
    df['payment_method_id'] = df['payment_method_id'].fillna(-1).astype(int).astype(str)
    df['payment_method_id'] = df['payment_method_id'].replace('-1', 'Unknown')
    
    df['num_plan_changes'] = df['num_plan_changes'].fillna(0)
    df['num_payment_methods'] = df['num_payment_methods'].fillna(0)
    df['num_cancellations'] = df['num_cancellations'].fillna(0)
    
    # Days since last transaction
    df['days_since_last_transaction'] = (ref_dt - df['transaction_date']).dt.days
    df['days_since_last_transaction'] = df['days_since_last_transaction'].fillna(-1) # -1 meaning no history
    
    cols = ['msno', 'plan_list_price', 'payment_plan_days', 'is_auto_renew', 
            'payment_method_id', 'num_plan_changes', 'num_payment_methods', 
            'num_cancellations', 'days_since_last_transaction']
    return df[cols]


def build_membership_tenure_features(members_df: pd.DataFrame, transactions_df: pd.DataFrame, base_msno_df: pd.DataFrame, reference_date=None) -> pd.DataFrame:
    """
    Build tenure and expiration features.
    """
    ref_dt = pd.to_datetime(reference_date) if reference_date else pd.to_datetime('today')
    
    # We need registration_init_time from members
    mem = members_df[['msno', 'registration_init_time']]
    
    # We need the max membership_expire_date from transactions up to the cutoff
    exp = transactions_df.groupby('msno')['membership_expire_date'].max().reset_index()
    
    df = pd.merge(base_msno_df, mem, on='msno', how='left')
    df = pd.merge(df, exp, on='msno', how='left')
    
    df['days_since_registration'] = (ref_dt - df['registration_init_time']).dt.days
    df['days_until_expire'] = (df['membership_expire_date'] - ref_dt).dt.days
    
    # Fill defaults
    df['days_since_registration'] = df['days_since_registration'].fillna(-1)
    df['days_until_expire'] = df['days_until_expire'].fillna(-999) # Very expired if missing
    
    return df[['msno', 'days_since_registration', 'days_until_expire']]


def build_engagement_features(logs_agg_df: pd.DataFrame, base_msno_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build recency/frequency/engagement features.
    logs_agg_df is already aggregated by etl.load_user_logs_agg.
    """
    df = pd.merge(base_msno_df, logs_agg_df, on='msno', how='left')
    
    # Fills NA with 0 for users with no logs
    cols_to_fill_0 = [c for c in df.columns if c != 'msno' and c != 'days_since_last_log']
    df[cols_to_fill_0] = df[cols_to_fill_0].fillna(0)
    
    # Recency missing = 999 days (very old)
    df['days_since_last_log'] = df['days_since_last_log'].fillna(999)
    
    # Trend ratios
    df['engagement_trend_secs_ratio'] = df['recent_avg_secs'] / (df['prior_avg_secs'] + 1e-5)
    df['engagement_trend_songs_ratio'] = df['recent_avg_songs'] / (df['prior_avg_songs'] + 1e-5)
    
    df['engagement_trend_secs_ratio'] = df['engagement_trend_secs_ratio'].fillna(0)
    df['engagement_trend_songs_ratio'] = df['engagement_trend_songs_ratio'].fillna(0)
    
    return df


def build_customer_feature_table(members_df: pd.DataFrame, transactions_df: pd.DataFrame, 
                               logs_agg_df: pd.DataFrame, base_msno_df: pd.DataFrame, 
                               reference_date=None) -> pd.DataFrame:
    """
    Orchestrate full feature engineering.
    """
    demo_feat = build_demographic_features(members_df, base_msno_df)
    trans_feat = build_transaction_features(transactions_df, base_msno_df, reference_date)
    tenure_feat = build_membership_tenure_features(members_df, transactions_df, base_msno_df, reference_date)
    engage_feat = build_engagement_features(logs_agg_df, base_msno_df)
    
    final_df = base_msno_df.copy()
    for feat_df in [demo_feat, trans_feat, tenure_feat, engage_feat]:
        final_df = pd.merge(final_df, feat_df, on='msno', how='left')
        
    return final_df
