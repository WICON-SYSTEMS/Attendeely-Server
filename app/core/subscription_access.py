"""
Dependencies for checking subscription and feature access
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.organization import Organization
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.user import User
from app.utils.subscription_features import (
    has_feature,
    get_employee_limit,
    is_within_employee_limit,
    Feature,
    is_trial_active,
    is_subscription_active
)


async def get_organization_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Organization, Optional[Subscription]]:
    """
    Get organization and its subscription.
    Creates a default FREE trial subscription if none exists.
    """
    organization = db.query(Organization).filter(
        Organization.admin_id == current_user.id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()
    
    # Create default subscription if none exists
    if not subscription:
        from app.models.subscription import Subscription
        trial_end = datetime.utcnow() + timedelta(days=7)
        subscription = Subscription(
            organization_id=organization.id,
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.TRIAL,
            trial_start_date=datetime.utcnow(),
            trial_end_date=trial_end
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    
    return organization, subscription


def create_feature_requirement(feature: str):
    """
    Factory function to create a feature requirement dependency.
    Usage: require_geofencing = create_feature_requirement(Feature.GEOFENCING)
    Then use: Depends(require_geofencing)
    """
    async def require_feature_dep(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> tuple[Organization, Subscription]:
        """
        Dependency to require a specific feature.
        Raises HTTPException if feature is not available.
        """
        organization, subscription = await get_organization_subscription(current_user, db)
        
        # Check if subscription is active
        if subscription.status == SubscriptionStatus.TRIAL:
            if subscription.trial_end_date and not is_trial_active(subscription.trial_end_date):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Trial period has expired. Please upgrade your subscription."
                )
        elif subscription.status == SubscriptionStatus.ACTIVE:
            if subscription.subscription_end_date and not is_subscription_active(subscription.subscription_end_date):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Subscription has expired. Please renew your subscription."
                )
        elif subscription.status in [SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription is not active. Please upgrade or renew your subscription."
            )
        
        # Check feature access
        if not has_feature(subscription.plan, feature):
            plan_name = subscription.plan.value
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature is not available in the {plan_name} plan. Please upgrade to access this feature."
            )
        
        return organization, subscription
    
    return require_feature_dep


async def check_employee_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Organization, Subscription]:
    """
    Dependency to check if organization can add more employees.
    Raises HTTPException if employee limit is reached.
    """
    organization, subscription = await get_organization_subscription(current_user, db)
    
    from app.models.employee import Employee
    current_employee_count = db.query(Employee).filter(
        Employee.organization_id == organization.id,
        Employee.is_active == True  # noqa: E712
    ).count()
    
    if not is_within_employee_limit(subscription.plan, current_employee_count):
        limit = get_employee_limit(subscription.plan)
        plan_name = subscription.plan.value
        if limit == -1:
            # Should not happen, but handle it
            return organization, subscription
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Employee limit reached ({limit} employees) for {plan_name} plan. Please upgrade to add more employees."
        )
    
    return organization, subscription

