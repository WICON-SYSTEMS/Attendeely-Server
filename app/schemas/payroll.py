from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.payroll import PayrollStatus


class PayrollProcessRequest(BaseModel):
    """Request payload to (re)calculate payroll for a month."""

    year: Optional[int] = Field(None, ge=2000, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    include_inactive: bool = Field(
        False, description="Include inactive employees who were active during the selected period."
    )
    recalculate_adjustments: bool = Field(
        True,
        description="When true, override existing deduction/bonus values with newly calculated defaults.",
    )


class PayrollSummaryCounts(BaseModel):
    """Breakdown counts for payroll summary."""

    total_employees: int
    paid: int
    pending: int


class PayrollPeriodMeta(BaseModel):
    """Metadata describing the payroll period."""

    month: int
    year: int
    label: str


class PayrollSummaryResponse(BaseModel):
    """Summary metrics for payroll dashboard."""

    total_payroll: float
    paid_amount: float
    pending_amount: float
    currency: str
    counts: PayrollSummaryCounts
    period: PayrollPeriodMeta


class PayrollEmployeeEntryResponse(BaseModel):
    """Detailed payroll entry for a single employee."""

    record_id: UUID
    employee_id: UUID
    employee_name: str
    department: str
    job_title: str
    base_salary: float
    attendance_days: int
    working_days: int
    deductions: float
    bonus: float
    net_pay: float
    status: PayrollStatus
    processed_at: Optional[datetime] = None
    currency: str


class PayrollUpdateRequest(BaseModel):
    """Update adjustments or status for a payroll record."""

    status: Optional[PayrollStatus] = None
    bonus: Optional[float] = Field(None, ge=0)
    deductions: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

