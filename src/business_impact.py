import pandas as pd
import numpy as np
from typing import List, Optional

def estimate_clv(customer_row: pd.Series, config: dict) -> float:
    """
    Estimate remaining customer lifetime value (CLV) based on their plan price and 
    an assumed average customer lifespan from the configuration.
    
    Formula: estimated_clv = monthly_revenue * expected_remaining_months
    This is a reasonable estimate, not a precise financial model.
    
    Assumptions:
    - Monthly revenue is derived from `plan_list_price` and `payment_plan_days`. If `payment_plan_days` 
      is 0 or missing, it falls back to `default_monthly_revenue` from config.
    - `expected_remaining_months` is taken from config `avg_customer_lifespan_months` 
      (assuming average subscriber lifespan).
    """
    params = config.get('business_impact', {})
    lifespan = params.get('avg_customer_lifespan_months', 20)
    default_rev = params.get('default_monthly_revenue', 149)
    
    plan_price = customer_row.get('plan_list_price', 0)
    plan_days = customer_row.get('payment_plan_days', 0)
    
    if pd.isna(plan_price) or pd.isna(plan_days) or plan_days <= 0:
        monthly_rev = default_rev
    else:
        # Normalize to a 30-day month
        monthly_rev = plan_price * (30.0 / plan_days)
        
    return float(monthly_rev * lifespan)


def calculate_expected_value(churn_probability: float, estimated_clv: float, config: dict) -> float:
    """
    Calculate the expected value of taking a retention action on a customer.
    
    Formula: Expected Value = 
      (churn_probability * retention_success_rate * estimated_clv) - 
      (discount_cost_percentage * estimated_clv)
      
    Assumptions:
    - `retention_success_rate`: The flat probability that a retention intervention 
      succeeds for a customer who would have otherwise churned.
    - `discount_cost_percentage`: The flat cost of the retention intervention as a % of CLV.
    - An expected value can be negative, indicating that the cost of intervention 
      outweighs the probable saved revenue.
    """
    params = config.get('business_impact', {})
    success_rate = params.get('retention_success_rate', 0.3)
    cost_pct = params.get('discount_cost_percentage', 0.05)
    
    expected_savings = churn_probability * success_rate * estimated_clv
    intervention_cost = cost_pct * estimated_clv
    
    return float(expected_savings - intervention_cost)


def suggested_retention_action(risk_tier: str, top_shap_drivers: Optional[List[str]], config: dict) -> str:
    """
    Suggest a simple rule-based retention action based on the user's risk tier 
    and top SHAP drivers.
    
    Assumptions:
    - Low Risk users require no action.
    - Medium Risk users receive standard engagement efforts.
    - High Risk users receive targeted interventions based on their top churn driver.
    """
    if risk_tier == 'Low':
        return "No action needed"
        
    if risk_tier == 'Medium':
        return "Send engagement email"
        
    # For High risk, check drivers
    if top_shap_drivers:
        payment_keywords = ['payment', 'auto_renew', 'expire', 'transaction']
        price_keywords = ['price', 'actual_amount_paid']
        
        # Check highest importance drivers first
        for driver in top_shap_drivers:
            driver_lower = driver.lower()
            if any(k in driver_lower for k in payment_keywords):
                return "Offer alternative payment method"
            if any(k in driver_lower for k in price_keywords):
                return "Offer discount"
                
    # Fallback for High risk if drivers are None or don't match keywords
    return "Offer discount"


def build_prioritized_action_list(customers_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Given a dataframe of customers with `churn_probability` and `estimated_clv`, 
    rank them by expected_value descending to build a prioritized action list.
    
    This ensures retention effort focuses on customers worth saving, not just 
    the highest-probability churners.
    """
    df = customers_df.copy()
    
    if 'estimated_clv' not in df.columns:
        df['estimated_clv'] = df.apply(lambda row: estimate_clv(row, config), axis=1)
        
    if 'expected_value' not in df.columns:
        df['expected_value'] = df.apply(
            lambda row: calculate_expected_value(row['churn_probability'], row['estimated_clv'], config), 
            axis=1
        )
        
    # Rank by expected value descending
    return df.sort_values(by='expected_value', ascending=False).reset_index(drop=True)
