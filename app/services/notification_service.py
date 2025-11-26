from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationCategory,
    NotificationRecipient
)


class NotificationService:
    """Utility helpers for creating in-app notifications."""

    @staticmethod
    def create_user_notification(
        db: Session,
        *,
        user_id: int,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.GENERAL,
        payload: Optional[dict[str, Any]] = None,
        auto_commit: bool = False
    ) -> Notification:
        notification = Notification(
            recipient_type=NotificationRecipient.USER,
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            payload=payload or {}
        )
        db.add(notification)

        if auto_commit:
            db.commit()
            db.refresh(notification)
        else:
            db.flush()

        return notification

    @staticmethod
    def create_employee_notification(
        db: Session,
        *,
        employee_id,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.GENERAL,
        payload: Optional[dict[str, Any]] = None,
        auto_commit: bool = False
    ) -> Notification:
        notification = Notification(
            recipient_type=NotificationRecipient.EMPLOYEE,
            employee_id=employee_id,
            title=title,
            message=message,
            category=category,
            payload=payload or {}
        )
        db.add(notification)

        if auto_commit:
            db.commit()
            db.refresh(notification)
        else:
            db.flush()

        return notification


