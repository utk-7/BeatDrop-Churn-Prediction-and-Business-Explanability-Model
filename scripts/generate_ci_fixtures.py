import pandas as pd
import numpy as np
import joblib
import os
import xgboost as xgb

os.makedirs('tests/fixtures', exist_ok=True)

# 1. Create a dummy customer_features.parquet
df = pd.DataFrame({
    'msno': ['dummy1', 'dummy2', 'dummy3', 'dummy4'],
    'is_churn': [0, 1, 0, 1],
    'plan_list_price': [149, 149, 99, 149],
    'payment_plan_days': [30, 30, 30, 30],
    'days_since_registration': [100, 200, 300, 400],
    'registered_via_clean': ['7', '9', '3', '7'],
    'age_clean': [25, 30, 35, 40],
    'is_auto_renew': [1, 0, 1, 0],
    'days_until_expire': [10, -5, 20, -10],
    'payment_method_id': ['41', '38', '41', '38'],
    'city': ['1', '5', '13', '1'],
    'gender': ['male', 'female', 'Unknown', 'female'],
    'days_since_last_transaction': [5, 40, 10, 50],
    'num_plan_changes': [0, 1, 0, 2],
    'num_cancellations': [0, 0, 0, 1],
    'num_payment_methods': [1, 2, 1, 2],
    'days_since_last_log': [2, 15, 1, 20],
    'active_days_7': [5, 1, 7, 0],
    'avg_songs_100_7': [20, 5, 50, 0],
    'recent_avg_secs': [5000, 1000, 8000, 0],
    'prior_avg_secs': [4500, 1500, 7000, 1000],
    'recent_avg_songs': [25, 5, 40, 0],
    'prior_avg_songs': [20, 10, 35, 5]
})
df['registered_via_clean'] = df['registered_via_clean'].astype('category')
df['payment_method_id'] = df['payment_method_id'].astype('category')
df['city'] = df['city'].astype('category')
df['gender'] = df['gender'].astype('category')

df.to_parquet('tests/fixtures/customer_features.parquet')

# 2. Train a tiny XGBoost model
X = df.drop(columns=['is_churn', 'msno'])
y = df['is_churn']

model = xgb.XGBClassifier(
    n_estimators=5,
    max_depth=3,
    learning_rate=0.1,
    enable_categorical=True,
    random_state=42
)
model.fit(X, y)

joblib.dump(model, 'tests/fixtures/xgboost_model_v0.2.0.joblib')
print("Fixture data generated!")
