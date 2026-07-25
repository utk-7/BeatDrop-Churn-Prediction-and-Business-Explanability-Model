import pandas as pd
import duckdb
import os
import yaml
from datetime import datetime

def load_config(config_path="config/feature_config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_members(members_path="data/raw/members_v3.csv") -> pd.DataFrame:
    """Load members table and parse dates."""
    if not os.path.exists(members_path):
        raise FileNotFoundError(f"Missing {members_path}")
    df = pd.read_csv(members_path)
    df['registration_init_time'] = pd.to_datetime(df['registration_init_time'], format='%Y%m%d', errors='coerce')
    return df

def load_transactions(transactions_path="data/raw/transactions_v2.csv", reference_date=None) -> pd.DataFrame:
    """
    Load transactions, handle same-day duplicates (take last by sequence),
    and strictly filter out anything after reference_date to prevent future leakage.
    """
    if not os.path.exists(transactions_path):
        raise FileNotFoundError(f"Missing {transactions_path}")
    df = pd.read_csv(transactions_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%Y%m%d', errors='coerce')
    df['membership_expire_date'] = pd.to_datetime(df['membership_expire_date'], format='%Y%m%d', errors='coerce')
    
    if reference_date is not None:
        ref_dt = pd.to_datetime(reference_date)
        df = df[df['transaction_date'] <= ref_dt]
    
    # Handle same-day duplicates: sort by date and tiebreakers, keep last
    # Using plan_list_price and is_cancel as tiebreakers if they exist on same day
    df = df.sort_values(['msno', 'transaction_date', 'is_cancel', 'plan_list_price'])
    df = df.drop_duplicates(subset=['msno', 'transaction_date'], keep='last')
    
    return df

def load_user_logs_agg(user_logs_path="data/raw/user_logs.csv", reference_date=None) -> pd.DataFrame:
    """
    Use DuckDB to aggregate user logs size-agnostically.
    Filters logs strictly <= reference_date.
    Computes per-user metrics for 7, 14, 30 day windows.
    """
    if not os.path.exists(user_logs_path):
        raise FileNotFoundError(f"Missing {user_logs_path}")
        
    config = load_config()
    windows = config['feature_pipeline'].get('windows_days', [7, 14, 30])
    recent_w = config['feature_pipeline'].get('trend_window_recent', 14)
    prior_w = config['feature_pipeline'].get('trend_window_prior', 14)
    
    ref_dt_str = str(pd.to_datetime(reference_date).date()) if reference_date else datetime.today().strftime('%Y-%m-%d')
    
    query = f"""
    WITH filtered_logs AS (
        SELECT 
            msno,
            strptime(CAST(date AS VARCHAR), '%Y%m%d') AS log_date,
            num_25, num_50, num_75, num_985, num_100, num_unq, total_secs,
            date_diff('day', strptime(CAST(date AS VARCHAR), '%Y%m%d'), CAST('{ref_dt_str}' AS DATE)) AS days_ago
        FROM read_csv_auto('{user_logs_path}')
        WHERE log_date <= CAST('{ref_dt_str}' AS DATE)
    )
    SELECT 
        msno,
        MIN(days_ago) AS days_since_last_log,
        
        -- 7 days
        COUNT(CASE WHEN days_ago <= 7 THEN 1 END) AS active_days_7,
        SUM(CASE WHEN days_ago <= 7 THEN num_100 ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 7 THEN 1 END), 0) AS avg_songs_100_7,
        SUM(CASE WHEN days_ago <= 7 THEN total_secs ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 7 THEN 1 END), 0) AS avg_secs_7,
        SUM(CASE WHEN days_ago <= 7 THEN num_unq ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 7 THEN 1 END), 0) AS avg_unq_7,
        
        -- 14 days
        COUNT(CASE WHEN days_ago <= 14 THEN 1 END) AS active_days_14,
        SUM(CASE WHEN days_ago <= 14 THEN num_100 ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 14 THEN 1 END), 0) AS avg_songs_100_14,
        SUM(CASE WHEN days_ago <= 14 THEN total_secs ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 14 THEN 1 END), 0) AS avg_secs_14,
        
        -- 30 days
        COUNT(CASE WHEN days_ago <= 30 THEN 1 END) AS active_days_30,
        SUM(CASE WHEN days_ago <= 30 THEN num_100 ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 30 THEN 1 END), 0) AS avg_songs_100_30,
        SUM(CASE WHEN days_ago <= 30 THEN total_secs ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= 30 THEN 1 END), 0) AS avg_secs_30,
        
        -- Trend components
        -- Recent window
        SUM(CASE WHEN days_ago <= {recent_w} THEN total_secs ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= {recent_w} THEN 1 END), 0) AS recent_avg_secs,
        SUM(CASE WHEN days_ago <= {recent_w} THEN num_100 ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago <= {recent_w} THEN 1 END), 0) AS recent_avg_songs,
        -- Prior window
        SUM(CASE WHEN days_ago > {recent_w} AND days_ago <= {recent_w + prior_w} THEN total_secs ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago > {recent_w} AND days_ago <= {recent_w + prior_w} THEN 1 END), 0) AS prior_avg_secs,
        SUM(CASE WHEN days_ago > {recent_w} AND days_ago <= {recent_w + prior_w} THEN num_100 ELSE 0 END) / NULLIF(COUNT(CASE WHEN days_ago > {recent_w} AND days_ago <= {recent_w + prior_w} THEN 1 END), 0) AS prior_avg_songs
        
    FROM filtered_logs
    GROUP BY msno
    """
    
    con = duckdb.connect()
    agg_df = con.execute(query).df()
    con.close()
    
    return agg_df

def build_base_table(train_path="data/raw/train_v2.csv", msno_list=None) -> pd.DataFrame:
    """
    Create a base DataFrame of msnos to build features upon.
    If msno_list is provided, builds for exactly those users (e.g. inference).
    Otherwise loads from train_path (e.g. training).
    """
    if msno_list is not None:
        return pd.DataFrame({'msno': msno_list})
        
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Missing {train_path}")
    
    df = pd.read_csv(train_path)
    return df[['msno']].drop_duplicates()
