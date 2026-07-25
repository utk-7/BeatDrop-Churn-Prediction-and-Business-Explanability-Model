from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CustomerProfileResponse(BaseModel):
    msno: str
    city: Optional[int]
    gender: Optional[str]
    age_clean: Optional[int]
    registered_via_clean: Optional[int]
    plan_list_price: Optional[float]
    payment_plan_days: Optional[int]
    is_auto_renew: Optional[int]
    days_since_registration: Optional[float]

class PredictResponse(BaseModel):
    msno: str
    churn_probability: float
    risk_tier: str
    estimated_clv: float
    expected_value: float
    low_confidence: bool

class BatchPredictRequest(BaseModel):
    msno_list: List[str]

class BatchPredictItemResult(BaseModel):
    msno: str
    success: bool
    error_message: Optional[str] = None
    churn_probability: Optional[float] = None
    risk_tier: Optional[str] = None
    estimated_clv: Optional[float] = None
    expected_value: Optional[float] = None
    low_confidence: Optional[bool] = None

class BatchPredictResponse(BaseModel):
    results: List[BatchPredictItemResult]

class ExplainResponse(BaseModel):
    msno: str
    top_drivers: List[str]
    
class SuggestedActionResponse(BaseModel):
    msno: str
    risk_tier: str
    suggested_action: str
    top_drivers_used: List[str]

class CohortStatsResponse(BaseModel):
    total_customers: int
    churn_rate: float
    risk_tier_distribution: Dict[str, float]

class PrioritizedActionItem(BaseModel):
    msno: str
    expected_value: float
    churn_probability: float
    estimated_clv: float

class TopActionsResponse(BaseModel):
    customers: List[PrioritizedActionItem]
    assumptions_used: Dict[str, Any]

class SimulateRequest(BaseModel):
    plan_list_price: Optional[float] = None
    payment_plan_days: Optional[int] = None
    is_auto_renew: Optional[int] = None
    days_since_registration: Optional[float] = None
