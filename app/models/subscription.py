from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "Free"
    STANDARD = "Standard"
    ENTERPRISE = "Enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, unique=True, index=True)
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False, default=SubscriptionPlan.FREE)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL)
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    monthly_price = Column(Numeric(10, 2), nullable=True)  # Price in organization's currency
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with organization
    organization = relationship("Organization", back_populates="subscription", uselist=False)

