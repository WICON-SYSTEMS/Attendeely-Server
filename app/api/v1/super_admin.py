from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_super_admin
from app.models.user import User
from app.models.organization import Organization
from app.models.employee import Employee
from app.models.subscription import Subscription
from app.models.feedback import Feedback
from app.schemas.super_admin import (
    SuperAdminOverviewStats,
    SuperAdminOrganizationSummary,
    SuperAdminOrganizationListResponse,
    SuperAdminUserSummary,
    SuperAdminUserListResponse,
    SuperAdminEmployeeSummary,
    SuperAdminEmployeeListResponse,
    SuperAdminSubscriptionSummary,
    SuperAdminSubscriptionListResponse,
    SuperAdminToggleOrganizationStatusRequest,
)
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


@router.get("/stats/overview", status_code=status.HTTP_200_OK)
async def get_super_admin_overview(
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    High-level global stats across all organizations.
    """
    try:
        total_orgs = db.query(func.count(Organization.id)).scalar() or 0
        active_orgs = (
            db.query(func.count(Organization.id))
            .filter(Organization.is_active.is_(True))
            .scalar()
            or 0
        )
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_employees = db.query(func.count(Employee.id)).scalar() or 0
        total_feedback = db.query(func.count(Feedback.id)).scalar() or 0
        total_subscriptions = db.query(func.count(Subscription.id)).scalar() or 0
        active_subscriptions = (
            db.query(func.count(Subscription.id))
            .filter(Subscription.is_active.is_(True))
            .scalar()
            or 0
        )

        # Subscriptions grouped by plan
        plan_rows = (
            db.query(Subscription.plan, func.count(Subscription.id))
            .group_by(Subscription.plan)
            .all()
        )
        subscriptions_by_plan = {str(plan): count for plan, count in plan_rows}

        stats = SuperAdminOverviewStats(
            total_organizations=total_orgs,
            active_organizations=active_orgs,
            total_users=total_users,
            total_employees=total_employees,
            total_feedback=total_feedback,
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            subscriptions_by_plan=subscriptions_by_plan,
        )

        return success_response(
            message="Super admin overview stats retrieved successfully",
            data=stats.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to load overview stats: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/organizations", status_code=status.HTTP_200_OK)
async def list_organizations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(
        None, description="Search by organization name or code"
    ),
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    List organizations across the platform, with admin, employee count, and subscription info.
    """
    try:
        query = db.query(Organization).join(User, Organization.admin_id == User.id)

        if is_active is not None:
            query = query.filter(Organization.is_active.is_(is_active))

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                (Organization.organization_name.ilike(like_pattern))
                | (Organization.organization_code.ilike(like_pattern))
            )

        total = query.count()

        orgs = (
            query.order_by(Organization.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        org_ids = [org.id for org in orgs]

        # Employee counts per org
        if org_ids:
            employee_counts_rows = (
                db.query(Employee.organization_id, func.count(Employee.id))
                .filter(Employee.organization_id.in_(org_ids))
                .group_by(Employee.organization_id)
                .all()
            )
            employee_counts = {org_id: count for org_id, count in employee_counts_rows}

            # Subscriptions per org
            subs = (
                db.query(Subscription)
                .filter(Subscription.organization_id.in_(org_ids))
                .all()
            )
            subs_by_org = {s.organization_id: s for s in subs}
        else:
            employee_counts = {}
            subs_by_org = {}

        summaries = []
        for org in orgs:
            admin = org.admin
            sub = subs_by_org.get(org.id)
            summaries.append(
                SuperAdminOrganizationSummary(
                    id=org.id,
                    organization_name=org.organization_name,
                    organization_code=org.organization_code,
                    country=org.country,
                    currency=org.currency,
                    is_active=org.is_active,
                    created_at=org.created_at,
                    admin_id=admin.id if admin else None,
                    admin_email=admin.email if admin else "",
                    employee_count=employee_counts.get(org.id, 0),
                    subscription_plan=str(sub.plan) if sub else None,
                    subscription_status=str(sub.status) if sub else None,
                )
            )

        response = SuperAdminOrganizationListResponse(
            organizations=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

        return success_response(
            message="Organizations retrieved successfully",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list organizations: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/organizations/{organization_id}", status_code=status.HTTP_200_OK)
async def get_organization_detail(
    organization_id: int,
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    Detailed information for a single organization, including admin, subscription, and counts.
    """
    try:
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        admin = org.admin
        employee_count = (
            db.query(func.count(Employee.id))
            .filter(Employee.organization_id == org.id)
            .scalar()
            or 0
        )
        sub = (
            db.query(Subscription)
            .filter(Subscription.organization_id == org.id)
            .first()
        )

        summary = SuperAdminOrganizationSummary(
            id=org.id,
            organization_name=org.organization_name,
            organization_code=org.organization_code,
            country=org.country,
            currency=org.currency,
            is_active=org.is_active,
            created_at=org.created_at,
            admin_id=admin.id if admin else None,
            admin_email=admin.email if admin else "",
            employee_count=employee_count,
            subscription_plan=str(sub.plan) if sub else None,
            subscription_status=str(sub.status) if sub else None,
        )

        return success_response(
            message="Organization detail retrieved successfully",
            data=summary.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message=f"Failed to load organization detail: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.patch(
    "/organizations/{organization_id}/status", status_code=status.HTTP_200_OK
)
async def toggle_organization_status(
    organization_id: int,
    payload: SuperAdminToggleOrganizationStatusRequest,
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    Activate / deactivate an organization.
    """
    try:
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        org.is_active = payload.is_active
        db.commit()
        db.refresh(org)

        return success_response(
            message="Organization status updated successfully",
            data={"id": org.id, "is_active": org.is_active},
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(
            message=f"Failed to update organization status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/users", status_code=status.HTTP_200_OK)
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    List all admin users (tenants) with their organizations.
    """
    try:
        query = db.query(User)
        total = query.count()
        users = (
            query.order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        summaries = []
        for user in users:
            org = user.organization
            summaries.append(
                SuperAdminUserSummary(
                    id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    is_active=user.is_active,
                    is_email_verified=user.is_email_verified,
                    is_super_admin=getattr(user, "is_super_admin", False),
                    created_at=user.created_at,
                    organization_id=org.id if org else None,
                    organization_name=org.organization_name if org else None,
                )
            )

        response = SuperAdminUserListResponse(
            users=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

        return success_response(
            message="Users retrieved successfully",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list users: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/employees", status_code=status.HTTP_200_OK)
async def list_employees(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organization_id: Optional[int] = Query(
        None, description="Optional filter: only employees of this organization"
    ),
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    List employees across all organizations, optionally filtered by organization.
    """
    try:
        query = db.query(Employee).join(Organization, Employee.organization_id == Organization.id)

        if organization_id is not None:
            query = query.filter(Employee.organization_id == organization_id)

        total = query.count()
        employees = (
            query.order_by(Employee.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        summaries = []
        for emp in employees:
            org = emp.organization
            summaries.append(
                SuperAdminEmployeeSummary(
                    id=str(emp.id),
                    full_name=emp.full_name,
                    email=emp.email,
                    department=emp.department,
                    job_title=emp.job_title,
                    role=str(emp.role.value),
                    is_active=emp.is_active,
                    organization_id=org.id if org else emp.organization_id,
                    organization_name=org.organization_name if org else "",
                )
            )

        response = SuperAdminEmployeeListResponse(
            employees=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

        return success_response(
            message="Employees retrieved successfully",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list employees: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/feedback", status_code=status.HTTP_200_OK)
async def list_all_feedback(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    List all feedback across the platform (separate from per-org admin view).
    """
    try:
        total = db.query(Feedback).count()
        feedback_rows = (
            db.query(Feedback)
            .order_by(Feedback.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Reuse existing feedback response shape to keep it simple
        from app.schemas.feedback import FeedbackResponse  # local import to avoid cycles

        feedback_list = [
            FeedbackResponse(
                id=fb.id,
                user_id=fb.user_id,
                employee_id=fb.employee_id,
                description=fb.description,
                image_url=fb.image_url,
                created_at=fb.created_at,
            )
            for fb in feedback_rows
        ]

        data = {
            "feedback": [item.model_dump() for item in feedback_list],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

        return success_response(
            message="All feedback retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list feedback: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/subscriptions", status_code=status.HTTP_200_OK)
async def list_subscriptions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    List all subscriptions with organization info.
    """
    try:
        query = db.query(Subscription).join(
            Organization, Subscription.organization_id == Organization.id
        )
        total = query.count()
        subs = (
            query.order_by(Subscription.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        summaries = []
        for sub in subs:
            org = sub.organization
            summaries.append(
                SuperAdminSubscriptionSummary(
                    id=sub.id,
                    organization_id=org.id if org else sub.organization_id,
                    organization_name=org.organization_name if org else "",
                    plan=str(sub.plan),
                    status=str(sub.status),
                    is_active=sub.is_active,
                    trial_start_date=sub.trial_start_date,
                    trial_end_date=sub.trial_end_date,
                    subscription_start_date=sub.subscription_start_date,
                    subscription_end_date=sub.subscription_end_date,
                    monthly_price=float(sub.monthly_price)
                    if sub.monthly_price is not None
                    else None,
                )
            )

        response = SuperAdminSubscriptionListResponse(
            subscriptions=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )

        return success_response(
            message="Subscriptions retrieved successfully",
            data=response.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list subscriptions: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


