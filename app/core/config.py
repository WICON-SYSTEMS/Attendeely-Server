from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Attendeely"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMPLOYEE_TOKEN_EXPIRE_DAYS: int = 90  # 90 days for persistent mobile login
    
    # Email (Resend)
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    RESEND_FROM_NAME: str = "Attendeely"
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    
    # Payment (Fapshi)
    API_USER: Optional[str] = None  # Fapshi API user (required for payment functionality)
    API_KEY: Optional[str] = None  # Fapshi API key (required for payment functionality)
    FAPSHI_ENV: str = "sandbox"  # Fapshi environment: "sandbox" or "production" (default: production)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env file
    )


settings = Settings()
