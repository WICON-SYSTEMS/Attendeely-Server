import secrets
import hashlib
from sqlalchemy.orm import Session
from typing import Union


def generate_organization_code(db: Session, length: int = 8) -> str:
    """
    Generate a unique organization code.
    
    Format: 8-character uppercase alphanumeric string
    Excludes ambiguous characters: 0, O, I, 1, L
    Example: A7K9X2M4, B3N8Q5P1, C4R7T2W9
    
    Args:
        db: Database session for checking uniqueness
        length: Length of the code (default: 8)
        
    Returns:
        str: Unique organization code
    """
    # Character set excluding ambiguous characters (0, O, I, 1, L)
    # This gives us 31 characters (23 letters + 8 digits)
    charset = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    
    max_attempts = 10
    for _ in range(max_attempts):
        # Generate random code using cryptographically secure random
        code = ''.join(secrets.choice(charset) for _ in range(length))
        
        # Check if code already exists in database
        from app.models.organization import Organization
        existing = db.query(Organization).filter(
            Organization.organization_code == code
        ).first()
        
        if not existing:
            return code
    
    # If we couldn't generate a unique code after max_attempts, raise an error
    raise ValueError("Failed to generate unique organization code after multiple attempts")


def generate_employee_code(db: Session, organization_id: int, length: int = 8) -> str:
    """
    Generate a unique employee code within an organization.
    
    Format: 8-character uppercase alphanumeric string
    Excludes ambiguous characters: 0, O, I, 1, L
    Example: EMP001, EMP002, etc.
    
    Args:
        db: Database session for checking uniqueness
        organization_id: ID of the organization
        length: Length of the code (default: 8)
        
    Returns:
        str: Unique employee code
    """
    from app.models.employee import Employee
    
    # Character set excluding ambiguous characters (0, O, I, 1, L)
    charset = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    
    max_attempts = 20
    for _ in range(max_attempts):
        # Generate random code using cryptographically secure random
        code = ''.join(secrets.choice(charset) for _ in range(length))
        
        # Check if code already exists in database for this organization
        existing = db.query(Employee).filter(
            Employee.employee_code == code,
            Employee.organization_id == organization_id
        ).first()
        
        if not existing:
            return code
    
    # If we couldn't generate a unique code after max_attempts, raise an error
    raise ValueError("Failed to generate unique employee code after multiple attempts")


def generate_qr_code(employee_id: Union[int, str], employee_code: str, organization_id: int) -> str:
    """
    Generate a unique QR code identifier for an employee.
    
    This code will be used to generate QR images on the frontend and
    when scanned, will identify the employee it belongs to.
    
    Format: SHA256 hash of employee data (64 characters)
    
    Args:
        employee_id: Employee ID
        employee_code: Employee code
        organization_id: Organization ID
        
    Returns:
        str: Unique QR code string
    """
    # Create a unique string combining employee data
    unique_string = f"{organization_id}_{str(employee_id)}_{employee_code}_{secrets.token_hex(16)}"
    
    # Generate SHA256 hash
    qr_code = hashlib.sha256(unique_string.encode()).hexdigest()
    
    return qr_code
