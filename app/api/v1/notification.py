from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_employee
from app.models.notification import Notification, NotificationRecipient
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.employee import Employee

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize_notifications(notifications: list[Notification]) -> list[dict]:
    return [
        NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            category=notification.category.value,
            recipient_type=notification.recipient_type.value,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            payload=notification.payload
        ).model_dump()
        for notification in notifications
    ]


@router.get("/admin", status_code=status.HTTP_200_OK)
async def get_admin_notifications(
    is_read: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List notifications for the current admin."""
    try:
        query = db.query(Notification).filter(
            Notification.recipient_type == NotificationRecipient.USER,
            Notification.user_id == current_user.id
        )

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()

        return success_response(
            message=f"Retrieved {len(notifications)} notification(s)",
            data=NotificationListResponse(
                notifications=_serialize_notifications(notifications),
                total=total,
                limit=limit,
                offset=offset
            ).model_dump(),
            status_code=status.HTTP_200_OK
        )
    except Exception as exc:
        return error_response(
            message="Failed to load notifications",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/admin/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_admin_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific admin notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_type == NotificationRecipient.USER,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        return error_response(
            message="Notification not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()

    return success_response(
        message="Notification marked as read",
        data=NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            category=notification.category.value,
            recipient_type=notification.recipient_type.value,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            payload=notification.payload
        ).model_dump(),
        status_code=status.HTTP_200_OK
    )


@router.put("/admin/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_admin_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread admin notifications as read."""
    updated = db.query(Notification).filter(
        Notification.recipient_type == NotificationRecipient.USER,
        Notification.user_id == current_user.id,
        Notification.is_read == False  # noqa: E712
    ).update(
        {"is_read": True, "read_at": datetime.utcnow()},
        synchronize_session=False
    )
    db.commit()

    return success_response(
        message=f"{updated} notification(s) marked as read",
        data={"updated": updated},
        status_code=status.HTTP_200_OK
    )


@router.get("/employee", status_code=status.HTTP_200_OK)
async def get_employee_notifications(
    is_read: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """List notifications for the current employee."""
    try:
        query = db.query(Notification).filter(
            Notification.recipient_type == NotificationRecipient.EMPLOYEE,
            Notification.employee_id == current_employee.id
        )

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()

        return success_response(
            message=f"Retrieved {len(notifications)} notification(s)",
            data=NotificationListResponse(
                notifications=_serialize_notifications(notifications),
                total=total,
                limit=limit,
                offset=offset
            ).model_dump(),
            status_code=status.HTTP_200_OK
        )
    except Exception:
        return error_response(
            message="Failed to load notifications",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/employee/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_employee_notification_read(
    notification_id: UUID,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Mark a specific employee notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_type == NotificationRecipient.EMPLOYEE,
        Notification.employee_id == current_employee.id
    ).first()

    if not notification:
        return error_response(
            message="Notification not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()

    return success_response(
        message="Notification marked as read",
        data=NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            category=notification.category.value,
            recipient_type=notification.recipient_type.value,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            payload=notification.payload
        ).model_dump(),
        status_code=status.HTTP_200_OK
    )


@router.put("/employee/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_employee_notifications_read(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Mark all unread employee notifications as read."""
    updated = db.query(Notification).filter(
        Notification.recipient_type == NotificationRecipient.EMPLOYEE,
        Notification.employee_id == current_employee.id,
        Notification.is_read == False  # noqa: E712
    ).update(
        {"is_read": True, "read_at": datetime.utcnow()},
        synchronize_session=False
    )
    db.commit()

    return success_response(
        message=f"{updated} notification(s) marked as read",
        data={"updated": updated},
        status_code=status.HTTP_200_OK
    )


