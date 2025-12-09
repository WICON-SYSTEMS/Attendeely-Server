from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.attendance import Attendance, AttendanceType
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.payroll import PayrollRecord, PayrollStatus
from app.models.user import User
from app.schemas.payroll import (
    PayrollEmployeeEntryResponse,
    PayrollMonthlyOverviewResponse,
    PayrollMonthlyPoint,
    PayrollPeriodMeta,
    PayrollProcessRequest,
    PayrollSummaryCounts,
    PayrollSummaryResponse,
    PayrollUpdateRequest,
)
from app.schemas.response import error_response, success_response

router = APIRouter(prefix="/payroll", tags=["Payroll"])

WORK_HOURS_PER_DAY = Decimal("8")
MONEY_QUANT = Decimal("0.01")


def _get_admin_organization(db: Session, user: User) -> Organization:
    organization = db.query(Organization).filter(Organization.admin_id == user.id).first()
    if not organization:
        raise ValueError("Organization not found for current admin")
    return organization


def _resolve_period(year: Optional[int], month: Optional[int]) -> tuple[int, int]:
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month
    if target_month < 1 or target_month > 12:
        raise ValueError("Month must be between 1 and 12")
    return target_year, target_month


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    _, last_day = calendar.monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)
    return start, end


def _count_working_days(start_date: date, end_date: date) -> int:
    if start_date > end_date:
        return 0
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday-Friday
            working_days += 1
        current += timedelta(days=1)
    return working_days


def _to_decimal(value: Optional[Decimal]) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_float(value: Decimal | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _month_label(year: int, month: int) -> str:
    """Return human-readable label for a month, e.g. 'Jan' or 'January'."""
    return calendar.month_abbr[month]


@router.post("/process", status_code=status.HTTP_200_OK)
async def process_payroll(
    request: PayrollProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate or refresh payroll records for the selected month.
    Requires Standard or Enterprise plan (automated payroll processing).
    """

    try:
        # Check automated payroll processing feature access
        from app.core.subscription_access import create_feature_requirement
        from app.utils.subscription_features import Feature
        
        require_automated_payroll = create_feature_requirement(Feature.AUTOMATED_PAYROLL_PROCESSING)
        try:
            organization, subscription = await require_automated_payroll(
                current_user=current_user,
                db=db
            )
        except HTTPException as e:
            from app.schemas.response import error_response
            return error_response(
                message=e.detail,
                status_code=e.status_code
            )
        year, month = _resolve_period(request.year, request.month)
        period_start, period_end = _month_bounds(year, month)
        period_start_dt = datetime.combine(period_start, datetime.min.time())
        period_end_dt = datetime.combine(period_end, datetime.max.time())

        employee_query = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.joining_date <= period_end,
        )
        if not request.include_inactive:
            employee_query = employee_query.filter(Employee.is_active == True)  # noqa: E712

        employees = employee_query.all()
        records_processed = 0

        for employee in employees:
            employee_start = max(employee.joining_date, period_start)
            working_days = _count_working_days(employee_start, period_end)
            if working_days <= 0:
                continue

            employee_start_dt = datetime.combine(employee_start, datetime.min.time())

            attendance_days = (
                db.query(func.count(func.distinct(func.date(Attendance.timestamp))))
                .filter(
                    Attendance.employee_id == employee.id,
                    Attendance.attendance_type == AttendanceType.CHECK_IN,
                    Attendance.timestamp >= employee_start_dt,
                    Attendance.timestamp <= period_end_dt,
                )
                .scalar()
                or 0
            )

            hourly_rate = _to_decimal(employee.salary_per_hour)
            base_salary = (hourly_rate * WORK_HOURS_PER_DAY * working_days).quantize(MONEY_QUANT)
            calculated_deductions = (
                hourly_rate * WORK_HOURS_PER_DAY * max(working_days - attendance_days, 0)
            ).quantize(MONEY_QUANT)

            record = (
                db.query(PayrollRecord)
                .filter(
                    PayrollRecord.employee_id == employee.id,
                    PayrollRecord.period_year == year,
                    PayrollRecord.period_month == month,
                )
                .first()
            )

            if record:
                record.base_salary = base_salary
                record.attendance_days = attendance_days
                record.working_days = working_days
                if request.recalculate_adjustments or record.deductions is None:
                    record.deductions = calculated_deductions
                if request.recalculate_adjustments or record.bonus is None:
                    record.bonus = Decimal("0.00")
                record.net_pay = (record.base_salary - record.deductions + record.bonus).quantize(
                    MONEY_QUANT
                )
                record.processed_at = datetime.utcnow()
            else:
                net_pay = (base_salary - calculated_deductions).quantize(MONEY_QUANT)
                record = PayrollRecord(
                    organization_id=organization.id,
                    employee_id=employee.id,
                    period_year=year,
                    period_month=month,
                    base_salary=base_salary,
                    attendance_days=attendance_days,
                    working_days=working_days,
                    deductions=calculated_deductions,
                    bonus=Decimal("0.00"),
                    net_pay=net_pay,
                    status=PayrollStatus.PENDING,
                    processed_at=datetime.utcnow(),
                )
                db.add(record)

            records_processed += 1

        db.commit()

        return success_response(
            message=f"Payroll processed for {calendar.month_name[month]} {year}",
            data={
                "period": {"month": month, "year": year},
                "processed_employees": records_processed,
            },
            status_code=status.HTTP_200_OK,
        )

    except ValueError as exc:
        return error_response(message=str(exc), status_code=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return error_response(
            message="Unable to process payroll",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_payroll_summary(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return aggregate payroll metrics for the selected period.
    """

    try:
        organization = _get_admin_organization(db, current_user)
        year, month = _resolve_period(year, month)

        records = (
            db.query(PayrollRecord)
            .filter(
                PayrollRecord.organization_id == organization.id,
                PayrollRecord.period_year == year,
                PayrollRecord.period_month == month,
            )
            .all()
        )

        total_payroll = sum((_to_decimal(record.net_pay) for record in records), Decimal("0.00"))
        paid_amount = sum(
            (_to_decimal(record.net_pay) for record in records if record.status == PayrollStatus.PAID),
            Decimal("0.00"),
        )
        pending_amount = total_payroll - paid_amount

        response = PayrollSummaryResponse(
            total_payroll=_to_float(total_payroll),
            paid_amount=_to_float(paid_amount),
            pending_amount=_to_float(pending_amount),
            currency=organization.currency,
            counts=PayrollSummaryCounts(
                total_employees=len(records),
                paid=sum(1 for record in records if record.status == PayrollStatus.PAID),
                pending=sum(1 for record in records if record.status == PayrollStatus.PENDING),
            ),
            period=PayrollPeriodMeta(
                month=month,
                year=year,
                label=f"{calendar.month_name[month]} {year}",
            ),
        )

        return success_response(
            message="Payroll summary loaded",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )

    except ValueError as exc:
        return error_response(message=str(exc), status_code=status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response(
            message="Unable to load payroll summary",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/monthly-overview", status_code=status.HTTP_200_OK)
async def get_monthly_payroll_overview(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return monthly payroll totals for a full year for use in dashboard charts.
    """

    try:
        organization = _get_admin_organization(db, current_user)
        target_year = year or date.today().year

        # Aggregate totals per month from payroll records
        rows = (
            db.query(
                PayrollRecord.period_year.label("year"),
                PayrollRecord.period_month.label("month"),
                func.coalesce(func.sum(PayrollRecord.net_pay), 0).label("total_net"),
                func.coalesce(
                    func.sum(
                        case(
                            (PayrollRecord.status == PayrollStatus.PAID, PayrollRecord.net_pay),
                            else_=0,
                        )
                    ),
                    0,
                ).label("paid_net"),
            )
            .filter(
                PayrollRecord.organization_id == organization.id,
                PayrollRecord.period_year == target_year,
            )
            .group_by(PayrollRecord.period_year, PayrollRecord.period_month)
            .order_by(PayrollRecord.period_month.asc())
            .all()
        )

        # Map month -> (total, paid)
        aggregates = {
            row.month: (row.total_net or 0, row.paid_net or 0) for row in rows
        }

        points: list[PayrollMonthlyPoint] = []
        for month in range(1, 13):
            total_net_raw, paid_net_raw = aggregates.get(month, (Decimal("0.00"), Decimal("0.00")))
            total_net = _to_decimal(total_net_raw)
            paid_net = _to_decimal(paid_net_raw)
            pending_net = (total_net - paid_net) if total_net >= paid_net else Decimal("0.00")

            points.append(
                PayrollMonthlyPoint(
                    month=month,
                    year=target_year,
                    label=_month_label(target_year, month),
                    total_payroll=_to_float(total_net),
                    paid_amount=_to_float(paid_net),
                    pending_amount=_to_float(pending_net),
                )
            )

        response = PayrollMonthlyOverviewResponse(
            year=target_year,
            currency=organization.currency,
            points=points,
        )

        return success_response(
            message="Monthly payroll overview loaded",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )

    except ValueError as exc:
        return error_response(message=str(exc), status_code=status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response(
            message="Unable to load monthly payroll overview",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/employees", status_code=status.HTTP_200_OK)
async def list_payroll_employees(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    status_filter: Optional[PayrollStatus] = Query(
        None, description="Filter by payroll status (Paid or Pending)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return payroll breakdown per employee for the selected month.
    """

    try:
        organization = _get_admin_organization(db, current_user)
        year, month = _resolve_period(year, month)

        query = (
            db.query(PayrollRecord, Employee)
            .join(Employee, PayrollRecord.employee_id == Employee.id)
            .filter(
                PayrollRecord.organization_id == organization.id,
                PayrollRecord.period_year == year,
                PayrollRecord.period_month == month,
            )
            .order_by(Employee.full_name.asc())
        )

        if status_filter:
            query = query.filter(PayrollRecord.status == status_filter)

        rows = query.all()
        entries = []
        for record, employee in rows:
            entries.append(
                PayrollEmployeeEntryResponse(
                    record_id=record.id,
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    department=employee.department,
                    job_title=employee.job_title,
                    base_salary=_to_float(record.base_salary),
                    attendance_days=record.attendance_days,
                    working_days=record.working_days,
                    deductions=_to_float(record.deductions),
                    bonus=_to_float(record.bonus),
                    net_pay=_to_float(record.net_pay),
                    status=record.status,
                    processed_at=record.processed_at,
                    currency=organization.currency,
                ).model_dump()
            )

        return success_response(
            message="Payroll employees loaded",
            data={
                "period": {
                    "month": month,
                    "year": year,
                    "label": f"{calendar.month_name[month]} {year}",
                },
                "currency": organization.currency,
                "employees": entries,
            },
            status_code=status.HTTP_200_OK,
        )

    except ValueError as exc:
        return error_response(message=str(exc), status_code=status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response(
            message="Unable to load payroll employees",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("/records/{record_id}", status_code=status.HTTP_200_OK)
async def update_payroll_record(
    record_id: UUID,
    request: PayrollUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update adjustments or status for a payroll record.
    """

    try:
        organization = _get_admin_organization(db, current_user)
        record = (
            db.query(PayrollRecord)
            .filter(
                PayrollRecord.id == record_id,
                PayrollRecord.organization_id == organization.id,
            )
            .first()
        )

        if not record:
            return error_response(
                message="Payroll record not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if request.bonus is not None:
            record.bonus = _to_decimal(request.bonus).quantize(MONEY_QUANT)
        if request.deductions is not None:
            record.deductions = _to_decimal(request.deductions).quantize(MONEY_QUANT)
        if request.status:
            record.status = request.status
            record.processed_at = datetime.utcnow() if record.status == PayrollStatus.PAID else None
        if request.notes is not None:
            record.notes = request.notes

        record.net_pay = (record.base_salary - record.deductions + record.bonus).quantize(MONEY_QUANT)
        db.commit()
        db.refresh(record)

        response = PayrollEmployeeEntryResponse(
            record_id=record.id,
            employee_id=record.employee_id,
            employee_name=record.employee.full_name if record.employee else "",
            department=record.employee.department if record.employee else "",
            job_title=record.employee.job_title if record.employee else "",
            base_salary=_to_float(record.base_salary),
            attendance_days=record.attendance_days,
            working_days=record.working_days,
            deductions=_to_float(record.deductions),
            bonus=_to_float(record.bonus),
            net_pay=_to_float(record.net_pay),
            status=record.status,
            processed_at=record.processed_at,
            currency=organization.currency,
        )

        return success_response(
            message="Payroll record updated",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )

    except ValueError as exc:
        return error_response(message=str(exc), status_code=status.HTTP_404_NOT_FOUND)
    except Exception:
        return error_response(
            message="Unable to update payroll record",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

