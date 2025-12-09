from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import decode_access_token, hash_token
from app.models.user import User
from app.models.employee import Employee
from app.models.feedback import Feedback
from app.models.employee_session import EmployeeSession
from app.schemas.feedback import FeedbackResponse, FeedbackListResponse
from app.schemas.response import success_response, error_response
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])

security = HTTPBearer(auto_error=False)


async def get_current_user_or_employee(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[Optional[User], Optional[Employee]]:
    """
    Get current authenticated user or employee from JWT token.
    Returns tuple of (user, employee) where one will be None.
    """
    if not credentials:
        return None, None
    
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        return None, None
    
    # Try to get user first (admin)
    email = payload.get("sub")
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user and user.is_active and user.is_email_verified:
            return user, None
    
    # Try to get employee
    employee_id = payload.get("employee_id")
    if employee_id:
        try:
            if isinstance(employee_id, str):
                employee_id = UUID(employee_id)
            
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if employee and employee.is_active:
                # Verify session is active
                token_hash = hash_token(token)
                active_session = db.query(EmployeeSession).filter(
                    EmployeeSession.employee_id == employee_id,
                    EmployeeSession.token_hash == token_hash,
                    EmployeeSession.is_active == True,
                    EmployeeSession.expires_at > datetime.utcnow()
                ).first()
                
                if active_session:
                    return None, employee
        except (ValueError, TypeError):
            pass
    
    return None, None


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    description: str = Form(..., min_length=10, max_length=5000, description="Description of the technical issue"),
    image: Optional[UploadFile] = File(None, description="Optional image attachment (JPEG, PNG, WEBP - Max 5MB)"),
    auth_result: tuple[Optional[User], Optional[Employee]] = Depends(get_current_user_or_employee),
    db: Session = Depends(get_db)
):
    """
    Submit feedback with optional image attachment.
    Can be submitted by either an authenticated user (admin) or employee.
    """
    try:
        user, employee = auth_result
        
        if not user and not employee:
            return error_response(
                message="Authentication required. Please login to submit feedback.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        user_id = user.id if user else None
        employee_id = employee.id if employee else None
        
        # Create feedback record
        new_feedback = Feedback(
            user_id=user_id,
            employee_id=employee_id,
            description=description
        )
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        # Upload image if provided
        image_url = None
        if image:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if image.content_type not in allowed_types:
                # Rollback feedback creation
                db.delete(new_feedback)
                db.commit()
                return error_response(
                    message="Invalid file type. Only JPEG, PNG, and WEBP images are allowed.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 5MB)
            contents = await image.read()
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                # Rollback feedback creation
                db.delete(new_feedback)
                db.commit()
                return error_response(
                    message="File size too large. Maximum size is 5MB.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload to Cloudinary
            image_url = await CloudinaryService.upload_feedback_image(
                contents,
                image.filename,
                new_feedback.id
            )
            
            if image_url:
                new_feedback.image_url = image_url
                db.commit()
                db.refresh(new_feedback)
            else:
                logger.warning(f"Failed to upload image for feedback {new_feedback.id}")
        
        # Prepare response
        response_data = FeedbackResponse(
            id=new_feedback.id,
            user_id=new_feedback.user_id,
            employee_id=new_feedback.employee_id,
            description=new_feedback.description,
            image_url=new_feedback.image_url,
            created_at=new_feedback.created_at
        )
        
        return success_response(
            message="Feedback submitted successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Submit feedback error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while submitting feedback. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/list", status_code=status.HTTP_200_OK)
async def list_feedback(
    limit: int = Query(20, ge=1, le=100, description="Number of feedback items to return"),
    offset: int = Query(0, ge=0, description="Number of feedback items to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all feedback messages (admin only).
    Returns paginated list of feedback submissions.
    """
    try:
        # Get total count
        total = db.query(Feedback).count()
        
        # Get paginated feedback
        feedback_list = db.query(Feedback).order_by(
            Feedback.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Prepare response data
        feedback_responses = [
            FeedbackResponse(
                id=fb.id,
                user_id=fb.user_id,
                employee_id=fb.employee_id,
                description=fb.description,
                image_url=fb.image_url,
                created_at=fb.created_at
            )
            for fb in feedback_list
        ]
        
        response_data = FeedbackListResponse(
            feedback=feedback_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
        return success_response(
            message="Feedback retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"List feedback error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving feedback.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

