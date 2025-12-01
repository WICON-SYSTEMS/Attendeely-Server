from datetime import datetime
from decimal import Decimal
import enum
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Numeric,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PayrollStatus(str, enum.Enum):
    """Status for payroll processing."""

    PENDING = "Pending"
    PAID = "Paid"


class PayrollRecord(Base):
    """Monthly payroll record per employee."""

    __tablename__ = "payroll_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    period_year = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    base_salary = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    attendance_days = Column(Integer, nullable=False, default=0)
    working_days = Column(Integer, nullable=False, default=0)
    deductions = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    bonus = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    net_pay = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    status = Column(SQLEnum(PayrollStatus), nullable=False, default=PayrollStatus.PENDING, index=True)
    processed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="payroll_records")
    employee = relationship("Employee", back_populates="payroll_records")

    __table_args__ = (
        UniqueConstraint("employee_id", "period_year", "period_month", name="uq_payroll_employee_period"),
        Index("ix_payroll_period", "organization_id", "period_year", "period_month"),
    )


