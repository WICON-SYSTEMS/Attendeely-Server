"""
Dependencies for subscription context.
Feature and plan checks are intentionally open.
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.organization import Organization
from app.models.subscription import Subscription, SubscriptionPlanEnum, SubscriptionStatus
from app.models.user import User


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
        trial_end = datetime.utcnow() + timedelta(days=7)
        # Use enum values explicitly to match DB enum ('Free', 'Standard', 'Enterprise')
        subscription = Subscription(
            organization_id=organization.id,
            plan=SubscriptionPlanEnum.FREE.value,
            status=SubscriptionStatus.TRIAL.value,
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
    Feature checks are currently open for all organizations.
    Usage: require_geofencing = create_feature_requirement(Feature.GEOFENCING)
    Then use: Depends(require_geofencing)
    """
    async def require_feature_dep(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> tuple[Organization, Subscription]:
        """
        Dependency to resolve organization and subscription context.
        Does not block access by plan/feature.
        """
        # Feature gates are open: always allow access.
        organization, subscription = await get_organization_subscription(current_user, db)
        return organization, subscription
    
    return require_feature_dep


async def check_employee_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Organization, Subscription]:
    """
    Dependency to resolve organization and subscription context.
    Employee-limit enforcement is disabled.
    """
    # Employee limits are open: always allow employee creation.
    organization, subscription = await get_organization_subscription(current_user, db)
    return organization, subscription


async def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[Organization, Subscription]:
    """
    Dependency to resolve organization and subscription context.
    Subscription-status enforcement is disabled.
    
    Example usage:
        @router.post("/some-endpoint")
        async def some_endpoint(
            organization, subscription = Depends(require_active_subscription),
            db: Session = Depends(get_db)
        ):
            # Endpoint code here
    """
    # Subscription status gates are open: always allow access.
    organization, subscription = await get_organization_subscription(current_user, db)
    return organization, subscription

