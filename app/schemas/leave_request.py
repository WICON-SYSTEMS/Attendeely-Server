from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.leave_request import LeaveRequestType, LeaveRequestStatus


class CreateLeaveRequestRequest(BaseModel):
    """Request schema for creating a leave/permission request"""
    request_type: LeaveRequestType = Field(..., description="Type of request (Permission, Leave, Sick, Vacation, Custom)")
    custom_type: Optional[str] = Field(None, max_length=100, description="Custom type name (required if request_type is Custom)")
    start_date: datetime = Field(..., description="Start date and time of the request")
    end_date: datetime = Field(..., description="End date and time of the request")
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for the request (required)")
    is_full_day: bool = Field(True, description="True for full day leave, False for partial permission (hours)")
    hours_deducted: Optional[float] = Field(None, ge=0, le=24, description="Hours to deduct for partial permission (required if is_full_day is False)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_type": "Leave",
                "start_date": "2024-12-01T09:00:00",
                "end_date": "2024-12-03T17:00:00",
                "reason": "Family emergency - need to travel home",
                "is_full_day": True
            }
        }


class ApproveRejectRequest(BaseModel):
    """Request schema for approving or rejecting a leave request"""
    review_notes: Optional[str] = Field(None, max_length=500, description="Optional notes from reviewer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_notes": "Approved - valid reason provided"
            }
        }


class LeaveRequestResponse(BaseModel):
    """Response schema for leave request data"""
    id: UUID
    employee_id: UUID
    employee_name: str
    employee_email: str
    request_type: str
    custom_type: Optional[str] = None
    start_date: datetime
    end_date: datetime
    reason: str
    status: str
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_time: Optional[datetime] = None
    review_notes: Optional[str] = None
    is_full_day: bool
    hours_deducted: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeaveRequestSummaryResponse(BaseModel):
    """Summary response for leave requests with counts"""
    total: int
    pending: int
    approved: int
    rejected: int
    cancelled: int
    requests: list[LeaveRequestResponse]

