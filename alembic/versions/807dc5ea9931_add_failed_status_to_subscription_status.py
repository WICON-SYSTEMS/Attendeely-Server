"""add_failed_status_to_subscription_status

Revision ID: 807dc5ea9931
Revises: f1a2b3c4d5e6
Create Date: 2026-01-26 02:59:53.354694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '807dc5ea9931'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'failed' value to subscriptionstatus enum
    connection = op.get_bind()
    
    # Check if enum exists
    status_enum_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus'")
    ).fetchone()
    
    if status_enum_exists:
        # Add 'failed' value if it doesn't exist
        try:
            op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'failed'")
        except Exception as e:
            # Value might already exist or there might be a transaction issue
            # PostgreSQL doesn't support IF NOT EXISTS in all versions, so we catch the exception
            # If the value already exists, that's fine
            pass


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # To remove 'failed' status, you would need to:
    # 1. Update all subscriptions with 'failed' status to another status (e.g., 'expired')
    # 2. Recreate the enum type without 'failed'
    # This is complex and not recommended, so we leave it as is
    pass
