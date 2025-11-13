from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the admin")
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "admin@company.com",
                "password": "SecurePass123!"
            }
        }


class SignupResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    is_email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@company.com",
                "otp_code": "123456"
            }
        }


class VerifyOTPResponse(BaseModel):
    user_id: int
    email: str
    is_email_verified: bool
    access_token: str
    token_type: str = "bearer"


class ResendOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@company.com"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@company.com",
                "password": "SecurePass123!"
            }
        }


class LoginResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    is_email_verified: bool
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@company.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456...",
                "new_password": "NewSecurePass123!"
            }
        }


class AdminProfileResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    is_email_verified: bool
    is_active: bool
    created_at: datetime
    has_organization: bool
    organization: Optional[dict] = None
    
    class Config:
        from_attributes = True
