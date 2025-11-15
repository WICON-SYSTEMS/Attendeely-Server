from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.organization import (
    CreateOrganizationRequest,
    OrganizationResponse,
    UpdateOrganizationRequest,
    SetGeofenceRequest
)
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.organization import Organization
from app.services.cloudinary_service import CloudinaryService
from app.services.email_service import EmailService
from app.utils.generators import generate_organization_code
from typing import Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organization", tags=["Organization"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_name: str = Form(..., min_length=2, max_length=100, description="Name of the organization"),
    industry: str = Form(..., min_length=2, max_length=100, description="Industry/sector (e.g., Technology, Healthcare, Finance)"),
    employees_count_range: str = Form(..., description="Employee count range (e.g., '1-10', '11-50', '51-200', '201-500', '500+')"),
    country: str = Form(..., min_length=2, max_length=100, description="Country where organization is based"),
    currency: str = Form(..., min_length=3, max_length=3, description="Currency code (e.g., USD, EUR, GBP)"),
    plan: str = Form("Free Trial", description="Pricing plan (Free Trial, Basic, Pro, Enterprise)"),
    logo: UploadFile = File(None, description="Company logo image (JPEG, PNG, WEBP - Max 5MB)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization.
    Admin user must be verified to create an organization.
    
    Args:
        organization_name: Name of the organization
        industry: Industry/sector the organization operates in
        employees_count_range: Employee count range
        country: Country where organization is based
        currency: Currency code (3 letters)
        plan: Pricing plan (Free Trial, Basic, Pro, Enterprise)
        logo: Optional company logo image file
        current_user: Current authenticated user (from JWT)
        db: Database session
    
    Returns:
        Organization details with auto-generated organization code
    """
    try:
        # Check if user already has an organization
        existing_org = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if existing_org:
            return error_response(
                message="You already have an organization. Each admin can only create one organization.",
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Generate unique organization code
        organization_code = generate_organization_code(db)
        
        # Create organization (without logo first)
        new_organization = Organization(
            organization_name=organization_name,
            organization_code=organization_code,
            industry=industry,
            employees_count_range=employees_count_range,
            country=country,
            currency=currency.upper(),  # Ensure currency is uppercase
            plan=plan,
            admin_id=current_user.id,
            logo_url=None
        )
        db.add(new_organization)
        db.commit()
        db.refresh(new_organization)
        
        # Upload logo if provided
        logo_url = None
        if logo:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if logo.content_type not in allowed_types:
                # Rollback organization creation
                db.delete(new_organization)
                db.commit()
                return error_response(
                    message="Invalid file type. Only JPEG, PNG, and WEBP images are allowed.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 5MB)
            contents = await logo.read()
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                # Rollback organization creation
                db.delete(new_organization)
                db.commit()
                return error_response(
                    message="File size too large. Maximum size is 5MB.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload to Cloudinary
            logo_url = await CloudinaryService.upload_logo(
                contents,
                logo.filename,
                new_organization.id
            )
            
            if logo_url:
                new_organization.logo_url = logo_url
                db.commit()
                db.refresh(new_organization)
            else:
                logger.warning(f"Failed to upload logo for organization {new_organization.id}")
        
        # Send welcome email with organization details
        organization_data = {
            'organization_name': new_organization.organization_name,
            'organization_code': new_organization.organization_code,
            'industry': new_organization.industry,
            'employees_count_range': new_organization.employees_count_range,
            'country': new_organization.country,
            'currency': new_organization.currency,
            'plan': new_organization.plan
        }
        email_sent = await EmailService.send_welcome_email(
            current_user.email,
            organization_data
        )
        if not email_sent:
            logger.warning(f"Failed to send welcome email to {current_user.email}")
        
        # Prepare response
        response_data = OrganizationResponse(
            id=new_organization.id,
            organization_name=new_organization.organization_name,
            organization_code=new_organization.organization_code,
            logo_url=new_organization.logo_url,
            industry=new_organization.industry,
            employees_count_range=new_organization.employees_count_range,
            country=new_organization.country,
            currency=new_organization.currency,
            plan=new_organization.plan,
            admin_id=new_organization.admin_id,
            geofence_latitude=float(new_organization.geofence_latitude) if new_organization.geofence_latitude else None,
            geofence_longitude=float(new_organization.geofence_longitude) if new_organization.geofence_longitude else None,
            geofence_radius=float(new_organization.geofence_radius) if new_organization.geofence_radius else None,
            is_active=new_organization.is_active,
            created_at=new_organization.created_at
        )
        
        return success_response(
            message="Organization created successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        
    except ValueError as e:
        logger.error(f"Organization creation error: {str(e)}")
        db.rollback()
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Organization creation error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while creating the organization. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the organization of the current authenticated user.
    """
    try:
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        response_data = OrganizationResponse(
            id=organization.id,
            organization_name=organization.organization_name,
            organization_code=organization.organization_code,
            logo_url=organization.logo_url,
            industry=organization.industry,
            employees_count_range=organization.employees_count_range,
            country=organization.country,
            currency=organization.currency,
            plan=organization.plan,
            admin_id=organization.admin_id,
            geofence_latitude=float(organization.geofence_latitude) if organization.geofence_latitude else None,
            geofence_longitude=float(organization.geofence_longitude) if organization.geofence_longitude else None,
            geofence_radius=float(organization.geofence_radius) if organization.geofence_radius else None,
            is_active=organization.is_active,
            created_at=organization.created_at
        )
        
        return success_response(
            message="Organization retrieved successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Get organization error: {str(e)}")
        return error_response(
            message="An error occurred while retrieving the organization.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/update", status_code=status.HTTP_200_OK)
async def update_organization(
    organization_name: Optional[str] = Form(None, min_length=2, max_length=100, description="New organization name (optional)"),
    industry: Optional[str] = Form(None, min_length=2, max_length=100, description="New industry/sector (optional)"),
    employees_count_range: Optional[str] = Form(None, description="New employee count range (optional)"),
    country: Optional[str] = Form(None, min_length=2, max_length=100, description="New country (optional)"),
    currency: Optional[str] = Form(None, min_length=3, max_length=3, description="New currency code (optional)"),
    plan: Optional[str] = Form(None, description="New pricing plan (optional)"),
    logo: UploadFile = File(None, description="New company logo image (JPEG, PNG, WEBP - Max 5MB, optional)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update organization details.
    Can update name, industry, employee count range, country, currency, plan, and/or logo.
    """
    try:
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Update organization fields if provided
        if organization_name:
            organization.organization_name = organization_name
        if industry:
            organization.industry = industry
        if employees_count_range:
            organization.employees_count_range = employees_count_range
        if country:
            organization.country = country
        if currency:
            organization.currency = currency.upper()
        if plan:
            organization.plan = plan
        
        # Update logo if provided
        if logo:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if logo.content_type not in allowed_types:
                return error_response(
                    message="Invalid file type. Only JPEG, PNG, and WEBP images are allowed.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size (max 5MB)
            contents = await logo.read()
            if len(contents) > 5 * 1024 * 1024:  # 5MB
                return error_response(
                    message="File size too large. Maximum size is 5MB.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete old logo if exists
            if organization.logo_url:
                await CloudinaryService.delete_logo(organization.logo_url)
            
            # Upload new logo
            logo_url = await CloudinaryService.upload_logo(
                contents,
                logo.filename,
                organization.id
            )
            
            if logo_url:
                organization.logo_url = logo_url
            else:
                logger.warning(f"Failed to upload logo for organization {organization.id}")
                return error_response(
                    message="Failed to upload logo. Please try again.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        db.commit()
        db.refresh(organization)
        
        # Prepare response
        response_data = OrganizationResponse(
            id=organization.id,
            organization_name=organization.organization_name,
            organization_code=organization.organization_code,
            logo_url=organization.logo_url,
            industry=organization.industry,
            employees_count_range=organization.employees_count_range,
            country=organization.country,
            currency=organization.currency,
            plan=organization.plan,
            admin_id=organization.admin_id,
            geofence_latitude=float(organization.geofence_latitude) if organization.geofence_latitude else None,
            geofence_longitude=float(organization.geofence_longitude) if organization.geofence_longitude else None,
            geofence_radius=float(organization.geofence_radius) if organization.geofence_radius else None,
            is_active=organization.is_active,
            created_at=organization.created_at
        )
        
        return success_response(
            message="Organization updated successfully",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Update organization error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while updating the organization.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/set-geofence", status_code=status.HTTP_200_OK)
async def set_geofence(
    request: SetGeofenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set geofence coordinates for the organization.
    Uses the admin's current device location and sets a 20m radius.
    """
    try:
        # Get user's organization
        organization = db.query(Organization).filter(
            Organization.admin_id == current_user.id
        ).first()
        
        if not organization:
            return error_response(
                message="No organization found. Please create an organization first.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate latitude and longitude
        if not (-90 <= request.latitude <= 90):
            return error_response(
                message="Invalid latitude. Must be between -90 and 90.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if not (-180 <= request.longitude <= 180):
            return error_response(
                message="Invalid longitude. Must be between -180 and 180.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Set geofence with 20m radius
        organization.geofence_latitude = Decimal(str(request.latitude))
        organization.geofence_longitude = Decimal(str(request.longitude))
        organization.geofence_radius = Decimal("20.00")  # 20 meters
        
        db.commit()
        db.refresh(organization)
        
        # Prepare response
        response_data = OrganizationResponse(
            id=organization.id,
            organization_name=organization.organization_name,
            organization_code=organization.organization_code,
            logo_url=organization.logo_url,
            industry=organization.industry,
            employees_count_range=organization.employees_count_range,
            country=organization.country,
            currency=organization.currency,
            plan=organization.plan,
            admin_id=organization.admin_id,
            geofence_latitude=float(organization.geofence_latitude),
            geofence_longitude=float(organization.geofence_longitude),
            geofence_radius=float(organization.geofence_radius),
            is_active=organization.is_active,
            created_at=organization.created_at
        )
        
        return success_response(
            message="Geofence set successfully with 20m radius",
            data=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Set geofence error: {str(e)}")
        db.rollback()
        return error_response(
            message="An error occurred while setting the geofence.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
