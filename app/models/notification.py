from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Index,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class NotificationCategory(str, enum.Enum):
    """Notification categories for grouping events."""
    GENERAL = "General"
    LEAVE = "Leave"
    ATTENDANCE = "Attendance"
    SYSTEM = "System"


class NotificationRecipient(str, enum.Enum):
    """Recipient type for notifications."""
    USER = "User"
    EMPLOYEE = "Employee"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recipient_type = Column(SQLEnum(NotificationRecipient), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    message = Column(String, nullable=False)
    category = Column(SQLEnum(NotificationCategory), nullable=False, default=NotificationCategory.GENERAL, index=True)
    payload = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="notifications")
    employee = relationship("Employee", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_employee_unread", "employee_id", "is_read"),
    )

