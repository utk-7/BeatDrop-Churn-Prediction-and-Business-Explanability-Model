import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fastapi.testclient import TestClient
from app.main import app, app_state

# We use the context manager to trigger lifespan events
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_version"] == "0.2.0"
    assert data["thresholds_loaded"] is True

def test_get_customer_valid(client):
    # Grab a valid msno from app_state for testing
    msno = app_state['customers_df'].index[0]
    response = client.get(f"/customers/{msno}")
    assert response.status_code == 200
    assert response.json()["msno"] == msno

def test_get_customer_invalid(client):
    response = client.get("/customers/INVALID_MSNO_123")
    assert response.status_code == 404

def test_predict_customer_valid(client):
    msno = app_state['customers_df'].index[0]
    response = client.get(f"/customers/{msno}/predict")
    assert response.status_code == 200
    data = response.json()
    assert "churn_probability" in data
    assert "risk_tier" in data
    assert "estimated_clv" in data
    assert "expected_value" in data
    assert "low_confidence" in data

def test_predict_batch(client):
    msno_valid = app_state['customers_df'].index[0]
    msno_invalid = "INVALID_123"
    
    response = client.post("/predict/batch", json={"msno_list": [msno_valid, msno_invalid]})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    
    valid_res = next(r for r in data["results"] if r["msno"] == msno_valid)
    assert valid_res["success"] is True
    assert "churn_probability" in valid_res
    
    invalid_res = next(r for r in data["results"] if r["msno"] == msno_invalid)
    assert invalid_res["success"] is False
    assert invalid_res["error_message"] == "Customer not found"

def test_predict_batch_empty(client):
    response = client.post("/predict/batch", json={"msno_list": []})
    assert response.status_code == 400

def test_predict_batch_oversize(client):
    max_batch = app_state['api_config']['max_batch_size']
    oversize_list = ["TEST"] * (max_batch + 1)
    response = client.post("/predict/batch", json={"msno_list": oversize_list})
    assert response.status_code == 400

def test_explain_customer(client):
    msno = app_state['customers_df'].index[0]
    response = client.get(f"/customers/{msno}/explain")
    assert response.status_code == 200
    data = response.json()
    assert "top_drivers" in data
    assert isinstance(data["top_drivers"], list)
    assert len(data["top_drivers"]) == app_state['api_config']['shap_top_n']
    
    # Confirm no synthetic features appear
    synthetic_cols = ['total_secs', 'num_25', 'num_50', 'num_75', 'num_985', 'num_100', 'num_unq']
    for driver in data["top_drivers"]:
        for synth in synthetic_cols:
            assert synth not in driver

def test_suggested_action(client):
    msno = app_state['customers_df'].index[0]
    response = client.get(f"/customers/{msno}/suggested-action")
    assert response.status_code == 200
    data = response.json()
    assert "suggested_action" in data
    assert "risk_tier" in data
    assert "top_drivers_used" in data

def test_business_impact_top_actions(client):
    response = client.get("/business-impact/top-actions?top_n=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["customers"]) <= 5
    assert "assumptions_used" in data
    
    # Verify ordered by EV descending
    evs = [c["expected_value"] for c in data["customers"]]
    assert evs == sorted(evs, reverse=True)
