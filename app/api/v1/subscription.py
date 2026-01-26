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
    FapshiWebhookRequest,
    PaymentStatusResponse,
    TestPaymentRequest,
    SubscriptionStatusByTransIdResponse,
    PaymentHistoryItem,
    PaymentHistoryResponse,
    PendingPaymentResponse,
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
        
        # Check if subscription has expired and update status if needed
        if subscription.status == SubscriptionStatus.ACTIVE and subscription.subscription_end_date:
            if datetime.utcnow() > subscription.subscription_end_date:
                subscription.status = SubscriptionStatus.EXPIRED
                subscription.is_active = False
                db.commit()
                db.refresh(subscription)
        
        # Get plan from database to ensure consistency (plan enum might be out of sync)
        plan_name = None
        plan_from_db = None
        if subscription.plan_id:
            plan_from_db = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            if plan_from_db:
                plan_name = plan_from_db.name
                # Sync plan enum if it's out of sync
                try:
                    plan_enum = SubscriptionPlanEnum(plan_name)
                    if subscription.plan != plan_enum:
                        subscription.plan = plan_enum
                        db.commit()
                        db.refresh(subscription)
                except ValueError:
                    pass  # Plan name doesn't match enum, keep existing
        
        # Fallback to enum value if plan_id is not set
        if not plan_name:
            plan_name = subscription.plan.value if subscription.plan else "Free"
        
        # Get plan enum for feature lookup (use database plan if available, otherwise enum)
        plan_for_features = subscription.plan
        if plan_from_db:
            try:
                plan_for_features = SubscriptionPlanEnum(plan_from_db.name)
            except ValueError:
                pass  # Keep existing plan enum
        
        # Get current employee count
        from app.models.employee import Employee
        current_employee_count = db.query(Employee).filter(
            Employee.organization_id == organization.id,
            Employee.is_active == True  # noqa: E712
        ).count()
        
        employee_limit = get_employee_limit(plan_for_features)
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
        features = get_plan_features(plan_for_features)
        
        # Use monthly_price from subscription, but if it's None and we have plan_from_db, use plan amount
        monthly_price = float(subscription.monthly_price) if subscription.monthly_price else None
        if monthly_price is None and plan_from_db:
            monthly_price = float(plan_from_db.amount)
        
        response_data = SubscriptionResponse(
            id=subscription.id,
            plan=plan_name,  # Use plan name from database for consistency
            status=subscription.status.value,
            trial_start_date=subscription.trial_start_date,
            trial_end_date=subscription.trial_end_date,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=subscription.subscription_end_date,
            monthly_price=monthly_price,
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
    Get all available subscription plans with their features, limits, and pricing.
    Returns plans from the database with their IDs for frontend to use.
    """
    try:
        # Get current subscription to highlight it
        current_subscription = None
        try:
            _, sub = await get_organization_subscription(current_user, db)
            current_subscription = sub
        except HTTPException:
            pass  # No organization yet
        
        # Query active plans from database
        db_plans = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True  # noqa: E712
        ).order_by(SubscriptionPlan.amount.asc()).all()
        
        plans_data = []
        for db_plan in db_plans:
            # Map plan name to enum for feature lookup
            try:
                plan_enum = SubscriptionPlanEnum(db_plan.name)
            except ValueError:
                # If plan name doesn't match enum, skip feature lookup
                plan_enum = None
            
            # Get features and limits from enum-based system
            if plan_enum:
                features = get_plan_features(plan_enum)
                employee_limit = get_employee_limit(plan_enum)
            else:
                features = set()
                employee_limit = None
            
            # Check if this is the current plan
            is_current_plan = False
            if current_subscription:
                if current_subscription.plan_id == db_plan.id:
                    is_current_plan = True
                elif current_subscription.plan and current_subscription.plan.value == db_plan.name:
                    is_current_plan = True
            
            plans_data.append(PlanFeaturesResponse(
                id=db_plan.id,
                name=db_plan.name,
                amount=float(db_plan.amount),
                currency=db_plan.currency,
                interval=db_plan.interval,
                description=db_plan.description,
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
        
        # Check if subscription is truly active (not expired)
        if existing_subscription:
            # Check if subscription has expired
            is_expired = False
            if existing_subscription.subscription_end_date:
                is_expired = datetime.utcnow() > existing_subscription.subscription_end_date
            
            # If subscription is expired, update status
            if is_expired and existing_subscription.status == SubscriptionStatus.ACTIVE:
                existing_subscription.status = SubscriptionStatus.EXPIRED
                existing_subscription.is_active = False
                db.commit()
                db.refresh(existing_subscription)
            
            # Only block if subscription is actually active (not expired, cancelled, or pending)
            # Allow resubscription if expired, cancelled, or pending
            if existing_subscription.status == SubscriptionStatus.ACTIVE and not is_expired:
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
        
        # Calculate amount for Fapshi (Fapshi expects amount in base currency, not smallest unit)
        # For XAF, send the amount directly (e.g., 33000 for 33,000 XAF)
        amount_for_fapshi = int(float(plan.amount))
        
        # Determine if we should create a new subscription or update existing one
        # Create a NEW subscription if:
        # 1. No existing subscription exists, OR
        # 2. Existing subscription is expired, cancelled, or past_due (allows new payment cycle)
        # Update existing subscription only if it's in PENDING status (payment retry)
        should_create_new = True
        if existing_subscription:
            # Only update if subscription is already PENDING (retry scenario)
            # Otherwise, create a new subscription for a new payment cycle
            if existing_subscription.status == SubscriptionStatus.PENDING:
                should_create_new = False
            # If expired, cancelled, or past_due, create a new subscription
            elif existing_subscription.status in [
                SubscriptionStatus.EXPIRED,
                SubscriptionStatus.CANCELLED,
                SubscriptionStatus.PAST_DUE
            ]:
                should_create_new = True
            else:
                # For any other status (shouldn't happen, but create new to be safe)
                should_create_new = True
        
        # Set plan enum based on plan name from database
        try:
            plan_enum = SubscriptionPlanEnum(plan.name)
        except ValueError:
            # If plan name doesn't match enum, default to FREE
            plan_enum = SubscriptionPlanEnum.FREE
            logger.warning(f"Plan name '{plan.name}' doesn't match SubscriptionPlanEnum, defaulting to FREE")
        
        # Create or update subscription with status = pending
        if existing_subscription and not should_create_new:
            # Update existing PENDING subscription (payment retry scenario)
            subscription = existing_subscription
            subscription.plan_id = plan.id
            subscription.status = SubscriptionStatus.PENDING
            subscription.start_date = None  # Will be set when payment is confirmed
            subscription.next_billing_date = None  # Will be set when payment is confirmed
            subscription.last_paid_date = None
            subscription.grace_ends_at = None
            # Update plan enum field to match the selected plan
            subscription.plan = plan_enum
            subscription.monthly_price = plan.amount
            subscription.is_active = True
        else:
            # Create new subscription (new payment cycle)
            subscription = Subscription(
                organization_id=organization.id,
                plan_id=plan.id,
                status=SubscriptionStatus.PENDING,
                start_date=None,
                next_billing_date=None,
                last_paid_date=None,
                grace_ends_at=None,
                plan=plan_enum,  # Set plan enum based on plan name
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
            amount=amount_for_fapshi,
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


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel the current active subscription.
    Sets status to CANCELLED and deactivates the subscription.
    """
    try:
        # Get user's organization and subscription
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        subscription = db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        if not subscription:
            return error_response(
                message="No subscription found to cancel.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if subscription is already cancelled
        if subscription.status == SubscriptionStatus.CANCELLED:
            return error_response(
                message="Subscription is already cancelled.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if subscription is already expired
        if subscription.status == SubscriptionStatus.EXPIRED:
            return error_response(
                message="Subscription is already expired. No need to cancel.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the subscription
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.is_active = False
        subscription.next_billing_date = None  # Clear next billing date
        
        # Update organization plan to Free Trial
        organization.plan = "Free Trial"
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Subscription cancelled: subscription_id={subscription.id}, user_id={current_user.id}")
        
        return success_response(
            message="Subscription cancelled successfully. Your subscription will remain active until the end of the current billing period.",
            data={
                "subscription_id": subscription.id,
                "status": subscription.status.value,
                "cancelled_at": datetime.utcnow().isoformat()
            },
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel subscription error: {str(e)}", exc_info=True)
        db.rollback()
        return error_response(
            message="An error occurred while cancelling your subscription.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/test-payment", status_code=status.HTTP_201_CREATED)
async def test_payment(
    request: TestPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to initiate a small payment (100 XAF) for testing purposes.
    This helps verify the payment flow without requiring large amounts.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # For test payments, always create a new subscription to track each test payment separately
        # Get the Free plan for testing
        free_plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == "Free"
        ).first()
        
        if not free_plan:
            return error_response(
                message="Free plan not found. Please seed subscription plans first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Create a new test subscription for each test payment
        # This ensures each test payment has its own subscription_id for tracking
        subscription = Subscription(
            organization_id=organization.id,
            plan_id=free_plan.id,
            status=SubscriptionStatus.PENDING,
            plan=SubscriptionPlanEnum.FREE,
            monthly_price=Decimal("0.00"),
            is_active=True
        )
        db.add(subscription)
        db.flush()
        
        # Test payment amount: 100 XAF
        test_amount = Decimal("100.00")
        amount_for_fapshi = 100  # 100 XAF
        
        # Prepare payment initiation data
        payment_name = request.name or current_user.full_name
        payment_message = request.message or "Test payment - 100 XAF"
        
        # Initiate payment via Fapshi
        fapshi_response = FapshiService.initiate_payment(
            amount=amount_for_fapshi,
            phone=request.phone,
            email=current_user.email,
            name=payment_name,
            external_id=f"TEST_{subscription.id}",  # Prefix with TEST_ to identify test payments
            medium="mobile money",
            message=payment_message,
            user_id=str(current_user.id)
        )
        
        # Check if payment initiation was successful
        if "transId" not in fapshi_response:
            error_msg = fapshi_response.get("message", "Failed to initiate payment")
            logger.error(f"Fapshi test payment initiation failed: {error_msg} - subscription_id={subscription.id}")
            db.rollback()
            return error_response(
                message=f"Payment initiation failed: {error_msg}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment record with status = initiated
        payment = Payment(
            user_id=current_user.id,
            subscription_id=subscription.id,
            amount=test_amount,
            currency="XAF",
            status=PaymentStatus.INITIATED,
            provider=PaymentProvider.FAPSHI,
            provider_ref=fapshi_response.get("transId"),
            provider_response=str(fapshi_response)
        )
        db.add(payment)
        
        # Commit all changes
        db.commit()
        db.refresh(subscription)
        db.refresh(payment)
        
        # Prepare response
        response_data = PaymentInitiationResponse(
            trans_id=fapshi_response.get("transId"),
            message=fapshi_response.get("message", "Test payment initiated successfully"),
            date_initiated=fapshi_response.get("dateInitiated"),
            subscription_id=subscription.id,
            amount=100.0,  # Test amount
            currency="XAF",
            status=PaymentStatus.INITIATED.value
        )
        
        logger.info(f"Test payment initiated: payment_id={payment.id}, trans_id={fapshi_response.get('transId')}, amount=100 XAF")
        
        return success_response(
            message="Test payment (100 XAF) initiated successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in test payment: {str(e)}")
        db.rollback()
        return error_response(
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Test payment error: {str(e)}", exc_info=True)
        db.rollback()
        return error_response(
            message="An error occurred while processing test payment.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def fapshi_webhook(
    webhook_data: FapshiWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive payment status updates from Fapshi.
    This endpoint is called by Fapshi when payment status changes.
    No authentication required (Fapshi calls this directly).
    """
    try:
        # Log full webhook payload for debugging
        logger.info(f"Received Fapshi webhook - Full payload: {webhook_data.model_dump()}")
        logger.info(f"Webhook details - transId: {webhook_data.transId}, status: '{webhook_data.status}', externalId: {webhook_data.externalId}")
        
        # Find payment by provider_ref (transId)
        payment = db.query(Payment).filter(
            Payment.provider_ref == webhook_data.transId,
            Payment.provider == PaymentProvider.FAPSHI
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for transId: {webhook_data.transId}")
            return error_response(
                message="Payment not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"Found payment: payment_id={payment.id}, current_status={payment.status.value}, subscription_id={payment.subscription_id}")
        
        # Update payment status and response
        payment.provider_response = str(webhook_data.model_dump())
        
        # Handle payment status (Fapshi sends "SUCCESSFUL" in uppercase)
        status_lower = webhook_data.status.lower()
        logger.info(f"Processing status: original='{webhook_data.status}', lowercased='{status_lower}'")
        if status_lower in ["success", "successful", "completed", "paid"]:
            # Payment successful
            payment.status = PaymentStatus.SUCCESS
            
            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.id == payment.subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"Subscription not found for payment: payment_id={payment.id}")
                db.commit()
                return error_response(
                    message="Subscription not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Get plan details
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            
            if not plan:
                logger.error(f"Plan not found for subscription: subscription_id={subscription.id}")
                db.commit()
                return error_response(
                    message="Plan not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Activate subscription
            now = datetime.utcnow()
            
            # Calculate billing dates based on plan interval
            if plan.interval == "monthly":
                next_billing = now + timedelta(days=30)
            elif plan.interval == "yearly":
                next_billing = now + timedelta(days=365)
            else:
                # Default to monthly
                next_billing = now + timedelta(days=30)
            
            # Update subscription
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.start_date = now
            subscription.next_billing_date = next_billing
            subscription.last_paid_date = now
            subscription.subscription_start_date = now
            subscription.subscription_end_date = next_billing
            subscription.is_active = True
            
            # Update plan enum field based on plan name
            try:
                subscription.plan = SubscriptionPlanEnum(plan.name)
            except ValueError:
                # If plan name doesn't match enum, keep existing or set to FREE
                subscription.plan = SubscriptionPlanEnum.FREE
            
            # Update organization plan
            organization = db.query(Organization).filter(
                Organization.id == subscription.organization_id
            ).first()
            
            if organization:
                organization.plan = plan.name
            
            db.commit()
            db.refresh(subscription)
            db.refresh(payment)
            
            logger.info(f"Subscription activated: subscription_id={subscription.id}, payment_id={payment.id}, transId={webhook_data.transId}")
            
            return success_response(
                message="Payment confirmed and subscription activated",
                data={
                    "payment_id": payment.id,
                    "subscription_id": subscription.id,
                    "status": "success"
                },
                status_code=status.HTTP_200_OK
            )
            
        elif status_lower in ["failed", "error", "cancelled", "failure"]:
            # Payment failed
            payment.status = PaymentStatus.FAILED
            
            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.id == payment.subscription_id
            ).first()
            
            if subscription:
                # Update subscription status based on current state
                if subscription.status == SubscriptionStatus.PENDING:
                    # Payment failed for a pending subscription - mark as expired/cancelled
                    # This means the subscription never activated because payment failed
                    subscription.status = SubscriptionStatus.EXPIRED
                    subscription.is_active = False
                    logger.info(f"Subscription expired due to failed payment: subscription_id={subscription.id}, payment_id={payment.id}")
                elif subscription.status == SubscriptionStatus.ACTIVE:
                    # Payment failed but subscription was already active
                    # Keep subscription active (user might have multiple payment attempts)
                    # Just mark the payment as failed, subscription continues
                    logger.info(f"Payment failed for active subscription (keeping subscription active): subscription_id={subscription.id}, payment_id={payment.id}")
                # For other statuses (EXPIRED, CANCELLED, etc.), don't change subscription status
            else:
                logger.warning(f"Subscription not found for failed payment: payment_id={payment.id}, subscription_id={payment.subscription_id}")
            
            db.commit()
            db.refresh(payment)
            if subscription:
                db.refresh(subscription)
            
            logger.warning(f"Payment failed: payment_id={payment.id}, transId={webhook_data.transId}, status_received='{webhook_data.status}'")
            
            return success_response(
                message="Payment status updated",
                data={
                    "payment_id": payment.id,
                    "subscription_id": subscription.id if subscription else None,
                    "subscription_status": subscription.status.value if subscription else None,
                    "status": "failed"
                },
                status_code=status.HTTP_200_OK
            )
        
        else:
            # Unknown status - log full details for debugging
            logger.warning(f"Unknown payment status: '{webhook_data.status}' (lowercased: '{status_lower}'), transId={webhook_data.transId}")
            logger.warning(f"Full webhook payload: {webhook_data.model_dump()}")
            # Don't update payment status for unknown statuses - keep as initiated
            db.commit()
            
            return success_response(
                message="Webhook received with unknown status",
                data={"status": "unknown", "received_status": webhook_data.status},
                status_code=status.HTTP_200_OK
            )
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        db.rollback()
        return error_response(
            message="An error occurred while processing webhook",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/payment-status/{subscription_id}", status_code=status.HTTP_200_OK)
async def get_payment_status(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment status for a subscription (for frontend polling).
    Frontend can poll this endpoint to check if payment has been confirmed.
    """
    try:
        # Verify subscription belongs to user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.organization_id == organization.id
        ).first()
        
        if not subscription:
            return error_response(
                message="Subscription not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get the most recent payment for this subscription
        payment = db.query(Payment).filter(
            Payment.subscription_id == subscription_id
        ).order_by(Payment.created_at.desc()).first()
        
        if not payment:
            return error_response(
                message="No payment found for this subscription",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        response_data = PaymentStatusResponse(
            payment_id=payment.id,
            subscription_id=subscription.id,
            status=payment.status.value,
            provider_ref=payment.provider_ref,
            amount=float(payment.amount),
            currency=payment.currency,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
        
        return success_response(
            message="Payment status retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment status error: {str(e)}", exc_info=True)
        return error_response(
            message="An error occurred while retrieving payment status",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/status-by-transid/{trans_id}", status_code=status.HTTP_200_OK)
async def get_subscription_status_by_transid(
    trans_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get subscription and payment status by Fapshi transaction ID (transId).
    Useful for checking payment status after initiating a payment.
    """
    try:
        # Find payment by provider_ref (transId)
        payment = db.query(Payment).filter(
            Payment.provider_ref == trans_id,
            Payment.provider == PaymentProvider.FAPSHI
        ).first()
        
        if not payment:
            return error_response(
                message=f"Payment not found for transaction ID: {trans_id}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verify payment belongs to current user
        if payment.user_id != current_user.id:
            return error_response(
                message="You don't have permission to access this payment",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get subscription
        subscription = db.query(Subscription).filter(
            Subscription.id == payment.subscription_id
        ).first()
        
        if not subscription:
            return error_response(
                message="Subscription not found for this payment",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Determine plan name by matching payment amount to plan amount
        # This ensures we show the correct plan even if subscription was updated later
        all_plans = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True  # noqa: E712
        ).all()
        
        plan_name = None
        payment_amount = float(payment.amount)
        
        # Try to match payment amount to a plan amount
        for plan in all_plans:
            if float(plan.amount) == payment_amount:
                plan_name = plan.name
                break
        
        # Fallback: Get plan from subscription's current plan_id
        if not plan_name and subscription.plan_id:
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            if plan:
                plan_name = plan.name
        
        response_data = SubscriptionStatusByTransIdResponse(
            trans_id=trans_id,
            payment_id=payment.id,
            subscription_id=subscription.id,
            payment_status=payment.status.value,
            subscription_status=subscription.status.value,
            amount=float(payment.amount),
            currency=payment.currency,
            provider=payment.provider.value,
            plan_name=plan_name,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            payment_created_at=payment.created_at,
            payment_updated_at=payment.updated_at
        )
        
        return success_response(
            message="Subscription status retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscription status by transId error: {str(e)}", exc_info=True)
        return error_response(
            message="An error occurred while retrieving subscription status",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/payment-history", status_code=status.HTTP_200_OK)
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of payments to return"),
    offset: int = Query(0, ge=0, description="Number of payments to skip")
):
    """
    Get payment history for the current user's organization.
    Returns a list of all payments associated with the user's subscriptions.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get all subscriptions for the organization
        subscriptions = db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).all()
        
        if not subscriptions:
            # Return empty list if no subscriptions
            response_data = PaymentHistoryResponse(
                payments=[],
                total=0,
                limit=limit,
                offset=offset
            )
            return success_response(
                message="No payment history found",
                data=response_data.model_dump(),
                status_code=status.HTTP_200_OK
            )
        
        # Get subscription IDs
        subscription_ids = [sub.id for sub in subscriptions]
        
        # Query payments for these subscriptions
        payments_query = db.query(Payment).filter(
            Payment.subscription_id.in_(subscription_ids),
            Payment.user_id == current_user.id
        )
        
        # Get total count
        total = payments_query.count()
        
        # Get paginated payments, ordered by most recent first
        payments = payments_query.order_by(
            Payment.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Get all active plans to match payment amounts
        all_plans = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True  # noqa: E712
        ).all()
        
        # Create a map of amount -> plan name for quick lookup
        # Handle multiple plans with same amount by preferring exact match
        amount_to_plan = {}
        for plan in all_plans:
            amount_key = float(plan.amount)
            # If multiple plans have same amount, keep the first one (shouldn't happen, but just in case)
            if amount_key not in amount_to_plan:
                amount_to_plan[amount_key] = plan.name
        
        # Build response data
        payment_items = []
        for payment in payments:
            # Determine plan name by matching payment amount to plan amount
            # This ensures we show the correct plan even if subscription was updated later
            plan_name = None
            payment_amount = float(payment.amount)
            
            # Try to match payment amount to a plan amount
            if payment_amount in amount_to_plan:
                plan_name = amount_to_plan[payment_amount]
            else:
                # Fallback: Get plan from subscription's current plan_id
                subscription = next((s for s in subscriptions if s.id == payment.subscription_id), None)
                if subscription and subscription.plan_id:
                    plan = db.query(SubscriptionPlan).filter(
                        SubscriptionPlan.id == subscription.plan_id
                    ).first()
                    if plan:
                        plan_name = plan.name
            
            payment_items.append(
                PaymentHistoryItem(
                    payment_id=payment.id,
                    subscription_id=payment.subscription_id,
                    trans_id=payment.provider_ref,
                    amount=float(payment.amount),
                    currency=payment.currency,
                    status=payment.status.value,
                    provider=payment.provider.value,
                    plan_name=plan_name,
                    created_at=payment.created_at,
                    updated_at=payment.updated_at
                )
            )
        
        response_data = PaymentHistoryResponse(
            payments=payment_items,
            total=total,
            limit=limit,
            offset=offset
        )
        
        return success_response(
            message="Payment history retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment history error: {str(e)}", exc_info=True)
        return error_response(
            message="An error occurred while retrieving payment history",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/pending-payment", status_code=status.HTTP_200_OK)
async def get_pending_payment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent pending payment (status = INITIATED) for the current user.
    Returns the payment that is waiting for user confirmation or completion.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="Organization not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get all subscriptions for the organization
        subscriptions = db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).all()
        
        if not subscriptions:
            return error_response(
                message="No subscriptions found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get subscription IDs
        subscription_ids = [sub.id for sub in subscriptions]
        
        # Find the most recent pending payment (status = INITIATED) for this user
        pending_payment = db.query(Payment).filter(
            Payment.subscription_id.in_(subscription_ids),
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.INITIATED
        ).order_by(Payment.created_at.desc()).first()
        
        if not pending_payment:
            return error_response(
                message="No pending payment found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get subscription and plan details
        subscription = next((s for s in subscriptions if s.id == pending_payment.subscription_id), None)
        
        # Determine plan name by matching payment amount to plan amount
        all_plans = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True  # noqa: E712
        ).all()
        
        plan_name = None
        payment_amount = float(pending_payment.amount)
        
        # Try to match payment amount to a plan amount
        for plan in all_plans:
            if float(plan.amount) == payment_amount:
                plan_name = plan.name
                break
        
        # Fallback: Get plan from subscription's current plan_id
        if not plan_name and subscription and subscription.plan_id:
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            if plan:
                plan_name = plan.name
        
        response_data = PendingPaymentResponse(
            payment_id=pending_payment.id,
            subscription_id=pending_payment.subscription_id,
            trans_id=pending_payment.provider_ref,
            amount=float(pending_payment.amount),
            currency=pending_payment.currency,
            status=pending_payment.status.value,
            provider=pending_payment.provider.value,
            plan_name=plan_name,
            subscription_status=subscription.status.value if subscription else None,
            created_at=pending_payment.created_at,
            updated_at=pending_payment.updated_at
        )
        
        return success_response(
            message="Pending payment retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get pending payment error: {str(e)}", exc_info=True)
        return error_response(
            message="An error occurred while retrieving pending payment",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

