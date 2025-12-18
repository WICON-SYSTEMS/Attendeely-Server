"""add_is_super_admin_to_users

Revision ID: b8c460b3ccf2
Revises: b2c3d4e5f6a7
Create Date: 2025-12-18 10:04:15.441013

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c460b3ccf2'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    # Optional: drop the server_default so future inserts rely on ORM/defaults
    op.alter_column('users', 'is_super_admin', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'is_super_admin')
