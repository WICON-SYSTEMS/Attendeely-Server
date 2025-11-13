from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from app.models.employee import WorkType, EmployeeRole, Gender


class CreateEmployeeRequest(BaseModel):
    """Request schema for creating an employee"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Employee full name")
    email: EmailStr = Field(..., description="Employee email address")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Employee phone number")
    gender: Gender = Field(..., description="Employee gender")
    date_of_birth: Optional[date] = Field(None, description="Employee date of birth")
    department: str = Field(..., min_length=2, max_length=100, description="Department within the company")
    job_title: str = Field(..., min_length=2, max_length=100, description="Employee job title")
    work_type: WorkType = Field(..., description="Work type (Full Time, Part Time, Contract, Intern)")
    joining_date: date = Field(..., description="Date employee is joining the company")
    role: EmployeeRole = Field(..., description="Employee role (Admin, HR Manager, Staff)")
    shift: str = Field(..., min_length=2, max_length=50, description="Shift the employee will work (e.g., Morning, Evening, Night, Flexible)")
    salary_per_hour: Optional[float] = Field(None, ge=0, description="Salary per hour in the organization's currency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Jane Smith",
                "email": "jane.smith@company.com",
                "phone_number": "+1234567890",
                "gender": "Female",
                "date_of_birth": "1990-05-15",
                "department": "Engineering",
                "job_title": "Software Engineer",
                "work_type": "Full Time",
                "joining_date": "2024-01-15",
                "role": "Staff",
                "shift": "Morning",
                "salary_per_hour": 45.5
            }
        }


class UpdateEmployeeRequest(BaseModel):
    """Request schema for updating an employee"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    job_title: Optional[str] = Field(None, min_length=2, max_length=100)
    work_type: Optional[WorkType] = None
    joining_date: Optional[date] = None
    role: Optional[EmployeeRole] = None
    shift: Optional[str] = Field(None, min_length=2, max_length=50)
    salary_per_hour: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    """Response schema for employee data"""
    id: UUID
    full_name: str
    email: str
    phone_number: str
    gender: str
    date_of_birth: Optional[date]
    department: str
    job_title: str
    work_type: str
    joining_date: date
    role: str
    photo_url: Optional[str] = None
    shift: str
    salary_per_hour: Optional[float]
    employee_code: str
    qr_code: str
    organization_id: int
    organization_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


