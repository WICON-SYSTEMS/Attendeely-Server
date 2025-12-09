from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FeedbackResponse(BaseModel):
    """Response schema for feedback"""
    id: UUID
    user_id: Optional[int] = None
    employee_id: Optional[UUID] = None
    description: str
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """Response schema for feedback list"""
    feedback: list[FeedbackResponse]
    total: int
    limit: int
    offset: int

