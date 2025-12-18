from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SuperAdminOverviewStats(BaseModel):
    total_organizations: int
    active_organizations: int
    total_users: int
    total_employees: int
    total_feedback: int
    total_subscriptions: int
    active_subscriptions: int
    subscriptions_by_plan: dict


class SuperAdminOrganizationSummary(BaseModel):
    id: int
    organization_name: str
    organization_code: str
    country: str
    currency: str
    is_active: bool
    created_at: datetime
    admin_id: int
    admin_email: str
    employee_count: int
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None


class SuperAdminOrganizationListResponse(BaseModel):
    organizations: List[SuperAdminOrganizationSummary]
    total: int
    limit: int
    offset: int


class SuperAdminUserSummary(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    is_email_verified: bool
    is_super_admin: bool
    created_at: datetime
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None


class SuperAdminUserListResponse(BaseModel):
    users: List[SuperAdminUserSummary]
    total: int
    limit: int
    offset: int


class SuperAdminEmployeeSummary(BaseModel):
    id: str  # UUID as string
    full_name: str
    email: str
    department: str
    job_title: str
    role: str
    is_active: bool
    organization_id: int
    organization_name: str


class SuperAdminEmployeeListResponse(BaseModel):
    employees: List[SuperAdminEmployeeSummary]
    total: int
    limit: int
    offset: int


class SuperAdminSubscriptionSummary(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    plan: str
    status: str
    is_active: bool
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    monthly_price: Optional[float] = None


class SuperAdminSubscriptionListResponse(BaseModel):
    subscriptions: List[SuperAdminSubscriptionSummary]
    total: int
    limit: int
    offset: int


class SuperAdminToggleOrganizationStatusRequest(BaseModel):
    is_active: bool


