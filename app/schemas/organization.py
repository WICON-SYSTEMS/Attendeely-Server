from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateOrganizationRequest(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=100, description="Name of the organization")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry/sector the organization operates in")
    employees_count_range: str = Field(..., description="Employee count range (e.g., '1-10', '11-50', '51-200', '201-500', '500+')")
    country: str = Field(..., min_length=2, max_length=100, description="Country where the organization is based")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., 'USD', 'EUR', 'GBP')")
    plan: str = Field("Free Trial", description="Pricing plan (Free Trial, Basic, Pro, Enterprise)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_name": "Acme Corporation",
                "industry": "Technology",
                "employees_count_range": "51-200",
                "country": "United States",
                "currency": "USD",
                "plan": "Free Trial"
            }
        }


class OrganizationResponse(BaseModel):
    id: int
    organization_name: str
    organization_code: str
    logo_url: Optional[str] = None
    industry: str
    employees_count_range: str
    country: str
    currency: str
    plan: str
    admin_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UpdateOrganizationRequest(BaseModel):
    organization_name: Optional[str] = Field(None, min_length=2, max_length=100, description="New organization name")
    industry: Optional[str] = Field(None, min_length=2, max_length=100, description="New industry/sector")
    employees_count_range: Optional[str] = Field(None, description="New employee count range")
    country: Optional[str] = Field(None, min_length=2, max_length=100, description="New country")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="New currency code")
    plan: Optional[str] = Field(None, description="New pricing plan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_name": "Updated Company Name",
                "industry": "Finance",
                "employees_count_range": "201-500",
                "country": "United Kingdom",
                "currency": "GBP",
                "plan": "Pro"
            }
        }
