"""add_payment_integration_tables

Revision ID: f1a2b3c4d5e6
Revises: b8c460b3ccf2
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'b8c460b3ccf2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Update subscriptionstatus enum to include 'pending' and 'past_due'
    # Check if enum exists and add new values
    status_enum_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus'")
    ).fetchone()
    
    if status_enum_exists:
        # Add new enum values if they don't exist
        try:
            op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'pending'")
        except Exception:
            pass  # Value might already exist
        try:
            op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'past_due'")
        except Exception:
            pass  # Value might already exist
    
    # Create paymentstatus enum (use IF NOT EXISTS to avoid errors if it already exists)
    payment_status_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'paymentstatus'")
    ).fetchone()
    if not payment_status_exists:
        op.execute("CREATE TYPE paymentstatus AS ENUM ('initiated', 'success', 'failed')")
    else:
        # Enum exists, make sure it has the right values (PostgreSQL doesn't support IF NOT EXISTS for enum values)
        pass
    
    # Create paymentprovider enum (use IF NOT EXISTS to avoid errors if it already exists)
    payment_provider_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'paymentprovider'")
    ).fetchone()
    if not payment_provider_exists:
        op.execute("CREATE TYPE paymentprovider AS ENUM ('fapshi')")
    else:
        # Enum exists
        pass
    
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='XAF'),
        sa.Column('interval', sa.String(length=20), nullable=False, server_default='monthly'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_subscription_plans_id', 'subscription_plans', ['id'], unique=False)
    op.create_index('ix_subscription_plans_name', 'subscription_plans', ['name'], unique=True)
    op.create_index('ix_subscription_plans_is_active', 'subscription_plans', ['is_active'], unique=False)
    
    # Add new columns to subscriptions table
    op.add_column('subscriptions', sa.Column('plan_id', sa.Integer(), nullable=True))
    op.add_column('subscriptions', sa.Column('start_date', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('next_billing_date', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('last_paid_date', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('grace_ends_at', sa.DateTime(), nullable=True))
    
    # Create foreign key for plan_id
    op.create_foreign_key(
        'fk_subscriptions_plan_id',
        'subscriptions', 'subscription_plans',
        ['plan_id'], ['id']
    )
    
    # Create indexes for new subscription columns
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'], unique=False)
    op.create_index('ix_subscriptions_start_date', 'subscriptions', ['start_date'], unique=False)
    op.create_index('ix_subscriptions_next_billing_date', 'subscriptions', ['next_billing_date'], unique=False)
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'], unique=False)
    op.create_index('ix_subscriptions_is_active', 'subscriptions', ['is_active'], unique=False)
    
    # Make plan column nullable (since we're adding plan_id)
    op.alter_column('subscriptions', 'plan', nullable=True)
    
    # Create payments table
    # Use postgresql.ENUM with create_type=False since we already created the types manually
    payment_status_enum = postgresql.ENUM('initiated', 'success', 'failed', name='paymentstatus', create_type=False)
    payment_provider_enum = postgresql.ENUM('fapshi', name='paymentprovider', create_type=False)
    
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='XAF'),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column('provider', payment_provider_enum, nullable=False),
        sa.Column('provider_ref', sa.String(length=255), nullable=True),
        sa.Column('provider_response', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_ref')
    )
    op.create_index('ix_payments_id', 'payments', ['id'], unique=False)
    op.create_index('ix_payments_user_id', 'payments', ['user_id'], unique=False)
    op.create_index('ix_payments_subscription_id', 'payments', ['subscription_id'], unique=False)
    op.create_index('ix_payments_status', 'payments', ['status'], unique=False)
    op.create_index('ix_payments_provider', 'payments', ['provider'], unique=False)
    op.create_index('ix_payments_provider_ref', 'payments', ['provider_ref'], unique=True)
    op.create_index('ix_payments_created_at', 'payments', ['created_at'], unique=False)
    op.create_index('ix_payments_user_subscription', 'payments', ['user_id', 'subscription_id'], unique=False)
    op.create_index('ix_payments_status_created', 'payments', ['status', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop payments table
    op.drop_index('ix_payments_status_created', table_name='payments')
    op.drop_index('ix_payments_user_subscription', table_name='payments')
    op.drop_index('ix_payments_created_at', table_name='payments')
    op.drop_index('ix_payments_provider_ref', table_name='payments')
    op.drop_index('ix_payments_provider', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_subscription_id', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_id', table_name='payments')
    op.drop_table('payments')
    
    # Remove columns from subscriptions table
    op.drop_index('ix_subscriptions_is_active', table_name='subscriptions')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_next_billing_date', table_name='subscriptions')
    op.drop_index('ix_subscriptions_start_date', table_name='subscriptions')
    op.drop_index('ix_subscriptions_plan_id', table_name='subscriptions')
    op.drop_constraint('fk_subscriptions_plan_id', 'subscriptions', type_='foreignkey')
    op.drop_column('subscriptions', 'grace_ends_at')
    op.drop_column('subscriptions', 'last_paid_date')
    op.drop_column('subscriptions', 'next_billing_date')
    op.drop_column('subscriptions', 'start_date')
    op.drop_column('subscriptions', 'plan_id')
    op.alter_column('subscriptions', 'plan', nullable=False)
    
    # Drop subscription_plans table
    op.drop_index('ix_subscription_plans_is_active', table_name='subscription_plans')
    op.drop_index('ix_subscription_plans_name', table_name='subscription_plans')
    op.drop_index('ix_subscription_plans_id', table_name='subscription_plans')
    op.drop_table('subscription_plans')
    
    # Note: We don't drop the enum types here as they might be used elsewhere
    # If you need to drop them, do it manually:
    # DROP TYPE IF EXISTS paymentstatus;
    # DROP TYPE IF EXISTS paymentprovider;
    # Note: Cannot easily remove enum values, so 'pending' and 'past_due' will remain in subscriptionstatus
