import json
from fastapi.testclient import TestClient
from app.main import app, app_state

with TestClient(app) as client:
    df = app_state['customers_df']
    
    # Filter out slashes
    safe_msnos_all = [m for m in df.index if '/' not in m]
    cust1_msno = safe_msnos_all[0] if len(safe_msnos_all) > 0 else None
    cust2_msno = safe_msnos_all[50] if len(safe_msnos_all) > 50 else None
    
    for i, msno in enumerate([cust1_msno, cust2_msno], start=1):
        if not msno: continue
        print(f"\n================ CUSTOMER {i} ({msno}) ================")
        from urllib.parse import quote
        safe_msno = quote(msno, safe="")
        
        # Predict
        pred = client.get(f"/customers/{safe_msno}/predict").json()
        print(f"Risk Tier: {pred['risk_tier']} (Prob: {pred['churn_probability']:.4f})")
        
        # Explain
        explain = client.get(f"/customers/{safe_msno}/explain").json()
        print("Top SHAP Drivers (from Explain endpoint):")
        for d in explain['top_drivers']:
            print(f"  - {d}")
            
        # Suggested Action
        action = client.get(f"/customers/{safe_msno}/suggested-action").json()
        print(f"Suggested Action: {action['suggested_action']}")
        print("Drivers passed to Business Impact layer:")
        for d in action['top_drivers_used']:
            print(f"  - {d}")
        print("====================================================\n")
