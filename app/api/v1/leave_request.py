from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_employee
from app.schemas.leave_request import (
    CreateLeaveRequestRequest,
    ApproveRejectRequest,
    LeaveRequestResponse,
    LeaveRequestSummaryResponse
)
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.leave_request import LeaveRequest, LeaveRequestType, LeaveRequestStatus
from app.models.attendance import Attendance, AttendanceType
from app.models.notification import NotificationCategory
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


# ==================== EMPLOYEE ENDPOINTS ====================

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    request: CreateLeaveRequestRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Create a new leave/permission request.
    Employees can request time off with reason and dates.
    """
    try:
        # Validate custom type if request type is Custom
        if request.request_type == LeaveRequestType.CUSTOM and not request.custom_type:
            return error_response(
                message="custom_type is required when request_type is Custom",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate dates
        if request.end_date <= request.start_date:
            return error_response(
                message="End date must be after start date",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate hours_deducted for partial permissions
        if not request.is_full_day and not request.hours_deducted:
            return error_response(
                message="hours_deducted is required for partial permissions (when is_full_day is False)",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if request.is_full_day and request.hours_deducted:
            return error_response(
                message="hours_deducted should not be provided for full day requests",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch organization/admin for notifications
        organization = db.query(Organization).filter(
            Organization.id == current_employee.organization_id
        ).first()
        admin_user = None
        if organization:
            admin_user = db.query(User).filter(User.id == organization.admin_id).first()

        # Create leave request
        leave_request = LeaveRequest(
            employee_id=current_employee.id,
            request_type=request.request_type,
            custom_type=request.custom_type if request.request_type == LeaveRequestType.CUSTOM else None,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            status=LeaveRequestStatus.PENDING,
            is_full_day=request.is_full_day,
            hours_deducted=Decimal(str(request.hours_deducted)) if request.hours_deducted else None
        )
        
        db.add(leave_request)
        db.flush()

        # Notify managers/admins (in-app)
        if admin_user:
            NotificationService.create_user_notification(
                db,
                user_id=admin_user.id,
                title="New leave request",
                message=f"{current_employee.full_name} submitted a {leave_request.request_type.value.lower()} request.",
                category=NotificationCategory.LEAVE,
                payload={
                    "leave_request_id": str(leave_request.id),
                    "employee_id": str(current_employee.id),
                    "request_type": leave_request.request_type.value,
                    "start_date": leave_request.start_date.isoformat(),
                    "end_date": leave_request.end_date.isoformat(),
                    "is_full_day": leave_request.is_full_day
                },
                auto_commit=False
            )

        db.commit()
        db.refresh(leave_request)

        # Notify managers/admins via email
        if admin_user:
            await EmailService.send_leave_request_notification(
                to_email=admin_user.email,
                admin_name=admin_user.full_name,
                employee_name=current_employee.full_name,
                request_type=leave_request.request_type.value,
                start_date=leave_request.start_date,
                end_date=leave_request.end_date,
                reason=leave_request.reason
            )
        
        # Prepare response
        response_data = {
            "id": str(leave_request.id),
            "employee_id": str(leave_request.employee_id),
            "request_type": leave_request.request_type.value,
            "custom_type": leave_request.custom_type,
            "start_date": leave_request.start_date.isoformat(),
            "end_date": leave_request.end_date.isoformat(),
            "reason": leave_request.reason,
            "status": leave_request.status.value,
            "is_full_day": leave_request.is_full_day,
            "hours_deducted": float(leave_request.hours_deducted) if leave_request.hours_deducted else None,
            "created_at": leave_request.created_at.isoformat()
        }
        
        return success_response(
            message="Leave request created successfully. Awaiting approval.",
            data=response_data,
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Create leave request error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while creating the leave request. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/my-requests", status_code=status.HTTP_200_OK)
async def get_my_leave_requests(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status (Pending, Approved, Rejected, Cancelled)")
):
    """
    Get all leave requests for the current employee.
    Can filter by status.
    """
    try:
        query = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == current_employee.id
        )
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = LeaveRequestStatus(status_filter)
                query = query.filter(LeaveRequest.status == status_enum)
            except ValueError:
                return error_response(
                    message=f"Invalid status filter. Valid values: {', '.join([s.value for s in LeaveRequestStatus])}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        # Prepare response data
        requests_data = []
        for req in leave_requests:
            reviewer_name = None
            if req.reviewer_id:
                reviewer = db.query(User).filter(User.id == req.reviewer_id).first()
                reviewer_name = reviewer.full_name if reviewer else None
            
            requests_data.append({
                "id": str(req.id),
                "request_type": req.request_type.value,
                "custom_type": req.custom_type,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "reason": req.reason,
                "status": req.status.value,
                "reviewer_name": reviewer_name,
                "review_time": req.review_time.isoformat() if req.review_time else None,
                "review_notes": req.review_notes,
                "is_full_day": req.is_full_day,
                "hours_deducted": float(req.hours_deducted) if req.hours_deducted else None,
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat()
            })
        
        return success_response(
            message=f"Retrieved {len(requests_data)} leave request(s)",
            data=requests_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get my leave requests error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving leave requests.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/my-requests/{request_id}", status_code=status.HTTP_200_OK)
async def get_my_leave_request(
    request_id: UUID,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get a specific leave request by ID (only if it belongs to the current employee).
    """
    try:
        leave_request = db.query(LeaveRequest).filter(
            LeaveRequest.id == request_id,
            LeaveRequest.employee_id == current_employee.id
        ).first()
        
        if not leave_request:
            return error_response(
                message="Leave request not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        reviewer_name = None
        if leave_request.reviewer_id:
            reviewer = db.query(User).filter(User.id == leave_request.reviewer_id).first()
            reviewer_name = reviewer.full_name if reviewer else None
        
        response_data = {
            "id": str(leave_request.id),
            "request_type": leave_request.request_type.value,
            "custom_type": leave_request.custom_type,
            "start_date": leave_request.start_date.isoformat(),
            "end_date": leave_request.end_date.isoformat(),
            "reason": leave_request.reason,
            "status": leave_request.status.value,
            "reviewer_name": reviewer_name,
            "review_time": leave_request.review_time.isoformat() if leave_request.review_time else None,
            "review_notes": leave_request.review_notes,
            "is_full_day": leave_request.is_full_day,
            "hours_deducted": float(leave_request.hours_deducted) if leave_request.hours_deducted else None,
            "created_at": leave_request.created_at.isoformat(),
            "updated_at": leave_request.updated_at.isoformat()
        }
        
        return success_response(
            message="Leave request retrieved successfully",
            data=response_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get leave request error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving the leave request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/my-requests/{request_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_leave_request(
    request_id: UUID,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending leave request.
    Only pending requests can be cancelled.
    """
    try:
        leave_request = db.query(LeaveRequest).filter(
            LeaveRequest.id == request_id,
            LeaveRequest.employee_id == current_employee.id
        ).first()
        
        if not leave_request:
            return error_response(
                message="Leave request not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if leave_request.status != LeaveRequestStatus.PENDING:
            return error_response(
                message=f"Cannot cancel a request that is already {leave_request.status.value}. Only pending requests can be cancelled.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = LeaveRequestStatus.CANCELLED
        db.commit()
        db.refresh(leave_request)
        
        return success_response(
            message="Leave request cancelled successfully",
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Cancel leave request error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while cancelling the leave request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== ADMIN/MANAGER ENDPOINTS ====================

@router.get("/pending", status_code=status.HTTP_200_OK)
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending leave requests for the organization.
    Only accessible by organization admin/manager.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get all pending requests for employees in this organization
        pending_requests = db.query(LeaveRequest).join(Employee).filter(
            Employee.organization_id == organization.id,
            LeaveRequest.status == LeaveRequestStatus.PENDING
        ).order_by(LeaveRequest.created_at.asc()).all()
        
        # Prepare response data
        requests_data = []
        for req in pending_requests:
            requests_data.append({
                "id": str(req.id),
                "employee_id": str(req.employee_id),
                "employee_name": req.employee.full_name,
                "employee_email": req.employee.email,
                "request_type": req.request_type.value,
                "custom_type": req.custom_type,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "reason": req.reason,
                "status": req.status.value,
                "is_full_day": req.is_full_day,
                "hours_deducted": float(req.hours_deducted) if req.hours_deducted else None,
                "created_at": req.created_at.isoformat()
            })
        
        return success_response(
            message=f"Retrieved {len(requests_data)} pending request(s)",
            data=requests_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get pending requests error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving pending requests.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_leave_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    employee_id: Optional[UUID] = Query(None, description="Filter by employee ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    start_date_from: Optional[datetime] = Query(None, description="Filter requests starting from this date"),
    start_date_to: Optional[datetime] = Query(None, description="Filter requests starting until this date"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all leave requests for the organization with filtering options.
    Dashboard for managers to view and filter requests.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Build query
        query = db.query(LeaveRequest).join(Employee).filter(
            Employee.organization_id == organization.id
        )
        
        # Apply filters
        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        
        if status_filter:
            try:
                status_enum = LeaveRequestStatus(status_filter)
                query = query.filter(LeaveRequest.status == status_enum)
            except ValueError:
                return error_response(
                    message=f"Invalid status filter",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        if request_type:
            try:
                type_enum = LeaveRequestType(request_type)
                query = query.filter(LeaveRequest.request_type == type_enum)
            except ValueError:
                return error_response(
                    message=f"Invalid request type filter",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        if start_date_from:
            query = query.filter(LeaveRequest.start_date >= start_date_from)
        
        if start_date_to:
            query = query.filter(LeaveRequest.start_date <= start_date_to)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).limit(limit).offset(offset).all()
        
        # Prepare response data
        requests_data = []
        for req in leave_requests:
            reviewer_name = None
            if req.reviewer_id:
                reviewer = db.query(User).filter(User.id == req.reviewer_id).first()
                reviewer_name = reviewer.full_name if reviewer else None
            
            requests_data.append({
                "id": str(req.id),
                "employee_id": str(req.employee_id),
                "employee_name": req.employee.full_name,
                "employee_email": req.employee.email,
                "request_type": req.request_type.value,
                "custom_type": req.custom_type,
                "start_date": req.start_date.isoformat(),
                "end_date": req.end_date.isoformat(),
                "reason": req.reason,
                "status": req.status.value,
                "reviewer_id": req.reviewer_id,
                "reviewer_name": reviewer_name,
                "review_time": req.review_time.isoformat() if req.review_time else None,
                "review_notes": req.review_notes,
                "is_full_day": req.is_full_day,
                "hours_deducted": float(req.hours_deducted) if req.hours_deducted else None,
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat()
            })
        
        # Get summary counts
        summary_query = db.query(LeaveRequest).join(Employee).filter(
            Employee.organization_id == organization.id
        )
        pending_count = summary_query.filter(LeaveRequest.status == LeaveRequestStatus.PENDING).count()
        approved_count = summary_query.filter(LeaveRequest.status == LeaveRequestStatus.APPROVED).count()
        rejected_count = summary_query.filter(LeaveRequest.status == LeaveRequestStatus.REJECTED).count()
        cancelled_count = summary_query.filter(LeaveRequest.status == LeaveRequestStatus.CANCELLED).count()
        
        return success_response(
            message=f"Retrieved {len(requests_data)} leave request(s)",
            data={
                "requests": requests_data,
                "summary": {
                    "total": total_count,
                    "pending": pending_count,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "cancelled": cancelled_count
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count
                }
            },
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get all leave requests error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving leave requests.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{request_id}/approve", status_code=status.HTTP_200_OK)
async def approve_leave_request(
    request_id: UUID,
    request: ApproveRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a leave request.
    Updates attendance records and notifies employee.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get leave request
        leave_request = db.query(LeaveRequest).join(Employee).filter(
            LeaveRequest.id == request_id,
            Employee.organization_id == organization.id
        ).first()
        
        if not leave_request:
            return error_response(
                message="Leave request not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if leave_request.status != LeaveRequestStatus.PENDING:
            return error_response(
                message=f"Request is already {leave_request.status.value}. Cannot approve.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request status
        leave_request.status = LeaveRequestStatus.APPROVED
        leave_request.reviewer_id = current_user.id
        leave_request.review_time = datetime.utcnow()
        leave_request.review_notes = request.review_notes
        
        # Adjust attendance records
        await adjust_attendance_for_approved_request(leave_request, db)
        
        # Create in-app notification for employee
        NotificationService.create_employee_notification(
            db,
            employee_id=leave_request.employee_id,
            title="Leave request approved",
            message=f"Your {leave_request.request_type.value.lower()} request was approved.",
            category=NotificationCategory.LEAVE,
            payload={
                "leave_request_id": str(leave_request.id),
                "request_type": leave_request.request_type.value,
                "start_date": leave_request.start_date.isoformat(),
                "end_date": leave_request.end_date.isoformat(),
                "review_notes": request.review_notes
            },
            auto_commit=False
        )

        db.commit()
        db.refresh(leave_request)
        
        # Notify employee
        await EmailService.send_leave_request_decision_email(
            to_email=leave_request.employee.email,
            employee_name=leave_request.employee.full_name,
            request_type=leave_request.request_type.value,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            decision="approved",
            reviewer_name=current_user.full_name,
            review_notes=request.review_notes
        )
        
        # Prepare response
        response_data = {
            "id": str(leave_request.id),
            "status": leave_request.status.value,
            "reviewer_name": current_user.full_name,
            "review_time": leave_request.review_time.isoformat(),
            "review_notes": leave_request.review_notes
        }
        
        return success_response(
            message="Leave request approved successfully. Attendance records have been adjusted.",
            data=response_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Approve leave request error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while approving the leave request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/{request_id}/reject", status_code=status.HTTP_200_OK)
async def reject_leave_request(
    request_id: UUID,
    request: ApproveRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a leave request.
    Notifies employee of rejection.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get leave request
        leave_request = db.query(LeaveRequest).join(Employee).filter(
            LeaveRequest.id == request_id,
            Employee.organization_id == organization.id
        ).first()
        
        if not leave_request:
            return error_response(
                message="Leave request not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if leave_request.status != LeaveRequestStatus.PENDING:
            return error_response(
                message=f"Request is already {leave_request.status.value}. Cannot reject.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request status
        leave_request.status = LeaveRequestStatus.REJECTED
        leave_request.reviewer_id = current_user.id
        leave_request.review_time = datetime.utcnow()
        leave_request.review_notes = request.review_notes
        
        # In-app notification
        NotificationService.create_employee_notification(
            db,
            employee_id=leave_request.employee_id,
            title="Leave request rejected",
            message=f"Your {leave_request.request_type.value.lower()} request was rejected.",
            category=NotificationCategory.LEAVE,
            payload={
                "leave_request_id": str(leave_request.id),
                "request_type": leave_request.request_type.value,
                "start_date": leave_request.start_date.isoformat(),
                "end_date": leave_request.end_date.isoformat(),
                "review_notes": request.review_notes
            },
            auto_commit=False
        )

        db.commit()
        db.refresh(leave_request)
        
        # Notify employee
        await EmailService.send_leave_request_decision_email(
            to_email=leave_request.employee.email,
            employee_name=leave_request.employee.full_name,
            request_type=leave_request.request_type.value,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            decision="rejected",
            reviewer_name=current_user.full_name,
            review_notes=request.review_notes
        )
        
        # Prepare response
        response_data = {
            "id": str(leave_request.id),
            "status": leave_request.status.value,
            "reviewer_name": current_user.full_name,
            "review_time": leave_request.review_time.isoformat(),
            "review_notes": leave_request.review_notes
        }
        
        return success_response(
            message="Leave request rejected successfully",
            data=response_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Reject leave request error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while rejecting the leave request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== HELPER FUNCTIONS ====================

async def adjust_attendance_for_approved_request(leave_request: LeaveRequest, db: Session):
    """
    Adjust attendance records when a leave request is approved.
    For full-day leaves: marks days as excused
    For partial permissions: deducts hours from attendance
    """
    try:
        if leave_request.is_full_day:
            # For full-day leaves, create excused attendance records for each day
            current_date = leave_request.start_date.date()
            end_date = leave_request.end_date.date()
            
            while current_date <= end_date:
                # Check if there are any attendance records for this day
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                # Get existing attendances for this day
                existing_attendances = db.query(Attendance).filter(
                    Attendance.employee_id == leave_request.employee_id,
                    Attendance.timestamp >= day_start,
                    Attendance.timestamp <= day_end
                ).all()
                
                # If no attendance records exist, create excused records
                if not existing_attendances:
                    # Create excused check-in and check-out
                    check_in_time = datetime.combine(current_date, time(hour=9, minute=0))
                    check_out_time = datetime.combine(current_date, time(hour=17, minute=0))
                    
                    excused_check_in = Attendance(
                        employee_id=leave_request.employee_id,
                        attendance_type=AttendanceType.CHECK_IN,
                        timestamp=check_in_time,
                        notes=f"Excused - {leave_request.request_type.value}: {leave_request.reason}"
                    )
                    
                    excused_check_out = Attendance(
                        employee_id=leave_request.employee_id,
                        attendance_type=AttendanceType.CHECK_OUT,
                        timestamp=check_out_time,
                        hours_worked=Decimal("8.00"),  # Full day
                        check_in_id=None,  # Not linked to check-in since it's excused
                        notes=f"Excused - {leave_request.request_type.value}: {leave_request.reason}"
                    )
                    
                    db.add(excused_check_in)
                    db.add(excused_check_out)
                
                current_date += timedelta(days=1)
        
        else:
            # For partial permissions, deduct hours from attendance
            # This is handled by the hours_deducted field
            # The frontend/reporting system should use this to adjust calculations
            pass
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error adjusting attendance for approved request: {str(e)}")
        raise

