from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_employee
from app.core.security import create_access_token, hash_token
from app.schemas.attendance import (
    EmployeeLoginRequest,
    EmployeeLoginResponse,
    AttendanceResponse,
    EmployeeProfileResponse
)
from app.schemas.response import success_response, error_response
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.attendance import Attendance, AttendanceType
from app.models.employee_session import EmployeeSession
from app.core.config import settings
from app.utils.geofence import is_within_geofence, get_distance_from_geofence
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employee", tags=["Employee Portal"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def employee_login(request: EmployeeLoginRequest, db: Session = Depends(get_db)):
    """
    Employee login using organization code, employee code, and email.
    Returns access token and employee information.
    """
    try:
        # Find organization by code
        organization = db.query(Organization).filter(
            Organization.organization_code == request.organization_code
        ).first()
        
        if not organization:
            return error_response(
                message="Invalid organization code",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Find employee by code and email within the organization
        employee = db.query(Employee).filter(
            Employee.employee_code == request.employee_code,
            Employee.email == request.email,
            Employee.organization_id == organization.id
        ).first()
        
        if not employee:
            return error_response(
                message="Invalid employee code, email, or organization code",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if employee is active
        if not employee.is_active:
            return error_response(
                message="Employee account is deactivated. Please contact your administrator.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Invalidate all existing active sessions for this employee
        db.query(EmployeeSession).filter(
            EmployeeSession.employee_id == employee.id,
            EmployeeSession.is_active == True
        ).update({"is_active": False})
        
        # Generate access token for employee with extended expiration (90 days for mobile)
        employee_token_expires = timedelta(days=settings.EMPLOYEE_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={
                "employee_id": str(employee.id),
                "email": employee.email,
                "organization_id": organization.id
            },
            expires_delta=employee_token_expires
        )
        
        # Create new session with extended expiration
        token_hash = hash_token(access_token)
        expires_at = datetime.utcnow() + employee_token_expires
        
        new_session = EmployeeSession(
            employee_id=employee.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_active=True
        )
        db.add(new_session)
        db.commit()
        
        # Prepare response
        response_data = EmployeeLoginResponse(
            employee_id=employee.id,
            full_name=employee.full_name,
            email=employee.email,
            employee_code=employee.employee_code,
            organization_code=organization.organization_code,
            organization_name=organization.organization_name,
            department=employee.department,
            job_title=employee.job_title,
            shift=employee.shift,
            access_token=access_token,
            token_type="bearer"
        )
        
        return success_response(
            message="Login successful",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Employee login error: {str(e)}")
        return error_response(
            message="An error occurred during login. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_employee_token(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Refresh the employee's access token to extend session.
    This keeps employees logged in on mobile devices.
    """
    try:
        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == current_employee.organization_id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Generate new access token with extended expiration
        employee_token_expires = timedelta(days=settings.EMPLOYEE_TOKEN_EXPIRE_DAYS)
        new_access_token = create_access_token(
            data={
                "employee_id": str(current_employee.id),
                "email": current_employee.email,
                "organization_id": organization.id
            },
            expires_delta=employee_token_expires
        )
        
        # Invalidate old active sessions and create a new one
        db.query(EmployeeSession).filter(
            EmployeeSession.employee_id == current_employee.id,
            EmployeeSession.is_active == True
        ).update({"is_active": False})
        
        # Create new session
        token_hash = hash_token(new_access_token)
        expires_at = datetime.utcnow() + employee_token_expires
        
        new_session = EmployeeSession(
            employee_id=current_employee.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_active=True
        )
        db.add(new_session)
        db.commit()
        
        return success_response(
            message="Token refreshed successfully",
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in_days": settings.EMPLOYEE_TOKEN_EXPIRE_DAYS
            },
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while refreshing the token. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def employee_logout(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Logout the current employee by invalidating their session.
    """
    try:
        # Invalidate all active sessions for this employee
        db.query(EmployeeSession).filter(
            EmployeeSession.employee_id == current_employee.id,
            EmployeeSession.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        return success_response(
            message="Logged out successfully",
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while logging out. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/profile", status_code=status.HTTP_200_OK)
async def get_employee_profile(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get current employee's profile information.
    """
    try:
        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == current_employee.organization_id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Prepare response
        profile_data = EmployeeProfileResponse(
            id=current_employee.id,
            full_name=current_employee.full_name,
            email=current_employee.email,
            phone_number=current_employee.phone_number,
            gender=current_employee.gender.value,
            date_of_birth=current_employee.date_of_birth,
            department=current_employee.department,
            job_title=current_employee.job_title,
            work_type=current_employee.work_type.value,
            joining_date=current_employee.joining_date,
            role=current_employee.role.value,
            photo_url=current_employee.photo_url,
            shift=current_employee.shift,
            salary_per_hour=float(current_employee.salary_per_hour) if current_employee.salary_per_hour is not None else None,
            employee_code=current_employee.employee_code,
            organization_code=organization.organization_code,
            organization_name=organization.organization_name,
            is_active=current_employee.is_active,
            created_at=current_employee.created_at
        )
        
        return success_response(
            message="Profile retrieved successfully",
            data=profile_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get employee profile error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving profile.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/attendance/check-in", status_code=status.HTTP_201_CREATED)
async def check_in(
    location_latitude: str = Form(...),
    location_longitude: str = Form(...),
    notes: Optional[str] = Form(None),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Record check-in for the current employee.
    Only one check-in per day is allowed.
    Location must be within the organization's geofence.
    """
    try:
        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == current_employee.organization_id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if geofence is set
        if not organization.geofence_latitude or not organization.geofence_longitude or not organization.geofence_radius:
            return error_response(
                message="Geofence not configured for this organization. Please contact your administrator.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and convert location coordinates
        try:
            check_lat = float(location_latitude)
            check_lon = float(location_longitude)
        except (ValueError, TypeError):
            return error_response(
                message="Invalid location coordinates",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate location is within geofence
        center_lat = float(organization.geofence_latitude)
        center_lon = float(organization.geofence_longitude)
        radius = float(organization.geofence_radius)
        
        if not is_within_geofence(center_lat, center_lon, radius, check_lat, check_lon):
            distance = get_distance_from_geofence(center_lat, center_lon, check_lat, check_lon)
            return error_response(
                message=f"You are outside the geofence area. You are {distance:.2f}m away from the allowed location. Please move within {radius}m radius to check in.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get today's date range
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        # Check if employee already checked in today
        existing_check_in = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= today_start,
            Attendance.timestamp <= today_end
        ).first()
        
        if existing_check_in:
            return error_response(
                message="You have already checked in today. Please check out first.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create check-in record
        check_in_record = Attendance(
            employee_id=current_employee.id,
            attendance_type=AttendanceType.CHECK_IN,
            timestamp=datetime.utcnow(),
            location_latitude=location_latitude,
            location_longitude=location_longitude,
            notes=notes
        )
        
        db.add(check_in_record)
        db.commit()
        db.refresh(check_in_record)
        
        # Prepare response
        response_data = AttendanceResponse(
            id=check_in_record.id,
            employee_id=check_in_record.employee_id,
            attendance_type=check_in_record.attendance_type.value,
            timestamp=check_in_record.timestamp,
            location_latitude=check_in_record.location_latitude,
            location_longitude=check_in_record.location_longitude,
            notes=check_in_record.notes,
            created_at=check_in_record.created_at
        )
        
        return success_response(
            message="Successfully checked in",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Check-in error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while recording check-in. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/attendance/check-out", status_code=status.HTTP_201_CREATED)
async def check_out(
    location_latitude: Optional[str] = None,
    location_longitude: Optional[str] = None,
    notes: Optional[str] = None,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Record check-out for the current employee.
    Requires a check-in for today. Calculates and records hours worked.
    """
    try:
        # Get today's date range
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        # Find today's check-in
        check_in_record = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id,
            Attendance.attendance_type == AttendanceType.CHECK_IN,
            Attendance.timestamp >= today_start,
            Attendance.timestamp <= today_end
        ).order_by(Attendance.timestamp.desc()).first()
        
        if not check_in_record:
            return error_response(
                message="You must check in first before checking out.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already checked out today
        existing_check_out = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id,
            Attendance.attendance_type == AttendanceType.CHECK_OUT,
            Attendance.check_in_id == check_in_record.id
        ).first()
        
        if existing_check_out:
            return error_response(
                message="You have already checked out today.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate hours worked
        check_out_time = datetime.utcnow()
        time_difference = check_out_time - check_in_record.timestamp
        hours_worked = Decimal(str(time_difference.total_seconds() / 3600)).quantize(Decimal('0.01'))
        
        # Create check-out record
        check_out_record = Attendance(
            employee_id=current_employee.id,
            attendance_type=AttendanceType.CHECK_OUT,
            timestamp=check_out_time,
            location_latitude=location_latitude,
            location_longitude=location_longitude,
            notes=notes,
            hours_worked=hours_worked,
            check_in_id=check_in_record.id
        )
        
        db.add(check_out_record)
        db.commit()
        db.refresh(check_out_record)
        
        # Prepare response
        response_data = AttendanceResponse(
            id=check_out_record.id,
            employee_id=check_out_record.employee_id,
            attendance_type=check_out_record.attendance_type.value,
            timestamp=check_out_record.timestamp,
            location_latitude=check_out_record.location_latitude,
            location_longitude=check_out_record.location_longitude,
            notes=check_out_record.notes,
            created_at=check_out_record.created_at
        )
        
        return success_response(
            message=f"Successfully checked out. Hours worked: {hours_worked}",
            data={
                **response_data.model_dump(),
                "hours_worked": float(hours_worked),
                "check_in_time": check_in_record.timestamp.isoformat()
            },
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Check-out error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while recording check-out. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/attendance/history", status_code=status.HTTP_200_OK)
async def get_attendance_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    Get attendance history for the current employee.
    Returns most recent records first.
    """
    try:
        # Get attendance records for the employee
        attendances = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id
        ).order_by(Attendance.timestamp.desc()).limit(limit).offset(offset).all()
        
        # Prepare response data
        attendance_data = []
        for att in attendances:
            attendance_data.append({
                "id": str(att.id),
                "employee_id": str(att.employee_id),
                "attendance_type": att.attendance_type.value,
                "timestamp": att.timestamp.isoformat(),
                "location_latitude": att.location_latitude,
                "location_longitude": att.location_longitude,
                "notes": att.notes,
                "hours_worked": float(att.hours_worked) if att.hours_worked is not None else None,
                "created_at": att.created_at.isoformat()
            })
        
        # Get total count
        total_count = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id
        ).count()
        
        return success_response(
            message=f"Retrieved {len(attendance_data)} attendance record(s)",
            data={
                "attendances": attendance_data,
                "total": total_count,
                "limit": limit,
                "offset": offset
            },
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get attendance history error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving attendance history.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/attendance/today", status_code=status.HTTP_200_OK)
async def get_today_attendance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get today's attendance records for the current employee.
    """
    try:
        from datetime import date
        
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        # Get today's attendance records
        attendances = db.query(Attendance).filter(
            Attendance.employee_id == current_employee.id,
            Attendance.timestamp >= today_start,
            Attendance.timestamp <= today_end
        ).order_by(Attendance.timestamp.asc()).all()
        
        # Prepare response data
        attendance_data = []
        for att in attendances:
            attendance_data.append({
                "id": str(att.id),
                "attendance_type": att.attendance_type.value,
                "timestamp": att.timestamp.isoformat(),
                "location_latitude": att.location_latitude,
                "location_longitude": att.location_longitude,
                "notes": att.notes
            })
        
        # Determine attendance status
        attendance_status = "Not checked in"
        if attendance_data:
            last_record = attendance_data[-1]
            if last_record["attendance_type"] == "Check In":
                attendance_status = "Checked in"
            else:
                attendance_status = "Checked out"
        
        return success_response(
            message="Today's attendance retrieved successfully",
            data={
                "status": attendance_status,
                "records": attendance_data,
                "date": date.today().isoformat()
            },
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get today attendance error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving today's attendance.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

