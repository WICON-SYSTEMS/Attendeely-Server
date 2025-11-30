from datetime import datetime, date, time, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, distinct, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.attendance import Attendance, AttendanceType
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, LeaveRequestStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.attendance import AttendanceDashboardResponse, DailyAttendanceDetailResponse
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/attendance", tags=["Attendance Tracking"])

LATE_THRESHOLD = time(hour=9, minute=15)  # default 9:15 AM cutoff for lateness


def _get_admin_organization(db: Session, user: User) -> Organization:
    """Get the organization for the current admin user."""
    organization = db.query(Organization).filter(
        Organization.admin_id == user.id
    ).first()

    if not organization:
        raise ValueError("Organization not found for current admin")

    return organization


def _get_day_bounds(target_date: date) -> tuple[datetime, datetime]:
    """Get start and end datetime bounds for a given date."""
    return (
        datetime.combine(target_date, datetime.min.time()),
        datetime.combine(target_date, datetime.max.time()),
    )


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_attendance_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time attendance dashboard metrics for today.
    Returns counts of present, absent, and late employees.
    """
    try:
        organization = _get_admin_organization(db, current_user)
        today = date.today()
        day_start, day_end = _get_day_bounds(today)

        # Get total active employees
        total_employees = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True  # noqa: E712
        ).count()

        # Get employees who checked in today
        present_employee_ids = db.query(distinct(Attendance.employee_id)).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).all()
        present_count = len(present_employee_ids)

        # Get employees who checked in late (after LATE_THRESHOLD)
        late_checkins = db.query(
            Attendance.employee_id,
            func.min(Attendance.timestamp).label("first_check_in")
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).group_by(Attendance.employee_id).all()

        late_count = 0
        for row in late_checkins:
            if row.first_check_in.time() > LATE_THRESHOLD:
                late_count += 1

        # Get employees on approved leave today
        leave_requests = db.query(LeaveRequest.employee_id).join(
            Employee, LeaveRequest.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            LeaveRequest.status == LeaveRequestStatus.APPROVED,
            LeaveRequest.start_date <= day_end,
            LeaveRequest.end_date >= day_start
        ).all()
        on_leave_ids = {req.employee_id for req in leave_requests}

        # Calculate absent: total - present - on leave
        present_ids_set = {row[0] for row in present_employee_ids}
        absent_count = max(total_employees - len(present_ids_set) - len(on_leave_ids), 0)

        response_data = {
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "total_employees": total_employees,
            "date": today.isoformat()
        }

        return success_response(
            message="Attendance dashboard loaded",
            data=response_data,
            status_code=status.HTTP_200_OK
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as exc:
        return error_response(
            message="Unable to load attendance dashboard",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/daily", status_code=status.HTTP_200_OK)
async def get_daily_attendance(
    selected_date: date = Query(..., description="Date to get attendance for (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed daily attendance for a specific date.
    Returns employee name, check-in time, check-out time, and status (late/present/absent).
    """
    try:
        organization = _get_admin_organization(db, current_user)
        day_start, day_end = _get_day_bounds(selected_date)

        # Get all active employees for the organization
        employees = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True,  # noqa: E712
            Employee.joining_date <= selected_date  # Only employees who joined before/on this date
        ).all()

        # Get all check-ins for the selected date
        check_ins = db.query(
            Attendance.employee_id,
            Attendance.timestamp,
            Attendance.id
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).all()

        # Create a map of employee_id -> earliest check-in
        check_in_map = {}
        check_in_id_map = {}
        for check_in in check_ins:
            emp_id = check_in.employee_id
            if emp_id not in check_in_map or check_in.timestamp < check_in_map[emp_id]:
                check_in_map[emp_id] = check_in.timestamp
                check_in_id_map[emp_id] = check_in.id

        # Get all check-outs for the selected date
        check_outs = db.query(
            Attendance.employee_id,
            Attendance.timestamp
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_OUT,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).all()

        # Create a map of employee_id -> check-out time
        # Use the latest check-out if there are multiple
        check_out_map = {}
        for check_out in check_outs:
            emp_id = check_out.employee_id
            if emp_id not in check_out_map or check_out.timestamp > check_out_map[emp_id]:
                check_out_map[emp_id] = check_out.timestamp

        # Get employees on approved leave for the selected date
        leave_requests = db.query(LeaveRequest.employee_id).join(
            Employee, LeaveRequest.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            LeaveRequest.status == LeaveRequestStatus.APPROVED,
            LeaveRequest.start_date <= day_end,
            LeaveRequest.end_date >= day_start
        ).all()
        on_leave_ids = {req.employee_id for req in leave_requests}

        # Build response data
        attendance_details = []
        for employee in employees:
            emp_id = employee.id
            check_in_time = check_in_map.get(emp_id)
            check_out_time = check_out_map.get(emp_id)

            # Determine status
            if emp_id in on_leave_ids:
                # On approved leave - could be considered present or handled separately
                # For now, we'll mark as absent but this could be customized
                status_value = "absent"
            elif check_in_time is None:
                status_value = "absent"
            elif check_in_time.time() > LATE_THRESHOLD:
                status_value = "late"
            else:
                status_value = "present"

            attendance_details.append({
                "employee_name": employee.full_name,
                "check_in_time": check_in_time.isoformat() if check_in_time else None,
                "check_out_time": check_out_time.isoformat() if check_out_time else None,
                "status": status_value
            })

        # Sort by employee name
        attendance_details.sort(key=lambda x: x["employee_name"])

        response_data = {
            "date": selected_date.isoformat(),
            "attendances": attendance_details
        }

        return success_response(
            message=f"Daily attendance loaded for {selected_date.isoformat()}",
            data=response_data,
            status_code=status.HTTP_200_OK
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as exc:
        return error_response(
            message="Unable to load daily attendance",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

