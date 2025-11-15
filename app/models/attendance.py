from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class AttendanceType(str, enum.Enum):
    """Attendance type enumeration"""
    CHECK_IN = "Check In"
    CHECK_OUT = "Check Out"


class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    attendance_type = Column(SQLEnum(AttendanceType), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    location_latitude = Column(String, nullable=True)  # For future GPS tracking
    location_longitude = Column(String, nullable=True)  # For future GPS tracking
    notes = Column(String, nullable=True)  # Optional notes
    hours_worked = Column(Numeric(5, 2), nullable=True)  # Hours worked (calculated on check-out)
    check_in_id = Column(UUID(as_uuid=True), ForeignKey("attendances.id"), nullable=True)  # Reference to check-in record
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with employee
    employee = relationship("Employee", back_populates="attendances", foreign_keys=[employee_id])
    # Self-referential relationship for check-in/check-out pairing
    check_in_record = relationship("Attendance", remote_side=[id], foreign_keys=[check_in_id])

