"""
Feature access definitions for subscription plans
"""
from app.models.subscription import SubscriptionPlan
from typing import Dict, Set
from datetime import datetime, timedelta


# Feature flags
class Feature:
    """Available features in the system"""
    BASIC_ATTENDANCE_TRACKING = "basic_attendance_tracking"
    ADVANCED_ATTENDANCE_TRACKING = "advanced_attendance_tracking"
    MONTHLY_PAYROLL_REPORTS = "monthly_payroll_reports"
    AUTOMATED_PAYROLL_PROCESSING = "automated_payroll_processing"
    QR_CODE_CHECK_INS = "qr_code_check_ins"
    GEOFENCING = "geofencing"
    PRIORITY_SUPPORT = "priority_support"
    EMAIL_SUPPORT = "email_support"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    API_ACCESS = "api_access"
    DEDICATED_ACCOUNT_MANAGER = "dedicated_account_manager"
    PHONE_SUPPORT = "phone_support"
    ADVANCED_ANALYTICS = "advanced_analytics"


# Plan features mapping
PLAN_FEATURES: Dict[SubscriptionPlan, Set[str]] = {
    SubscriptionPlan.FREE: {
        Feature.BASIC_ATTENDANCE_TRACKING,
        Feature.MONTHLY_PAYROLL_REPORTS,
        Feature.EMAIL_SUPPORT,
    },
    SubscriptionPlan.STANDARD: {
        Feature.BASIC_ATTENDANCE_TRACKING,
        Feature.ADVANCED_ATTENDANCE_TRACKING,
        Feature.AUTOMATED_PAYROLL_PROCESSING,
        Feature.QR_CODE_CHECK_INS,
        Feature.GEOFENCING,
        Feature.PRIORITY_SUPPORT,
        Feature.EMAIL_SUPPORT,
    },
    SubscriptionPlan.ENTERPRISE: {
        Feature.BASIC_ATTENDANCE_TRACKING,
        Feature.ADVANCED_ATTENDANCE_TRACKING,
        Feature.AUTOMATED_PAYROLL_PROCESSING,
        Feature.QR_CODE_CHECK_INS,
        Feature.GEOFENCING,
        Feature.PRIORITY_SUPPORT,
        Feature.EMAIL_SUPPORT,
        Feature.CUSTOM_INTEGRATIONS,
        Feature.API_ACCESS,
        Feature.DEDICATED_ACCOUNT_MANAGER,
        Feature.PHONE_SUPPORT,
        Feature.ADVANCED_ANALYTICS,
    },
}

# Employee limits per plan
EMPLOYEE_LIMITS: Dict[SubscriptionPlan, int] = {
    SubscriptionPlan.FREE: 10,
    SubscriptionPlan.STANDARD: 100,
    SubscriptionPlan.ENTERPRISE: -1,  # -1 means unlimited
}

# Trial period in days
TRIAL_PERIOD_DAYS = 7


def get_plan_features(plan: SubscriptionPlan) -> Set[str]:
    """Get features available for a given plan"""
    return PLAN_FEATURES.get(plan, set())


def has_feature(plan: SubscriptionPlan, feature: str) -> bool:
    """Check if a plan has access to a specific feature"""
    features = get_plan_features(plan)
    return feature in features


def get_employee_limit(plan: SubscriptionPlan) -> int:
    """Get the employee limit for a given plan"""
    return EMPLOYEE_LIMITS.get(plan, 0)


def is_within_employee_limit(plan: SubscriptionPlan, current_count: int) -> bool:
    """Check if current employee count is within plan limit"""
    limit = get_employee_limit(plan)
    if limit == -1:  # Unlimited
        return True
    return current_count < limit


def calculate_trial_end_date(start_date: datetime) -> datetime:
    """Calculate trial end date from start date"""
    return start_date + timedelta(days=TRIAL_PERIOD_DAYS)


def is_trial_active(trial_end_date: datetime) -> bool:
    """Check if trial is still active"""
    return datetime.utcnow() < trial_end_date


def is_subscription_active(subscription_end_date: datetime) -> bool:
    """Check if subscription is still active"""
    return datetime.utcnow() < subscription_end_date

