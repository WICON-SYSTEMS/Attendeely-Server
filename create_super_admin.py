import getpass
from typing import Optional

from app.core.database import SessionLocal
from app.core.security import get_password_hash, validate_password
from app.models.user import User


def prompt_non_empty(prompt_text: str) -> str:
    value: Optional[str] = None
    while not value:
        value = input(prompt_text).strip()
        if not value:
            print("Value cannot be empty.")
    return value


def main() -> None:
    print("=== Attendeely Super Admin Setup ===")
    full_name = prompt_non_empty("Full name: ")
    email = prompt_non_empty("Email: ")

    # Password with validation
    while True:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Please try again.")
            continue

        is_valid, error_msg = validate_password(password)
        if not is_valid:
            print(f"Invalid password: {error_msg}")
            continue
        break

    db = SessionLocal()
    try:
        # Ensure only one super admin: demote any existing ones
        existing_super_admins = (
            db.query(User).filter(User.is_super_admin.is_(True)).all()
        )
        if existing_super_admins:
            print(f"Found {len(existing_super_admins)} existing super admin(s). Demoting them...")
            for u in existing_super_admins:
                u.is_super_admin = False
            db.commit()

        # If a user already exists with this email, upgrade that user to super admin
        existing_with_email = db.query(User).filter(User.email == email).first()

        hashed_password = get_password_hash(password)

        if existing_with_email:
            print(f"Updating existing user with email {email} to be the super admin.")
            existing_with_email.full_name = full_name
            existing_with_email.hashed_password = hashed_password
            existing_with_email.is_email_verified = True
            existing_with_email.is_active = True
            existing_with_email.is_super_admin = True
            super_admin = existing_with_email
        else:
            super_admin = User(
                full_name=full_name,
                email=email,
                hashed_password=hashed_password,
                is_email_verified=True,
                is_active=True,
                is_super_admin=True,
            )
            db.add(super_admin)

        db.commit()
        db.refresh(super_admin)

        print("\nSuper admin configured successfully:")
        print(f"  ID: {super_admin.id}")
        print(f"  Name: {super_admin.full_name}")
        print(f"  Email: {super_admin.email}")
        print("You can now login with these credentials and use all /api/v1/super-admin endpoints.")
    except Exception as e:
        db.rollback()
        print(f"Error while creating super admin: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()


