from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.subscription_access import get_organization_subscription
from app.services.fapshi_service import FapshiService
from decimal import Decimal
from app.models.organization import Organization
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionPlanEnum,
    SubscriptionStatus,
    Payment,
    PaymentStatus,
    PaymentProvider,
)
from app.models.employee import Employee
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    PlanFeaturesResponse,
    AllPlansResponse,
    SubscribeRequest,
    PaymentInitiationResponse,
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
            new_plan = SubscriptionPlanEnum(request.plan)
        except ValueError:
            return error_response(
                message=f"Invalid plan. Must be one of: {[p.value for p in SubscriptionPlanEnum]}",
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


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_to_plan(
    request: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subscribe to a subscription plan (first payment flow).
    Creates a pending subscription and initiates payment via Fapshi.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if subscription already exists
        existing_subscription = db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        if existing_subscription and existing_subscription.status == SubscriptionStatus.ACTIVE:
            return error_response(
                message="You already have an active subscription. Please update your existing subscription instead.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan exists and is active
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == request.plan_id,
            SubscriptionPlan.is_active == True  # noqa: E712
        ).first()
        
        if not plan:
            return error_response(
                message="Invalid or inactive subscription plan.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate amount in smallest currency unit (e.g., cents for XAF)
        # Fapshi expects amount in smallest unit, so multiply by 100 for XAF
        amount_in_smallest_unit = int(float(plan.amount) * 100)
        
        # Create or update subscription with status = pending
        if existing_subscription:
            # Update existing subscription
            subscription = existing_subscription
            subscription.plan_id = plan.id
            subscription.status = SubscriptionStatus.PENDING
            subscription.start_date = None  # Will be set when payment is confirmed
            subscription.next_billing_date = None  # Will be set when payment is confirmed
            subscription.last_paid_date = None
            subscription.grace_ends_at = None
            # Update legacy plan field for backward compatibility
            subscription.plan = SubscriptionPlanEnum.FREE  # Default, will be updated based on plan name
            subscription.monthly_price = plan.amount
        else:
            # Create new subscription
            subscription = Subscription(
                organization_id=organization.id,
                plan_id=plan.id,
                status=SubscriptionStatus.PENDING,
                start_date=None,
                next_billing_date=None,
                last_paid_date=None,
                grace_ends_at=None,
                plan=SubscriptionPlanEnum.FREE,  # Default, will be updated based on plan name
                monthly_price=plan.amount,
                is_active=True
            )
            db.add(subscription)
        
        db.flush()  # Flush to get subscription.id
        
        # Prepare payment initiation data
        payment_name = request.name or current_user.full_name
        payment_message = request.message or f"Subscription payment for {plan.name} plan"
        
        # Initiate payment via Fapshi
        fapshi_response = FapshiService.initiate_payment(
            amount=amount_in_smallest_unit,
            phone=request.phone,
            email=current_user.email,
            name=payment_name,
            external_id=str(subscription.id),  # Use subscription ID as external ID
            medium="mobile money",
            message=payment_message,
            user_id=str(current_user.id)
        )
        
        # Check if payment initiation was successful
        if "transId" not in fapshi_response:
            # Payment initiation failed
            error_msg = fapshi_response.get("message", "Failed to initiate payment")
            logger.error(f"Fapshi payment initiation failed: {error_msg} - subscription_id={subscription.id}")
            
            # Rollback subscription creation
            db.rollback()
            
            return error_response(
                message=f"Payment initiation failed: {error_msg}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment record with status = initiated
        payment = Payment(
            user_id=current_user.id,
            subscription_id=subscription.id,
            amount=plan.amount,
            currency=plan.currency,
            status=PaymentStatus.INITIATED,
            provider=PaymentProvider.FAPSHI,
            provider_ref=fapshi_response.get("transId"),
            provider_response=str(fapshi_response)  # Store full response as string
        )
        db.add(payment)
        
        # Commit all changes
        db.commit()
        db.refresh(subscription)
        db.refresh(payment)
        
        # Prepare response
        response_data = PaymentInitiationResponse(
            trans_id=fapshi_response.get("transId"),
            message=fapshi_response.get("message", "Payment initiated successfully"),
            date_initiated=fapshi_response.get("dateInitiated"),
            subscription_id=subscription.id,
            amount=float(plan.amount),
            currency=plan.currency,
            status=PaymentStatus.INITIATED.value
        )
        
        logger.info(f"Subscription created and payment initiated: subscription_id={subscription.id}, trans_id={fapshi_response.get('transId')}")
        
        return success_response(
            message="Subscription created and payment initiated successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in subscribe: {str(e)}")
        db.rollback()
        return error_response(
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Subscribe error: {str(e)}", exc_info=True)
        db.rollback()
        return error_response(
            message="An error occurred while processing your subscription.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

