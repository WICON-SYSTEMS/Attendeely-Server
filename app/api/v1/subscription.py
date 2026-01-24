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
        
        # Get or create a test subscription
        subscription = db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        # If no subscription exists, create a minimal test one
        if not subscription:
            # Get the Free plan for testing
            free_plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.name == "Free"
            ).first()
            
            if not free_plan:
                return error_response(
                    message="Free plan not found. Please seed subscription plans first.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
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
            
            # Update subscription to keep it as pending or mark as failed
            subscription = db.query(Subscription).filter(
                Subscription.id == payment.subscription_id
            ).first()
            
            if subscription and subscription.status == SubscriptionStatus.PENDING:
                # Keep as pending, user can retry
                pass
            
            db.commit()
            db.refresh(payment)
            
            logger.warning(f"Payment failed: payment_id={payment.id}, transId={webhook_data.transId}, status_received='{webhook_data.status}'")
            
            return success_response(
                message="Payment status updated",
                data={
                    "payment_id": payment.id,
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

