from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SubscriptionResponse(BaseModel):
    """Response schema for subscription details"""
    id: int
    plan: str
    status: str
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    monthly_price: Optional[float] = None
    current_employee_count: int
    employee_limit: str  # "10", "100", or "Unlimited"
    features: List[str]
    is_trial: bool
    trial_days_remaining: Optional[int] = None
    
    class Config:
        from_attributes = True


class SubscriptionUpdateRequest(BaseModel):
    """Request schema for updating subscription"""
    plan: str = Field(..., description="New plan: Free, Standard, or Enterprise")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan": "Standard"
            }
        }


class PlanFeaturesResponse(BaseModel):
    """Response schema for plan features"""
    plan: str
    employee_limit: Optional[int] = None  # None means unlimited
    features: List[str]
    is_current_plan: bool = False


class AllPlansResponse(BaseModel):
    """Response schema for all plans"""
    plans: List[PlanFeaturesResponse]

