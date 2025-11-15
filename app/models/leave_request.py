from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class LeaveRequestType(str, enum.Enum):
    """Leave/Permission request type enumeration"""
    PERMISSION = "Permission"
    LEAVE = "Leave"
    SICK = "Sick"
    VACATION = "Vacation"
    CUSTOM = "Custom"


class LeaveRequestStatus(str, enum.Enum):
    """Leave request status enumeration"""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    request_type = Column(SQLEnum(LeaveRequestType), nullable=False)
    custom_type = Column(String, nullable=True)  # For custom request types
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    reason = Column(Text, nullable=False)  # Required reason
    status = Column(SQLEnum(LeaveRequestStatus), nullable=False, default=LeaveRequestStatus.PENDING, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin/Manager who reviewed
    review_time = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)  # Optional notes from reviewer
    is_full_day = Column(Boolean, default=True)  # True for full day, False for partial (hours)
    hours_deducted = Column(Numeric(5, 2), nullable=True)  # Hours to deduct for partial permissions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="leave_requests", foreign_keys=[employee_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

