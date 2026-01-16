from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class SubscriptionPlanEnum(str, enum.Enum):
    """Subscription plan types (legacy enum for backward compatibility)"""
    FREE = "Free"
    STANDARD = "Standard"
    ENTERPRISE = "Enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    PENDING = "pending"
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    INITIATED = "initiated"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentProvider(str, enum.Enum):
    """Payment provider types"""
    FAPSHI = "fapshi"
    # Add more providers as needed


class SubscriptionPlan(Base):
    """Subscription plan table - stores plan details"""
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # e.g., BASIC, PRO
    amount = Column(Numeric(10, 2), nullable=False)  # Price amount
    currency = Column(String(3), nullable=False, default="XAF")  # Currency code (XAF, USD, etc.)
    interval = Column(String(20), nullable=False, default="monthly")  # monthly, yearly, etc.
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan_details")


class Subscription(Base):
    """User/Organization subscription table"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, unique=True, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True, index=True)
    
    # Legacy plan field for backward compatibility (can reference enum or plan name)
    plan = Column(
        SQLEnum(
            SubscriptionPlanEnum,
            name="subscriptionplan",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=True,  # Made nullable to allow plan_id to be primary
    )
    
    status = Column(
        SQLEnum(
            SubscriptionStatus,
            name="subscriptionstatus",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
        index=True,
    )
    
    # Payment-related fields
    start_date = Column(DateTime, nullable=True, index=True)
    next_billing_date = Column(DateTime, nullable=True, index=True)
    last_paid_date = Column(DateTime, nullable=True)
    grace_ends_at = Column(DateTime, nullable=True)  # Grace period end date for past_due subscriptions
    
    # Legacy trial fields
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    
    # Legacy price field (can be derived from plan_id)
    monthly_price = Column(Numeric(10, 2), nullable=True)  # Price in organization's currency
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscription", uselist=False)
    plan_details = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """Payment transaction table"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="XAF")
    
    status = Column(
        SQLEnum(
            PaymentStatus,
            name="paymentstatus",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False,
        default=PaymentStatus.INITIATED,
        index=True,
    )
    
    provider = Column(
        SQLEnum(
            PaymentProvider,
            name="paymentprovider",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False,
        default=PaymentProvider.FAPSHI,
        index=True,
    )
    
    provider_ref = Column(String(255), nullable=True, unique=True, index=True)  # External payment reference ID
    provider_response = Column(String, nullable=True)  # Store full provider response as JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
    
    __table_args__ = (
        Index("ix_payments_user_subscription", "user_id", "subscription_id"),
        Index("ix_payments_status_created", "status", "created_at"),
    )

