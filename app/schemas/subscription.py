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
    """Webhook request schema from Fapshi
    
    This is called by Fapshi (payment provider), NOT by the frontend.
    Fapshi sends this webhook when payment status changes.
    """
    transId: str = Field(..., description="Fapshi transaction ID (required)")
    externalId: Optional[str] = Field(None, description="External ID (subscription_id) - optional, we use transId to find payment")
    status: str = Field(..., description="Payment status: SUCCESSFUL, FAILED, etc. (required)")
    # Optional fields that Fapshi might send
    amount: Optional[float] = Field(None, description="Payment amount (optional)")
    message: Optional[str] = Field(None, description="Status message (optional)")
    datePaid: Optional[str] = Field(None, description="Date payment was completed (optional)")


class PaymentStatusResponse(BaseModel):
    """Response schema for payment status (for frontend polling)"""
    payment_id: int
    subscription_id: int
    status: str  # initiated, success, failed
    provider_ref: Optional[str] = None  # transId from Fapshi
    amount: float
    currency: str
    created_at: datetime
    updated_at: datetime


class TestPaymentRequest(BaseModel):
    """Request schema for test payment endpoint"""
    phone: str = Field(..., description="Phone number for payment (mobile money)")
    name: Optional[str] = Field(None, description="Name for payment (defaults to user's full name)")
    message: Optional[str] = Field(None, description="Optional payment message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+237612345678",
                "name": "John Doe",
                "message": "Test payment"
            }
        }


class SubscriptionStatusByTransIdResponse(BaseModel):
    """Response schema for subscription status by transaction ID"""
    trans_id: str
    payment_id: int
    subscription_id: int
    payment_status: str  # initiated, success, failed
    subscription_status: str  # pending, active, expired, cancelled, etc.
    amount: float
    currency: str
    provider: str  # fapshi
    plan_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    payment_created_at: datetime
    payment_updated_at: datetime


class PaymentHistoryItem(BaseModel):
    """Schema for a single payment in history"""
    payment_id: int
    subscription_id: int
    trans_id: Optional[str] = None  # provider_ref
    amount: float
    currency: str
    status: str  # initiated, success, failed
    provider: str  # fapshi
    plan_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentHistoryResponse(BaseModel):
    """Response schema for payment history"""
    payments: List[PaymentHistoryItem]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None

