from datetime import datetime, date, time, timedelta
from calendar import monthrange
from typing import List, Optional
from uuid import UUID
import logging

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
from app.schemas.attendance import (
    AttendanceDashboardResponse,
    DailyAttendanceDetailResponse,
    MonthlyAttendanceSummaryResponse,
    EmployeeMonthlyAttendanceSummary,
    MonthlyAttendanceDayDetail
)
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/attendance", tags=["Attendance Tracking"])
logger = logging.getLogger(__name__)

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


def _get_month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    """Get start and end datetime bounds for a given month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return (
        datetime.combine(first_day, datetime.min.time()),
        datetime.combine(last_day, datetime.max.time()),
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
            Attendance.id,
            Attendance.location_latitude,
            Attendance.location_longitude
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).all()

        # Create maps for employee_id -> check-in data
        check_in_map = {}
        check_in_lat_map = {}
        check_in_lon_map = {}
        check_in_id_map = {}
        for check_in in check_ins:
            emp_id = check_in.employee_id
            if emp_id not in check_in_map or check_in.timestamp < check_in_map[emp_id]:
                check_in_map[emp_id] = check_in.timestamp
                check_in_lat_map[emp_id] = check_in.location_latitude
                check_in_lon_map[emp_id] = check_in.location_longitude
                check_in_id_map[emp_id] = check_in.id

        # Get all check-outs for the selected date
        check_outs = db.query(
            Attendance.employee_id,
            Attendance.timestamp,
            Attendance.location_latitude,
            Attendance.location_longitude
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.attendance_type == AttendanceType.CHECK_OUT,
            Attendance.timestamp >= day_start,
            Attendance.timestamp <= day_end
        ).all()

        # Create maps for employee_id -> check-out data
        # Use the latest check-out if there are multiple
        check_out_map = {}
        check_out_lat_map = {}
        check_out_lon_map = {}
        for check_out in check_outs:
            emp_id = check_out.employee_id
            if emp_id not in check_out_map or check_out.timestamp > check_out_map[emp_id]:
                check_out_map[emp_id] = check_out.timestamp
                check_out_lat_map[emp_id] = check_out.location_latitude
                check_out_lon_map[emp_id] = check_out.location_longitude

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
            check_in_lat = check_in_lat_map.get(emp_id)
            check_in_lon = check_in_lon_map.get(emp_id)
            check_out_lat = check_out_lat_map.get(emp_id)
            check_out_lon = check_out_lon_map.get(emp_id)

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
                "check_in_latitude": check_in_lat,
                "check_in_longitude": check_in_lon,
                "check_out_latitude": check_out_lat,
                "check_out_longitude": check_out_lon,
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


@router.get("/monthly-summary", status_code=status.HTTP_200_OK)
async def get_monthly_attendance_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (YYYY)"),
    employee_id: Optional[UUID] = Query(None, description="Optional employee ID to filter by specific employee"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly attendance history/summary for all employees or a specific employee.
    Returns daily attendance records, totals, and statistics for the specified month.
    """
    try:
        organization = _get_admin_organization(db, current_user)
        month_start, month_end = _get_month_bounds(year, month)
        
        # Build employee query
        employee_query = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True,  # noqa: E712
            Employee.joining_date <= month_end.date()  # Only employees who joined before/on this month
        )
        
        # Filter by specific employee if provided
        if employee_id:
            employee_query = employee_query.filter(Employee.id == employee_id)
            if not employee_query.first():
                return error_response(
                    message="Employee not found or does not belong to your organization",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        employees = employee_query.all()
        
        if not employees:
            return success_response(
                message="No employees found for the specified criteria",
                data={
                    "month": month,
                    "year": year,
                    "employees": [],
                    "total_employees": 0
                },
                status_code=status.HTTP_200_OK
            )
        
        # Get all leave requests for the month
        leave_requests = db.query(LeaveRequest).join(
            Employee, LeaveRequest.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            LeaveRequest.status == LeaveRequestStatus.APPROVED,
            LeaveRequest.start_date <= month_end.date(),
            LeaveRequest.end_date >= month_start.date()
        ).all()
        
        # Build leave map: employee_id -> set of dates on leave
        leave_map = {}
        for leave in leave_requests:
            if leave.employee_id not in leave_map:
                leave_map[leave.employee_id] = set()
            # Add all dates in the leave range that fall within the month
            leave_start = max(leave.start_date, month_start.date())
            leave_end = min(leave.end_date, month_end.date())
            current_date = leave_start
            while current_date <= leave_end:
                leave_map[leave.employee_id].add(current_date)
                current_date += timedelta(days=1)
        
        # Get all attendance records for the month
        attendance_query = db.query(Attendance).join(
            Employee, Attendance.employee_id == Employee.id
        ).filter(
            Employee.organization_id == organization.id,
            Attendance.timestamp >= month_start,
            Attendance.timestamp <= month_end
        )
        
        if employee_id:
            attendance_query = attendance_query.filter(Attendance.employee_id == employee_id)
        
        attendances = attendance_query.order_by(Attendance.timestamp).all()
        
        # Organize attendance by employee and date
        # Structure: {employee_id: {date: {'check_in': ..., 'check_out': ..., 'hours': ...}}}
        attendance_by_employee = {}
        
        for att in attendances:
            emp_id = att.employee_id
            att_date = att.timestamp.date()
            
            if emp_id not in attendance_by_employee:
                attendance_by_employee[emp_id] = {}
            
            if att_date not in attendance_by_employee[emp_id]:
                attendance_by_employee[emp_id][att_date] = {
                    'check_in': None,
                    'check_out': None,
                    'check_in_lat': None,
                    'check_in_lon': None,
                    'check_out_lat': None,
                    'check_out_lon': None,
                    'hours_worked': None
                }
            
            if att.attendance_type == AttendanceType.CHECK_IN:
                # Use earliest check-in for the day
                if (attendance_by_employee[emp_id][att_date]['check_in'] is None or
                    att.timestamp < attendance_by_employee[emp_id][att_date]['check_in']):
                    attendance_by_employee[emp_id][att_date]['check_in'] = att.timestamp
                    attendance_by_employee[emp_id][att_date]['check_in_lat'] = att.location_latitude
                    attendance_by_employee[emp_id][att_date]['check_in_lon'] = att.location_longitude
            elif att.attendance_type == AttendanceType.CHECK_OUT:
                # Use latest check-out for the day
                if (attendance_by_employee[emp_id][att_date]['check_out'] is None or
                    att.timestamp > attendance_by_employee[emp_id][att_date]['check_out']):
                    attendance_by_employee[emp_id][att_date]['check_out'] = att.timestamp
                    attendance_by_employee[emp_id][att_date]['check_out_lat'] = att.location_latitude
                    attendance_by_employee[emp_id][att_date]['check_out_lon'] = att.location_longitude
                    attendance_by_employee[emp_id][att_date]['hours_worked'] = float(att.hours_worked) if att.hours_worked else None
        
        # Build response for each employee
        employee_summaries = []
        
        for employee in employees:
            emp_id = employee.id
            emp_attendance = attendance_by_employee.get(emp_id, {})
            emp_leaves = leave_map.get(emp_id, set())
            
            # Calculate statistics
            total_days_worked = 0
            total_hours_worked = 0.0
            late_arrivals = 0
            absent_days = 0
            daily_records = []
            
            # Iterate through all days in the month
            current_date = month_start.date()
            while current_date <= month_end.date():
                # Skip if employee joined after this date
                if employee.joining_date > current_date:
                    current_date += timedelta(days=1)
                    continue
                
                day_attendance = emp_attendance.get(current_date)
                is_on_leave = current_date in emp_leaves
                
                check_in_time = None
                check_out_time = None
                hours_worked = None
                check_in_lat = None
                check_in_lon = None
                check_out_lat = None
                check_out_lon = None
                status_value = "absent"
                
                if day_attendance:
                    check_in_time = day_attendance['check_in']
                    check_out_time = day_attendance['check_out']
                    hours_worked = day_attendance['hours_worked']
                    check_in_lat = day_attendance['check_in_lat']
                    check_in_lon = day_attendance['check_in_lon']
                    check_out_lat = day_attendance['check_out_lat']
                    check_out_lon = day_attendance['check_out_lon']
                
                if is_on_leave:
                    status_value = "absent"  # On leave is considered absent for attendance purposes
                    absent_days += 1
                elif check_in_time is None:
                    status_value = "absent"
                    absent_days += 1
                else:
                    total_days_worked += 1
                    if hours_worked:
                        total_hours_worked += hours_worked
                    
                    if check_in_time.time() > LATE_THRESHOLD:
                        status_value = "late"
                        late_arrivals += 1
                    else:
                        status_value = "present"
                
                daily_records.append(MonthlyAttendanceDayDetail(
                    date=current_date,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    hours_worked=hours_worked,
                    status=status_value,
                    check_in_latitude=check_in_lat,
                    check_in_longitude=check_in_lon,
                    check_out_latitude=check_out_lat,
                    check_out_longitude=check_out_lon
                ))
                
                current_date += timedelta(days=1)
            
            employee_summaries.append(EmployeeMonthlyAttendanceSummary(
                employee_id=emp_id,
                employee_name=employee.full_name,
                employee_code=employee.employee_code,
                department=employee.department,
                job_title=employee.job_title,
                total_days_worked=total_days_worked,
                total_hours_worked=round(total_hours_worked, 2),
                late_arrivals=late_arrivals,
                absent_days=absent_days,
                daily_records=daily_records
            ))
        
        # Sort by employee name
        employee_summaries.sort(key=lambda x: x.employee_name)
        
        response_data = MonthlyAttendanceSummaryResponse(
            month=month,
            year=year,
            employees=employee_summaries,
            total_employees=len(employee_summaries)
        )
        
        return success_response(
            message=f"Monthly attendance summary loaded for {year}-{month:02d}",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as exc:
        logger.error(f"Monthly attendance summary error: {str(exc)}", exc_info=True)
        return error_response(
            message="Unable to load monthly attendance summary",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

