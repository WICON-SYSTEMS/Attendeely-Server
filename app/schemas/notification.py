from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    category: str
    recipient_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    payload: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata for clients")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    limit: int
    offset: int


