from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.employee import (
    CreateEmployeeRequest,
    UpdateEmployeeRequest,
    EmployeeResponse
)
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.employee import Employee, WorkType, EmployeeRole, Gender
from app.models.organization import Organization
from app.services.cloudinary_service import CloudinaryService
from app.services.email_service import EmailService
from app.utils.generators import generate_employee_code, generate_qr_code
import logging
import secrets
import hashlib
from datetime import datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employees", tags=["Employees"])


def get_user_organization(db: Session, user: User) -> Organization:
    """
    Get the organization for the current user.
    Raises HTTPException if user doesn't have an organization.
    """
    organization = db.query(Organization).filter(
        Organization.admin_id == user.id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found. Please create an organization first."
        )
    
    return organization


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_employee(
    full_name: str = Form(..., min_length=2, max_length=100),
    email: str = Form(...),
    phone_number: str = Form(..., min_length=10, max_length=20),
    gender: str = Form(...),
    date_of_birth: Optional[str] = Form(None),  # Will be parsed to date
    department: str = Form(..., min_length=2, max_length=100),
    job_title: str = Form(..., min_length=2, max_length=100),
    work_type: str = Form(...),
    joining_date: str = Form(...),  # Will be parsed to date
    role: str = Form(...),
    shift: str = Form(..., min_length=2, max_length=50),
    salary_per_hour: Optional[float] = Form(None),
    photo: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new employee.
    Only accessible by users who have an organization.
    """
    try:
        # Get user's organization
        organization = get_user_organization(db, current_user)
        
        # Check employee limit based on subscription
        from app.core.subscription_access import check_employee_limit
        try:
            organization, subscription = await check_employee_limit(
                current_user=current_user,
                db=db
            )
        except HTTPException as e:
            return error_response(
                message=e.detail,
                status_code=e.status_code
            )
        
        # Validate email is not already used in this organization
        existing_employee = db.query(Employee).filter(
            Employee.email == email,
            Employee.organization_id == organization.id
        ).first()
        
        if existing_employee:
            return error_response(
                message="Email already exists for an employee in this organization",
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Parse date strings
        try:
            dob = None
            if date_of_birth:
                dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            joining = datetime.strptime(joining_date, "%Y-%m-%d").date()
        except ValueError:
            return error_response(
                message="Invalid date format. Use YYYY-MM-DD",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate salary per hour if provided
        salary_decimal: Optional[Decimal] = None
        if salary_per_hour is not None:
            try:
                salary_decimal = Decimal(str(salary_per_hour))
            except (InvalidOperation, TypeError):
                return error_response(
                    message="Invalid salary_per_hour value",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if salary_decimal < 0:
                return error_response(
                    message="salary_per_hour cannot be negative",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate enums
        try:
            gender_enum = Gender(gender)
            work_type_enum = WorkType(work_type)
            role_enum = EmployeeRole(role)
        except ValueError as e:
            return error_response(
                message=f"Invalid enum value: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate employee code
        employee_code = generate_employee_code(db, organization.id)
        
        # Generate temporary QR code (will be regenerated with actual employee ID)
        temp_qr = hashlib.sha256(f"{organization.id}_{employee_code}_{secrets.token_hex(16)}".encode()).hexdigest()
        
        # Create employee (without photo first)
        new_employee = Employee(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            gender=gender_enum,
            date_of_birth=dob,
            department=department,
            job_title=job_title,
            work_type=work_type_enum,
            joining_date=joining,
            role=role_enum,
            shift=shift,
            salary_per_hour=salary_decimal,
            organization_id=organization.id,
            photo_url=None,
            employee_code=employee_code,
            qr_code=temp_qr  # Temporary, will be updated
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        
        # Generate proper QR code after employee is created (with actual employee ID)
        qr_code = generate_qr_code(new_employee.id, new_employee.employee_code, organization.id)
        new_employee.qr_code = qr_code
        db.commit()
        db.refresh(new_employee)
        
        # Upload photo if provided
        photo_url = None
        if photo:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if photo.content_type not in allowed_types:
                # Rollback employee creation
                db.delete(new_employee)
                db.commit()
                return error_response(
                    message="Invalid file type. Only JPEG, PNG, and WEBP images are allowed.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 5MB)
            contents = await photo.read()
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                # Rollback employee creation
                db.delete(new_employee)
                db.commit()
                return error_response(
                    message="File size too large. Maximum size is 5MB.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload to Cloudinary
            photo_url = await CloudinaryService.upload_employee_photo(
                contents,
                photo.filename,
                new_employee.id,
                organization.id
            )
            
            if photo_url:
                new_employee.photo_url = photo_url
                db.commit()
                db.refresh(new_employee)
            else:
                logger.warning(f"Failed to upload photo for employee {new_employee.id}")
        
        # Send onboarding email with organization and employee codes
        try:
            email_sent = await EmailService.send_employee_access_email(
                to_email=new_employee.email,
                full_name=new_employee.full_name,
                organization_name=organization.organization_name,
                organization_code=organization.organization_code,
                employee_code=new_employee.employee_code,
                shift=new_employee.shift
            )
            if not email_sent:
                logger.warning(f"Failed to send employee access email to {new_employee.email}")
        except Exception as e:
            logger.error(f"Error sending employee access email to {new_employee.email}: {str(e)}")
        
        # Prepare response
        response_data = EmployeeResponse(
            id=new_employee.id,
            full_name=new_employee.full_name,
            email=new_employee.email,
            phone_number=new_employee.phone_number,
            gender=new_employee.gender.value,
            date_of_birth=new_employee.date_of_birth,
            department=new_employee.department,
            job_title=new_employee.job_title,
            work_type=new_employee.work_type.value,
            joining_date=new_employee.joining_date,
            role=new_employee.role.value,
            photo_url=new_employee.photo_url,
            shift=new_employee.shift,
            salary_per_hour=float(new_employee.salary_per_hour) if new_employee.salary_per_hour is not None else None,
            employee_code=new_employee.employee_code,
            qr_code=new_employee.qr_code,
            organization_id=new_employee.organization_id,
            organization_code=organization.organization_code,
            is_active=new_employee.is_active,
            created_at=new_employee.created_at,
            updated_at=new_employee.updated_at
        )
        
        return success_response(
            message="Employee created successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create employee error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while creating the employee. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_employees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all employees for the current user's organization.
    Only returns employees belonging to the user's organization.
    """
    try:
        # Get user's organization
        organization = get_user_organization(db, current_user)
        
        # Get all employees for this organization
        employees = db.query(Employee).options(joinedload(Employee.organization)).filter(
            Employee.organization_id == organization.id
        ).order_by(Employee.created_at.desc()).all()
        
        # Prepare response data
        employees_data = []
        for emp in employees:
            employees_data.append({
                "id": emp.id,
                "full_name": emp.full_name,
                "email": emp.email,
                "phone_number": emp.phone_number,
                "gender": emp.gender.value,
                "date_of_birth": emp.date_of_birth.isoformat() if emp.date_of_birth else None,
                "department": emp.department,
                "job_title": emp.job_title,
                "work_type": emp.work_type.value,
                "joining_date": emp.joining_date.isoformat(),
                "role": emp.role.value,
                "photo_url": emp.photo_url,
                "shift": emp.shift,
                "salary_per_hour": float(emp.salary_per_hour) if emp.salary_per_hour is not None else None,
                "employee_code": emp.employee_code,
                "qr_code": emp.qr_code,
                "organization_id": emp.organization_id,
                "organization_code": emp.organization.organization_code if emp.organization else organization.organization_code,
                "is_active": emp.is_active,
                "created_at": emp.created_at.isoformat(),
                "updated_at": emp.updated_at.isoformat()
            })
        
        return success_response(
            message=f"Retrieved {len(employees_data)} employee(s) successfully",
            data=employees_data,
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get employees error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving employees.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/{employee_code}", status_code=status.HTTP_200_OK)
async def get_employee_by_code(
    employee_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee by employee code.
    Only accessible if employee belongs to the current user's organization.
    """
    try:
        # Get user's organization
        organization = get_user_organization(db, current_user)
        
        # Find employee by code within this organization
        employee = db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.organization_id == organization.id
        ).first()
        
        if not employee:
            return error_response(
                message="Employee not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Prepare response
        response_data = EmployeeResponse(
            id=employee.id,
            full_name=employee.full_name,
            email=employee.email,
            phone_number=employee.phone_number,
            gender=employee.gender.value,
            date_of_birth=employee.date_of_birth,
            department=employee.department,
            job_title=employee.job_title,
            work_type=employee.work_type.value,
            joining_date=employee.joining_date,
            role=employee.role.value,
            photo_url=employee.photo_url,
            shift=employee.shift,
            salary_per_hour=float(employee.salary_per_hour) if employee.salary_per_hour is not None else None,
            employee_code=employee.employee_code,
            qr_code=employee.qr_code,
            organization_id=employee.organization_id,
            organization_code=organization.organization_code,
            is_active=employee.is_active,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )
        
        return success_response(
            message="Employee retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get employee error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving the employee.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{employee_code}", status_code=status.HTTP_200_OK)
async def update_employee(
    employee_code: str,
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    work_type: Optional[str] = Form(None),
    joining_date: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    shift: Optional[str] = Form(None),
    salary_per_hour: Optional[float] = Form(None),
    is_active: Optional[bool] = Form(None),
    photo: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee details.
    Only accessible if employee belongs to the current user's organization.
    """
    try:
        # Get user's organization
        organization = get_user_organization(db, current_user)
        
        # Find employee by code within this organization
        employee = db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.organization_id == organization.id
        ).first()
        
        if not employee:
            return error_response(
                message="Employee not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Update fields if provided
        if full_name is not None:
            employee.full_name = full_name
        if email is not None:
            # Check if email is already used by another employee in this organization
            existing = db.query(Employee).filter(
                Employee.email == email,
                Employee.organization_id == organization.id,
                Employee.id != employee.id
            ).first()
            if existing:
                return error_response(
                    message="Email already exists for another employee in this organization",
                    status_code=status.HTTP_409_CONFLICT
                )
            employee.email = email
        if phone_number is not None:
            employee.phone_number = phone_number
        if gender is not None:
            try:
                employee.gender = Gender(gender)
            except ValueError:
                return error_response(
                    message="Invalid gender value",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        if date_of_birth is not None:
            try:
                employee.date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            except ValueError:
                return error_response(
                    message="Invalid date format. Use YYYY-MM-DD",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        if salary_per_hour is not None:
            try:
                salary_decimal = Decimal(str(salary_per_hour))
            except (InvalidOperation, TypeError):
                return error_response(
                    message="Invalid salary_per_hour value",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if salary_decimal < 0:
                return error_response(
                    message="salary_per_hour cannot be negative",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            employee.salary_per_hour = salary_decimal
        if department is not None:
            employee.department = department
        if job_title is not None:
            employee.job_title = job_title
        if work_type is not None:
            try:
                employee.work_type = WorkType(work_type)
            except ValueError:
                return error_response(
                    message="Invalid work type value",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        if joining_date is not None:
            try:
                employee.joining_date = datetime.strptime(joining_date, "%Y-%m-%d").date()
            except ValueError:
                return error_response(
                    message="Invalid date format. Use YYYY-MM-DD",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        if role is not None:
            try:
                employee.role = EmployeeRole(role)
            except ValueError:
                return error_response(
                    message="Invalid role value",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        if shift is not None:
            employee.shift = shift
        if is_active is not None:
            employee.is_active = is_active
        
        # Update photo if provided
        if photo:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if photo.content_type not in allowed_types:
                return error_response(
                    message="Invalid file type. Only JPEG, PNG, and WEBP images are allowed.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 5MB)
            contents = await photo.read()
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                return error_response(
                    message="File size too large. Maximum size is 5MB.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete old photo if exists
            if employee.photo_url:
                await CloudinaryService.delete_employee_photo(employee.photo_url)
            
            # Upload new photo
            photo_url = await CloudinaryService.upload_employee_photo(
                contents,
                photo.filename,
                employee.id,
                organization.id
            )
            
            if photo_url:
                employee.photo_url = photo_url
            else:
                logger.warning(f"Failed to upload photo for employee {employee.id}")
                return error_response(
                    message="Failed to upload photo. Please try again.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        db.commit()
        db.refresh(employee)
        
        # Prepare response
        response_data = EmployeeResponse(
            id=employee.id,
            full_name=employee.full_name,
            email=employee.email,
            phone_number=employee.phone_number,
            gender=employee.gender.value,
            date_of_birth=employee.date_of_birth,
            department=employee.department,
            job_title=employee.job_title,
            work_type=employee.work_type.value,
            joining_date=employee.joining_date,
            role=employee.role.value,
            photo_url=employee.photo_url,
            shift=employee.shift,
            salary_per_hour=float(employee.salary_per_hour) if employee.salary_per_hour is not None else None,
            employee_code=employee.employee_code,
            qr_code=employee.qr_code,
            organization_id=employee.organization_id,
            organization_code=organization.organization_code,
            is_active=employee.is_active,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )
        
        return success_response(
            message="Employee updated successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update employee error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while updating the employee.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/{employee_code}", status_code=status.HTTP_200_OK)
async def delete_employee(
    employee_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an employee.
    Only accessible if employee belongs to the current user's organization.
    """
    try:
        # Get user's organization
        organization = get_user_organization(db, current_user)
        
        # Find employee by code within this organization
        employee = db.query(Employee).filter(
            Employee.employee_code == employee_code,
            Employee.organization_id == organization.id
        ).first()
        
        if not employee:
            return error_response(
                message="Employee not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Delete photo from Cloudinary if exists
        if employee.photo_url:
            await CloudinaryService.delete_employee_photo(employee.photo_url)
        
        # Delete employee
        db.delete(employee)
        db.commit()
        
        return success_response(
            message="Employee deleted successfully",
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete employee error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while deleting the employee.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

