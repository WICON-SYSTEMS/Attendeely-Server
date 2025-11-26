from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class WorkType(str, enum.Enum):
    """Employee work type enumeration"""
    FULL_TIME = "Full Time"
    PART_TIME = "Part Time"
    CONTRACT = "Contract"
    INTERN = "Intern"


class EmployeeRole(str, enum.Enum):
    """Employee role enumeration"""
    ADMIN = "Admin"
    HR_MANAGER = "HR Manager"
    STAFF = "Staff"


class Gender(str, enum.Enum):
    """Gender enumeration"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    department = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    work_type = Column(SQLEnum(WorkType), nullable=False)
    joining_date = Column(Date, nullable=False)
    role = Column(SQLEnum(EmployeeRole), nullable=False)
    photo_url = Column(String, nullable=True)
    shift = Column(String, nullable=False)  # e.g., "Morning", "Evening", "Night", "Flexible"
    salary_per_hour = Column(Numeric(10, 2), nullable=True)
    employee_code = Column(String(10), nullable=False, index=True)
    qr_code = Column(String(64), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint: employee_code must be unique within an organization
    __table_args__ = (
        UniqueConstraint('employee_code', 'organization_id', name='uq_employee_code_organization'),
    )
    
    # Relationship with organization
    organization = relationship("Organization", back_populates="employees")
    # Relationship with attendances
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan", foreign_keys="Attendance.employee_id")
    # Relationship with sessions
    sessions = relationship("EmployeeSession", back_populates="employee", cascade="all, delete-orphan")
    # Relationship with leave requests
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan", foreign_keys="LeaveRequest.employee_id")
    # Notifications
    notifications = relationship("Notification", back_populates="employee", cascade="all, delete-orphan")

