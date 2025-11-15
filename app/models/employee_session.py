from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class EmployeeSession(Base):
    __tablename__ = "employee_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, index=True)  # Hash of the JWT token
    device_info = Column(String, nullable=True)  # Optional device information
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship with employee
    employee = relationship("Employee", back_populates="sessions")
    
    # Index for faster lookups
    __table_args__ = (
        Index('ix_employee_sessions_employee_active', 'employee_id', 'is_active'),
    )

