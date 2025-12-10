from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.subscription_access import get_organization_subscription
from app.models.organization import Organization
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.employee import Employee
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    PlanFeaturesResponse,
    AllPlansResponse
)
from app.schemas.response import success_response, error_response
from app.utils.subscription_features import (
    get_plan_features,
    get_employee_limit,
    Feature,
    PLAN_FEATURES,
    EMPLOYEE_LIMITS
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["Subscription Management"])


@router.get("/current", status_code=status.HTTP_200_OK)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current subscription details for the organization.
    """
    try:
        organization, subscription = await get_organization_subscription(current_user, db)
        
        # Get current employee count
        from app.models.employee import Employee
        current_employee_count = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True  # noqa: E712
        ).count()
        
        employee_limit = get_employee_limit(subscription.plan)
        if employee_limit == -1:
            employee_limit_str = "Unlimited"
        else:
            employee_limit_str = str(employee_limit)
        
        # Check if trial is active
        is_trial = subscription.status == SubscriptionStatus.TRIAL
        trial_days_remaining = None
        if is_trial and subscription.trial_end_date:
            days_left = (subscription.trial_end_date - datetime.utcnow()).days
            trial_days_remaining = max(0, days_left)
        
        # Get available features
        features = get_plan_features(subscription.plan)
        
        response_data = SubscriptionResponse(
            id=subscription.id,
            plan=subscription.plan.value,
            status=subscription.status.value,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=subscription.subscription_end_date,
            monthly_price=float(subscription.monthly_price) if subscription.monthly_price else None,
            current_employee_count=current_employee_count,
            employee_limit=employee_limit_str,
            features=list(features),
            is_trial=is_trial,
            trial_days_remaining=trial_days_remaining
        )
        
        return success_response(
            message="Subscription retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscription error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving subscription.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/update", status_code=status.HTTP_200_OK)
async def update_subscription(
    request: SubscriptionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update subscription plan.
    This would typically be called after payment processing.
    """
    try:
        organization, subscription = await get_organization_subscription(current_user, db)
        
        # Validate new plan
        try:
            new_plan = SubscriptionPlan(request.plan)
        except ValueError:
            return error_response(
                message=f"Invalid plan. Must be one of: {[p.value for p in SubscriptionPlan]}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update subscription
        subscription.plan = new_plan
        
        # If upgrading from trial or expired, activate subscription
        if subscription.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.EXPIRED]:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.subscription_start_date = datetime.utcnow()
            # Set end date to 30 days from now
            subscription.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        
        # Update organization plan field for backward compatibility
        organization.plan = new_plan.value
        
        db.commit()
        db.refresh(subscription)
        
        # Recompute counts and limits
        current_employee_count = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True  # noqa: E712
        ).count()
        employee_limit = get_employee_limit(subscription.plan)
        employee_limit_str = "Unlimited" if employee_limit == -1 else str(employee_limit)
        
        # Get updated features
        features = get_plan_features(subscription.plan)
        
        response_data = SubscriptionResponse(
            id=subscription.id,
            plan=subscription.plan.value,
            status=subscription.status.value,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=subscription.subscription_end_date,
            monthly_price=float(subscription.monthly_price) if subscription.monthly_price else None,
            current_employee_count=current_employee_count,
            employee_limit=employee_limit_str,
            features=list(features),
            is_trial=False,
            trial_days_remaining=None
        )
        
        return success_response(
            message=f"Subscription updated to {new_plan.value} plan",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update subscription error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while updating subscription.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/plans", status_code=status.HTTP_200_OK)
async def get_all_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available subscription plans with their features and limits.
    """
    try:
        # Get current subscription to highlight it
        current_subscription = None
        try:
            _, sub = await get_organization_subscription(current_user, db)
            current_subscription = sub
        except HTTPException:
            pass  # No organization yet
        
        plans_data = []
        for plan in SubscriptionPlan:
            features = get_plan_features(plan)
            employee_limit = get_employee_limit(plan)
            
            is_current_plan = (
                current_subscription and 
                current_subscription.plan == plan
            )
            
            plans_data.append(PlanFeaturesResponse(
                plan=plan.value,
                employee_limit=employee_limit if employee_limit != -1 else None,
                features=list(features),
                is_current_plan=is_current_plan
            ))
        
        response_data = AllPlansResponse(plans=plans_data)
        
        return success_response(
            message="Plans retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get plans error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving plans.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

