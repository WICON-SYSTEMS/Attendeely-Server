from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String, nullable=False, index=True)
    organization_code = Column(String(8), unique=True, nullable=False, index=True)
    logo_url = Column(String, nullable=True)
    industry = Column(String, nullable=False)
    employees_count_range = Column(String, nullable=False)
    country = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="Free Trial")
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Geofence settings
    geofence_latitude = Column(Numeric(10, 8), nullable=True)  # Center latitude
    geofence_longitude = Column(Numeric(11, 8), nullable=True)  # Center longitude
    geofence_radius = Column(Numeric(10, 2), nullable=True)  # Radius in meters (default 20m)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with admin user
    admin = relationship("User", back_populates="organization", foreign_keys=[admin_id])
    # Relationship with employees
    employees = relationship("Employee", back_populates="organization", cascade="all, delete-orphan")
    # Relationship with payroll
    payroll_records = relationship("PayrollRecord", back_populates="organization", cascade="all, delete-orphan")
