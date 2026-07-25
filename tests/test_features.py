import pytest
import pandas as pd
from datetime import datetime
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import features
import etl

@pytest.fixture
def mock_config(tmp_path):
    config = {
        'feature_pipeline': {
            'windows_days': [7, 14, 30],
            'trend_window_recent': 14,
            'trend_window_prior': 14,
            'age_bounds': {'min_valid': 0, 'max_valid': 100},
            'registered_via_min_freq': 0.01
        }
    }
    import yaml
    config_file = tmp_path / "feature_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    
    # Override features config loader
    original_load = features.load_config
    features.load_config = lambda p=None: config
    yield config
    features.load_config = original_load

def test_missing_msno_in_logs(mock_config):
    # Test 1: Missing msno in user_logs returns 0-filled engagement features
    base_msno_df = pd.DataFrame({'msno': ['A', 'B']})
    # User B is missing from logs
    logs_agg_df = pd.DataFrame({
        'msno': ['A'],
        'days_since_last_log': [2],
        'active_days_7': [5],
        'avg_songs_100_7': [10.5],
        'recent_avg_secs': [5000],
        'prior_avg_secs': [4000],
        'recent_avg_songs': [20],
        'prior_avg_songs': [15]
    })
    
    res = features.build_engagement_features(logs_agg_df, base_msno_df)
    
    # User B should be filled
    b_features = res[res['msno'] == 'B'].iloc[0]
    assert b_features['active_days_7'] == 0
    assert b_features['days_since_last_log'] == 999
    assert b_features['engagement_trend_secs_ratio'] == 0

def test_duplicate_same_day_transactions():
    # Test 2: Duplicate same-day transactions correctly resolve to a single row
    # Create temp CSV
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("msno,payment_method_id,payment_plan_days,plan_list_price,actual_amount_paid,is_auto_renew,transaction_date,membership_expire_date,is_cancel\n")
        # Duplicates on 20170101
        f.write("A,41,30,99,99,1,20170101,20170201,0\n")
        f.write("A,41,30,149,149,1,20170101,20170201,1\n") 
        path = f.name
        
    try:
        df = etl.load_transactions(path, reference_date='2017-02-01')
        assert len(df) == 1
        # The tiebreaker keeps the one with highest is_cancel / plan_list_price since we sort ascending and take last
        assert df.iloc[0]['is_cancel'] == 1
        assert df.iloc[0]['plan_list_price'] == 149
    finally:
        os.remove(path)

def test_age_bucketing(mock_config):
    # Test 3: Ages < 0 or > 100 are properly bucketed into "Unknown/Invalid"
    base_msno_df = pd.DataFrame({'msno': ['A', 'B', 'C', 'D']})
    members_df = pd.DataFrame({
        'msno': ['A', 'B', 'C', 'D'],
        'city': [1, 1, 1, 1],
        'bd': [-5, 25, 105, None],
        'gender': ['male', 'female', None, 'male'],
        'registered_via': [7, 7, 7, 9],
        'registration_init_time': ['20150101', '20150101', '20150101', '20150101']
    })
    
    res = features.build_demographic_features(members_df, base_msno_df)
    
    ages = dict(zip(res['msno'], res['age_clean']))
    assert ages['A'] == "Unknown/Invalid"
    assert ages['B'] == "25"
    assert ages['C'] == "Unknown/Invalid"
    assert ages['D'] == "Unknown/Invalid"

def test_reference_date_shifting():
    # Test 4: Changing reference_date correctly censors "future" data and shifts recency values
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("msno,payment_method_id,payment_plan_days,plan_list_price,actual_amount_paid,is_auto_renew,transaction_date,membership_expire_date,is_cancel\n")
        f.write("A,41,30,99,99,1,20170101,20170201,0\n")
        f.write("A,41,30,149,149,1,20170301,20170401,0\n") 
        path = f.name
        
    try:
        # Reference date before second transaction
        df_early = etl.load_transactions(path, reference_date='2017-02-01')
        assert len(df_early) == 1
        assert df_early.iloc[0]['transaction_date'] == pd.to_datetime('2017-01-01')
        
        # Build features for early date
        base_msno_df = pd.DataFrame({'msno': ['A']})
        feat_early = features.build_transaction_features(df_early, base_msno_df, reference_date='2017-02-01')
        assert feat_early.iloc[0]['days_since_last_transaction'] == 31 # 2017-02-01 - 2017-01-01
        
        # Reference date after second transaction
        df_late = etl.load_transactions(path, reference_date='2017-04-01')
        assert len(df_late) == 2
        feat_late = features.build_transaction_features(df_late, base_msno_df, reference_date='2017-04-01')
        assert feat_late.iloc[0]['days_since_last_transaction'] == 31 # 2017-04-01 - 2017-03-01
        
    finally:
        os.remove(path)
