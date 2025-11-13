from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, validate_password, create_access_token, verify_password
from app.schemas.auth import (
    SignupRequest, SignupResponse, 
    VerifyOTPRequest, VerifyOTPResponse,
    ResendOTPRequest,
    LoginRequest, LoginResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
    AdminProfileResponse
)
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.otp import OTP
from app.models.organization import Organization
from app.core.dependencies import get_current_user
from app.services.email_service import EmailService
from app.utils.otp import generate_otp
from datetime import timedelta, datetime
import logging
import secrets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create admin account with email and password.
    Sends a 6-digit OTP to the provided email for verification.
    
    Password Requirements:
    - At least 8 characters
    - One lowercase letter
    - One uppercase letter
    - One number
    - One special character
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            return error_response(
                message="Email already registered",
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Validate password
        is_valid, error_msg = validate_password(request.password)
        if not is_valid:
            return error_response(
                message=error_msg,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        hashed_password = get_password_hash(request.password)
        new_user = User(
            full_name=request.full_name,
            email=request.email,
            hashed_password=hashed_password,
            is_email_verified=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate OTP
        otp_code = generate_otp()
        otp = OTP(
            user_id=new_user.id,
            otp_code=otp_code,
            expires_at=OTP.create_expiry_time()
        )
        db.add(otp)
        db.commit()
        
        # Send OTP email
        email_sent = await EmailService.send_otp_email(request.email, otp_code)
        print(otp_code)
        if not email_sent:
            logger.warning(f"Failed to send OTP email to {request.email}")
            # Don't fail the request, user can resend OTP
        
        # Prepare response
        response_data = SignupResponse(
            user_id=new_user.id,
            full_name=new_user.full_name,
            email=new_user.email,
            is_email_verified=new_user.is_email_verified,
            created_at=new_user.created_at
        )
        
        return success_response(
            message="Account created successfully. Please check your email for the OTP code.",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred during signup. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify email with OTP code.
    Returns access token upon successful verification.
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return error_response(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already verified
        if user.is_email_verified:
            return error_response(
                message="Email already verified",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Find valid OTP
        otp = db.query(OTP).filter(
            OTP.user_id == user.id,
            OTP.otp_code == request.otp_code,
            OTP.is_used == False
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp:
            return error_response(
                message="Invalid OTP code",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if OTP is expired
        if otp.is_expired():
            return error_response(
                message="OTP code has expired. Please request a new one.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark OTP as used
        otp.is_used = True
        
        # Mark user as verified
        user.is_email_verified = True
        
        db.commit()
        db.refresh(user)
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Prepare response
        response_data = VerifyOTPResponse(
            user_id=user.id,
            email=user.email,
            is_email_verified=user.is_email_verified,
            access_token=access_token,
            token_type="bearer"
        )
        
        return success_response(
            message="Email verified successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred during verification. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(request: ResendOTPRequest, db: Session = Depends(get_db)):
    """
    Resend OTP code to user's email.
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return error_response(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already verified
        if user.is_email_verified:
            return error_response(
                message="Email already verified",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Invalidate old OTPs
        db.query(OTP).filter(
            OTP.user_id == user.id,
            OTP.is_used == False
        ).update({"is_used": True})
        
        # Generate new OTP
        otp_code = generate_otp()
        otp = OTP(
            user_id=user.id,
            otp_code=otp_code,
            expires_at=OTP.create_expiry_time()
        )
        db.add(otp)
        db.commit()
        
        # Send OTP email
        email_sent = await EmailService.send_otp_email(request.email, otp_code)
        if not email_sent:
            return error_response(
                message="Failed to send OTP email. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return success_response(
            message="OTP code sent successfully. Please check your email.",
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Resend OTP error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while resending OTP. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns access token and user information.
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return error_response(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not verify_password(request.password, user.hashed_password):
            return error_response(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is active
        if not user.is_active:
            return error_response(
                message="Account is deactivated. Please contact support.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if email is verified
        if not user.is_email_verified:
            return error_response(
                message="Email not verified. Please verify your email first.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Prepare response
        response_data = LoginResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_email_verified=user.is_email_verified,
            access_token=access_token,
            token_type="bearer"
        )
        
        return success_response(
            message="Login successful",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return error_response(
            message="An error occurred during login. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset - sends reset link to email"""
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            # Don't reveal if email exists
            return success_response(
                message="If the email exists, a password reset link has been sent.",
                status_code=status.HTTP_200_OK
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # Send reset email
        email_sent = await EmailService.send_password_reset_email(user.email, reset_token)
        
        if not email_sent:
            logger.warning(f"Failed to send password reset email to {user.email}")
        
        return success_response(
            message="If the email exists, a password reset link has been sent.",
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return error_response(
            message="An error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token from email"""
    try:
        user = db.query(User).filter(User.reset_token == request.token).first()
        
        if not user:
            return error_response(
                message="Invalid or expired reset token.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is expired
        if user.reset_token_expiry < datetime.utcnow():
            return error_response(
                message="Reset token has expired. Please request a new one.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password
        is_valid, validation_message = validate_password(request.new_password)
        if not is_valid:
            return error_response(
                message=validation_message,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
        
        return success_response(
            message="Password reset successful. You can now login with your new password.",
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/profile", status_code=status.HTTP_200_OK)
async def get_admin_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin profile with organization details"""
    try:
        # Get organization if exists
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        # Prepare organization data
        org_data = None
        has_organization = False
        
        if organization:
            has_organization = True
            org_data = {
                'id': organization.id,
                'organization_name': organization.organization_name,
                'organization_code': organization.organization_code,
                'logo_url': organization.logo_url,
                'industry': organization.industry,
                'employees_count_range': organization.employees_count_range,
                'country': organization.country,
                'currency': organization.currency,
                'plan': organization.plan,
                'is_active': organization.is_active,
                'created_at': organization.created_at.isoformat()
            }
        
        # Prepare profile response
        profile_data = {
            'user_id': current_user.id,
            'full_name': current_user.full_name,
            'email': current_user.email,
            'is_email_verified': current_user.is_email_verified,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at,
            'has_organization': has_organization,
            'organization': org_data
        }
        
        return success_response(
            message="Profile retrieved successfully",
            data=profile_data,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving profile.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
