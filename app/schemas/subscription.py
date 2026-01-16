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
    id: int  # Plan ID from database
    name: str  # Plan name (e.g., "Free", "Standard", "Enterprise")
    amount: float  # Plan amount
    currency: str  # Currency code (e.g., "XAF")
    interval: str  # Billing interval (e.g., "monthly")
    description: Optional[str] = None
    employee_limit: Optional[int] = None  # None means unlimited
    features: List[str]
    is_current_plan: bool = False
    
    class Config:
        from_attributes = True


class AllPlansResponse(BaseModel):
    """Response schema for all plans"""
    plans: List[PlanFeaturesResponse]


class SubscribeRequest(BaseModel):
    """Request schema for subscribing to a plan"""
    plan_id: int = Field(..., description="ID of the subscription plan to subscribe to")
    phone: str = Field(..., description="Phone number for payment (mobile money)")
    name: Optional[str] = Field(None, description="Name for payment (defaults to user's full name)")
    message: Optional[str] = Field(None, description="Optional payment message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": 1,
                "phone": "+237612345678",
                "name": "John Doe",
                "message": "Monthly subscription payment"
            }
        }


class PaymentInitiationResponse(BaseModel):
    """Response schema for payment initiation"""
    trans_id: Optional[str] = Field(None, description="Fapshi transaction ID")
    message: str = Field(..., description="Payment initiation message")
    date_initiated: Optional[str] = Field(None, description="Date payment was initiated")
    subscription_id: int = Field(..., description="ID of the created subscription")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Payment currency")
    status: str = Field(..., description="Payment status (initiated)")


class FapshiWebhookRequest(BaseModel):
    """Webhook request schema from Fapshi"""
    transId: str = Field(..., description="Fapshi transaction ID")
    externalId: Optional[str] = Field(None, description="External ID (subscription_id)")
    status: str = Field(..., description="Payment status: success, failed, etc.")
    amount: Optional[float] = Field(None, description="Payment amount")
    message: Optional[str] = Field(None, description="Status message")
    datePaid: Optional[str] = Field(None, description="Date payment was completed")

