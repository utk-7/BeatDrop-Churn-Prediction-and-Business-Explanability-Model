import pytest
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import business_impact

@pytest.fixture
def mock_config():
    return {
        'business_impact': {
            'avg_customer_lifespan_months': 20,
            'discount_cost_percentage': 0.05,
            'retention_success_rate': 0.3,
            'default_monthly_revenue': 149
        }
    }

def test_estimate_clv(mock_config):
    # Normal customer
    row = pd.Series({'plan_list_price': 149, 'payment_plan_days': 30})
    clv = business_impact.estimate_clv(row, mock_config)
    assert clv == 149 * 20
    assert clv > 0

    # Missing plan price fallback
    row_missing = pd.Series({'plan_list_price': None, 'payment_plan_days': 0})
    clv_missing = business_impact.estimate_clv(row_missing, mock_config)
    assert clv_missing == 149 * 20

def test_calculate_expected_value(mock_config):
    clv = 3000
    # High churn probability, value should be positive
    # EV = (0.8 * 0.3 * 3000) - (0.05 * 3000) = 720 - 150 = 570
    ev_positive = business_impact.calculate_expected_value(0.8, clv, mock_config)
    assert ev_positive == 570.0
    
    # Low churn prob, high cost scenario where it might be negative
    # EV = (0.1 * 0.3 * 3000) - (0.05 * 3000) = 90 - 150 = -60
    ev_negative = business_impact.calculate_expected_value(0.1, clv, mock_config)
    assert ev_negative < 0

def test_build_prioritized_action_list(mock_config):
    # Customer A: High churn probability, but low CLV
    # Customer B: Lower churn probability, but very high CLV
    # Customer C: Very low churn probability, negative EV
    
    data = {
        'msno': ['A', 'B', 'C'],
        'churn_probability': [0.9, 0.6, 0.05],
        'plan_list_price': [99, 149, 149], # A pays less
        'payment_plan_days': [30, 30, 30],
        'estimated_clv': [99*20, 149*20, 149*20] # A = 1980, B = 2980, C = 2980
    }
    df = pd.DataFrame(data)
    
    ranked_df = business_impact.build_prioritized_action_list(df, mock_config)
    
    # EV for A = (0.9 * 0.3 * 1980) - (0.05 * 1980) = 534.6 - 99.0 = 435.6
    # EV for B = (0.6 * 0.3 * 2980) - (0.05 * 2980) = 536.4 - 149.0 = 387.4 
    # Wait, B is slightly lower EV than A with these numbers! Let's bump B's CLV to make sure B ranks higher.
    
    data['plan_list_price'] = [99, 300, 149]
    data['estimated_clv'] = [99*20, 300*20, 149*20] # A = 1980, B = 6000, C = 2980
    df = pd.DataFrame(data)
    
    ranked_df = business_impact.build_prioritized_action_list(df, mock_config)
    
    # EV for A = 435.6
    # EV for B = (0.6 * 0.3 * 6000) - (0.05 * 6000) = 1080 - 300 = 780
    
    # B should rank above A despite A having a higher churn probability
    assert ranked_df.iloc[0]['msno'] == 'B'
    assert ranked_df.iloc[1]['msno'] == 'A'
    assert ranked_df.iloc[2]['msno'] == 'C'
    
    # C should have negative EV
    assert ranked_df.iloc[2]['expected_value'] < 0


def test_suggested_retention_action(mock_config):
    # Low risk
    assert business_impact.suggested_retention_action('Low', None, mock_config) == "No action needed"
    
    # Medium risk
    assert business_impact.suggested_retention_action('Medium', ['active_days_7 (High)'], mock_config) == "Send engagement email"
    
    # High risk with drivers
    assert business_impact.suggested_retention_action('High', ['payment_method_id (High)', 'age (High)'], mock_config) == "Offer alternative payment method"
    assert business_impact.suggested_retention_action('High', ['plan_list_price (High)'], mock_config) == "Offer discount"
    assert business_impact.suggested_retention_action('High', ['days_until_expire (High)'], mock_config) == "Proactive renewal outreach"
    
    # High risk with None drivers handles gracefully
    assert business_impact.suggested_retention_action('High', None, mock_config) == "Send targeted retention offer"
