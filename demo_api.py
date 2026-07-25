import json
from fastapi.testclient import TestClient
from app.main import app, app_state

with TestClient(app) as client:
    # 1. Health
    res_health = client.get("/health")
    
    # Get a customer
    msno = app_state['customers_df'].index[0]
    
    # 2. Predict
    res_predict = client.get(f"/customers/{msno}/predict")
    
    # 3. Explain
    res_explain = client.get(f"/customers/{msno}/explain")
    
    # 4. Suggested Action
    res_suggested = client.get(f"/customers/{msno}/suggested-action")
    
    print("--- 1. Health ---")
    print(json.dumps(res_health.json(), indent=2))
    print("\n--- 2. Predict ---")
    print(json.dumps(res_predict.json(), indent=2))
    print("\n--- 3. Explain (SHAP Drivers) ---")
    print(json.dumps(res_explain.json(), indent=2))
    print("\n--- 4. Suggested Action ---")
    print(json.dumps(res_suggested.json(), indent=2))
