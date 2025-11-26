from datetime import datetime, date, time, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.attendance import Attendance, AttendanceType
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, LeaveRequestStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

LATE_THRESHOLD = time(hour=9, minute=15)  # default 9:15 AM cutoff for lateness


def _get_admin_organization(db: Session, user: User) -> Organization:
    organization = db.query(Organization).filter(
        Organization.admin_id == user.id
    ).first()

    if not organization:
        raise ValueError("Organization not found for current admin")

    return organization


def _calc_percentage_change(current: float, previous: float) -> float:
    if previous in (0, None):
        return 0.0
    try:
        return round(((current - previous) / previous) * 100, 2)
    except ZeroDivisionError:
        return 0.0


def _get_day_bounds(target_date: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(target_date, datetime.min.time()),
        datetime.combine(target_date, datetime.max.time()),
    )


def _get_month_bounds(ref_date: date) -> tuple[datetime, datetime]:
    first_day = date(ref_date.year, ref_date.month, 1)
    if ref_date.month == 12:
        next_month = date(ref_date.year + 1, 1, 1)
    else:
        next_month = date(ref_date.year, ref_date.month + 1, 1)

    start_dt = datetime.combine(first_day, datetime.min.time())
    end_dt = datetime.combine(next_month, datetime.min.time()) - timedelta(microseconds=1)
    return start_dt, end_dt


def _get_previous_month_bounds(ref_date: date) -> tuple[datetime, datetime]:
    first_day_this_month = date(ref_date.year, ref_date.month, 1)
    last_day_previous_month = first_day_this_month - timedelta(days=1)
    start_dt = datetime.combine(
        date(last_day_previous_month.year, last_day_previous_month.month, 1),
        datetime.min.time(),
    )
    end_dt = datetime.combine(
        date(last_day_previous_month.year, last_day_previous_month.month, last_day_previous_month.day),
        datetime.max.time(),
    )
    return start_dt, end_dt


def _count_active_employees(db: Session, organization_id: int, ref_date: date | None = None) -> int:
    query = db.query(Employee).filter(
        Employee.organization_id == organization_id,
        Employee.is_active == True  # noqa: E712
    )

    if ref_date:
        query = query.filter(Employee.joining_date <= ref_date)

    return query.count()


def _count_present_employees(
    db: Session,
    organization_id: int,
    target_date: date
) -> int:
    day_start, day_end = _get_day_bounds(target_date)
    return db.query(func.count(distinct(Attendance.employee_id))).join(
        Employee, Attendance.employee_id == Employee.id
    ).filter(
        Employee.organization_id == organization_id,
        Attendance.attendance_type == AttendanceType.CHECK_IN,
        Attendance.timestamp >= day_start,
        Attendance.timestamp <= day_end
    ).scalar() or 0


def _count_compliant_employees(
    db: Session,
    organization_id: int,
    target_date: date
) -> int:
    day_start, day_end = _get_day_bounds(target_date)
    return db.query(func.count(distinct(Attendance.employee_id))).join(
        Employee, Attendance.employee_id == Employee.id
    ).filter(
        Employee.organization_id == organization_id,
        Attendance.attendance_type == AttendanceType.CHECK_OUT,
        Attendance.timestamp >= day_start,
        Attendance.timestamp <= day_end
    ).scalar() or 0


def _calculate_payroll(
    db: Session,
    organization_id: int,
    start_dt: datetime,
    end_dt: datetime
) -> float:
    total = db.query(
        func.sum(
            (Attendance.hours_worked * func.coalesce(Employee.salary_per_hour, 0))
        )
    ).join(
        Employee, Attendance.employee_id == Employee.id
    ).filter(
        Employee.organization_id == organization_id,
        Attendance.attendance_type == AttendanceType.CHECK_OUT,
        Attendance.timestamp >= start_dt,
        Attendance.timestamp <= end_dt
    ).scalar()

    return float(total) if total is not None else 0.0


def _build_leave_map(
    leave_requests: List[LeaveRequest],
    start_date: date,
    end_date: date
) -> Dict[date, set]:
    leave_map: Dict[date, set] = {}
    for request in leave_requests:
        current = max(start_date, request.start_date.date())
        end = min(end_date, request.end_date.date())
        while current <= end:
            leave_map.setdefault(current, set()).add(request.employee_id)
            current += timedelta(days=1)
    return leave_map


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return top-level dashboard metrics for the admin's organization.
    """
    try:
        organization = _get_admin_organization(db, current_user)
        today = date.today()
        last_month_base = today.replace(day=1) - timedelta(days=1)
        last_month_same_day = last_month_base.replace(day=min(today.day, last_month_base.day))

        total_employees = _count_active_employees(db, organization.id, today)
        total_employees_last_month = _count_active_employees(db, organization.id, last_month_same_day)

        present_today = _count_present_employees(db, organization.id, today)
        present_last_month = _count_present_employees(db, organization.id, last_month_same_day)

        current_attendance_rate = round((present_today / total_employees) * 100, 2) if total_employees else 0.0
        last_attendance_rate = round((present_last_month / total_employees_last_month) * 100, 2) if total_employees_last_month else 0.0

        compliant_today = _count_compliant_employees(db, organization.id, today)
        compliant_last_month = _count_compliant_employees(db, organization.id, last_month_same_day)

        compliance_rate = round((compliant_today / total_employees) * 100, 2) if total_employees else 0.0
        compliance_last_rate = round((compliant_last_month / total_employees_last_month) * 100, 2) if total_employees_last_month else 0.0

        current_month_start, current_month_end = _get_month_bounds(today)
        previous_month_start, previous_month_end = _get_previous_month_bounds(today)

        current_payroll = _calculate_payroll(db, organization.id, current_month_start, current_month_end)
        previous_payroll = _calculate_payroll(db, organization.id, previous_month_start, previous_month_end)

        response = {
            "total_employees": {
                "value": total_employees,
                "change_percentage": _calc_percentage_change(total_employees, total_employees_last_month)
            },
            "present_today": {
                "value": present_today,
                "attendance_rate": current_attendance_rate,
                "change_percentage": _calc_percentage_change(present_today, present_last_month)
            },
            "payroll": {
                "value": round(current_payroll, 2),
                "currency": organization.currency,
                "change_percentage": _calc_percentage_change(current_payroll, previous_payroll)
            },
            "compliance_rate": {
                "value": compliance_rate,
                "change_percentage": _calc_percentage_change(compliance_rate, compliance_last_rate)
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

        return success_response(
            message="Dashboard overview loaded",
            data=response,
            status_code=status.HTTP_200_OK
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as exc:
        return error_response(
            message="Unable to load dashboard overview",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/daily-attendance", status_code=status.HTTP_200_OK)
async def get_daily_attendance_trend(
    days: int = Query(7, ge=3, le=31),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns attendance counts for the past `days` days.
    """
    try:
        organization = _get_admin_organization(db, current_user)
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        start_dt, end_dt = _get_day_bounds(start_date)
        _, today_end = _get_day_bounds(today)

        attendance_rows = db.query(
            func.date(Attendance.timestamp).label("day"),
            func.count(distinct(Attendance.employee_id)).label("present")
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= start_dt,
            Attendance.timestamp <= today_end
        ).group_by(
            func.date(Attendance.timestamp)
        ).all()

        attendance_map = {row.day: row.present for row in attendance_rows}
        total_employees = _count_active_employees(db, organization.id, today)

        data_points = []
        current_day = start_date
        while current_day <= today:
            present = attendance_map.get(current_day, 0)
            attendance_rate = round((present / total_employees) * 100, 2) if total_employees else 0.0

            data_points.append({
                "date": current_day.isoformat(),
                "present": present,
                "attendance_rate": attendance_rate
            })
            current_day += timedelta(days=1)

        return success_response(
            message="Daily attendance trend loaded",
            data={
                "range": {
                    "start_date": start_date.isoformat(),
                    "end_date": today.isoformat()
                },
                "data": data_points
            },
            status_code=status.HTTP_200_OK
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception:
        return error_response(
            message="Unable to load attendance trend",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/late-absent", status_code=status.HTTP_200_OK)
async def get_late_and_absent_metrics(
    days: int = Query(7, ge=3, le=31),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns late and absent employee counts for the past `days` days.
    """
    try:
        organization = _get_admin_organization(db, current_user)
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_dt, _ = _get_day_bounds(start_date)
        _, today_end = _get_day_bounds(today)

        # Fetch earliest check-ins per employee per day
        earliest_checkins = db.query(
            func.date(Attendance.timestamp).label("day"),
            Attendance.employee_id,
            func.min(Attendance.timestamp).label("first_check_in")
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= start_dt,
            Attendance.timestamp <= today_end
        ).group_by(
            func.date(Attendance.timestamp),
            Attendance.employee_id
        ).all()

        lateness_map: Dict[date, int] = {}
        presence_map: Dict[date, set] = {}
        for row in earliest_checkins:
            entry_day: date = row.day
            presence_map.setdefault(entry_day, set()).add(row.employee_id)

            if row.first_check_in.time() > LATE_THRESHOLD:
                lateness_map[entry_day] = lateness_map.get(entry_day, 0) + 1

        # Approved leaves overlapping period
        leave_requests = db.query(
            LeaveRequest.employee_id,
            LeaveRequest.start_date,
            LeaveRequest.end_date
        ).join(
            Employee, LeaveRequest.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            LeaveRequest.status == LeaveRequestStatus.APPROVED,
            LeaveRequest.end_date >= start_dt,
            LeaveRequest.start_date <= today_end
        ).all()

        leave_map = _build_leave_map(leave_requests, start_date, today)
        total_employees = _count_active_employees(db, organization.id, today)

        data_points = []
        current_day = start_date
        while current_day <= today:
            late_count = lateness_map.get(current_day, 0)
            present_employee_ids = presence_map.get(current_day, set())
            on_leave = len(leave_map.get(current_day, set()))

            absent = max(total_employees - len(present_employee_ids) - on_leave, 0)

            data_points.append({
                "date": current_day.isoformat(),
                "late": late_count,
                "absent": absent
            })
            current_day += timedelta(days=1)

        return success_response(
            message="Late and absent metrics loaded",
            data={
                "range": {
                    "start_date": start_date.isoformat(),
                    "end_date": today.isoformat()
                },
                "data": data_points
            },
            status_code=status.HTTP_200_OK
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception:
        return error_response(
            message="Unable to load late/absent metrics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

