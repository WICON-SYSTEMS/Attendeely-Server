from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from app.models.attendance import AttendanceType


class EmployeeLoginRequest(BaseModel):
    """Request schema for employee login"""
    organization_code: str = Field(..., min_length=8, max_length=8, description="Organization code")
    employee_code: str = Field(..., min_length=8, max_length=10, description="Employee code")
    email: str = Field(..., description="Employee email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_code": "A7K9X2M4",
                "employee_code": "B3N8Q5P1",
                "email": "employee@company.com"
            }
        }


class EmployeeLoginResponse(BaseModel):
    """Response schema for employee login"""
    employee_id: UUID
    full_name: str
    email: str
    employee_code: str
    organization_code: str
    organization_name: str
    department: str
    job_title: str
    shift: str
    access_token: str
    token_type: str = "bearer"


class CheckInOutRequest(BaseModel):
    """Request schema for check-in/check-out"""
    attendance_type: AttendanceType = Field(..., description="Check In or Check Out")
    location_latitude: Optional[str] = Field(None, description="GPS latitude (optional)")
    location_longitude: Optional[str] = Field(None, description="GPS longitude (optional)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "attendance_type": "Check In",
                "location_latitude": "40.7128",
                "location_longitude": "-74.0060",
                "notes": "Arrived on time"
            }
        }


class AttendanceResponse(BaseModel):
    """Response schema for attendance record"""
    id: UUID
    employee_id: UUID
    attendance_type: str
    timestamp: datetime
    location_latitude: Optional[str] = None
    location_longitude: Optional[str] = None
    notes: Optional[str] = None
    hours_worked: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeProfileResponse(BaseModel):
    """Response schema for employee profile"""
    id: UUID
    full_name: str
    email: str
    phone_number: str
    gender: str
    date_of_birth: Optional[date] = None
    department: str
    job_title: str
    work_type: str
    joining_date: datetime
    role: str
    photo_url: Optional[str] = None
    shift: str
    salary_per_hour: Optional[float] = None
    employee_code: str
    organization_code: str
    organization_name: str
    organization_currency: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AttendanceDashboardResponse(BaseModel):
    """Response schema for attendance dashboard metrics"""
    present: int
    absent: int
    late: int
    total_employees: int
    date: date
    
    class Config:
        from_attributes = True


class DailyAttendanceDetailResponse(BaseModel):
    """Response schema for daily attendance detail"""
    employee_name: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    check_in_latitude: Optional[str] = None
    check_in_longitude: Optional[str] = None
    check_out_latitude: Optional[str] = None
    check_out_longitude: Optional[str] = None
    status: str  # "late", "present", or "absent"
    
    class Config:
        from_attributes = True


class MonthlyAttendanceDayDetail(BaseModel):
    """Response schema for a single day's attendance in monthly summary"""
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    hours_worked: Optional[float] = None
    status: str  # "late", "present", or "absent"
    check_in_latitude: Optional[str] = None
    check_in_longitude: Optional[str] = None
    check_out_latitude: Optional[str] = None
    check_out_longitude: Optional[str] = None


class EmployeeMonthlyAttendanceSummary(BaseModel):
    """Response schema for an employee's monthly attendance summary"""
    employee_id: UUID
    employee_name: str
    employee_code: str
    department: str
    job_title: str
    total_days_worked: int
    total_hours_worked: float
    late_arrivals: int
    absent_days: int
    daily_records: list[MonthlyAttendanceDayDetail]


class MonthlyAttendanceSummaryResponse(BaseModel):
    """Response schema for monthly attendance summary"""
    month: int
    year: int
    employees: list[EmployeeMonthlyAttendanceSummary]
    total_employees: int

