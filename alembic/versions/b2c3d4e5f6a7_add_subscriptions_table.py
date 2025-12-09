"""add_subscriptions_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-01 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Check if enum types exist, create only if they don't
    plan_enum_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'subscriptionplan'")
    ).fetchone()
    if not plan_enum_exists:
        op.execute("CREATE TYPE subscriptionplan AS ENUM ('Free', 'Standard', 'Enterprise')")
    
    status_enum_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus'")
    ).fetchone()
    if not status_enum_exists:
        op.execute("CREATE TYPE subscriptionstatus AS ENUM ('active', 'trial', 'expired', 'cancelled')")
    
    # Check if table exists
    table_exists = connection.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'subscriptions'")
    ).fetchone()
    
    if not table_exists:
        # Create table using raw SQL to avoid enum creation issues
        op.execute("""
            CREATE TABLE subscriptions (
                id SERIAL PRIMARY KEY,
                organization_id INTEGER NOT NULL UNIQUE,
                plan subscriptionplan NOT NULL,
                status subscriptionstatus NOT NULL,
                trial_start_date TIMESTAMP,
                trial_end_date TIMESTAMP,
                subscription_start_date TIMESTAMP,
                subscription_end_date TIMESTAMP,
                monthly_price NUMERIC(10, 2),
                is_active BOOLEAN,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                CONSTRAINT fk_subscriptions_organization 
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
            )
        """)
        
        # Create indexes
        op.create_index('ix_subscriptions_organization_id', 'subscriptions', ['organization_id'], unique=True)
        op.create_index('ix_subscriptions_id', 'subscriptions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_organization_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    
    # Note: We don't drop the enum types here as they might be used elsewhere
    # If you need to drop them, do it manually:
    # DROP TYPE IF EXISTS subscriptionplan;
    # DROP TYPE IF EXISTS subscriptionstatus;
