"""convert_employee_id_to_uuid

Revision ID: 31288ead6f36
Revises: 8b7deb91ef2a
Create Date: 2025-11-13 15:14:51.656573

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '31288ead6f36'
down_revision = '8b7deb91ef2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure UUID generation function is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # Add temporary UUID column with default generator
    op.add_column(
        'employees',
        sa.Column(
            'id_uuid',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        )
    )

    # Populate UUIDs for existing rows
    op.execute('UPDATE employees SET id_uuid = gen_random_uuid();')

    # Drop primary key and index on the old integer column
    op.drop_constraint('employees_pkey', 'employees', type_='primary')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')

    # Drop the old integer id column
    op.drop_column('employees', 'id')

    # Rename the UUID column to id
    op.alter_column('employees', 'id_uuid', new_column_name='id')

    # Recreate primary key and index on the new UUID column
    op.create_primary_key('employees_pkey', 'employees', ['id'])
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'])

    # Old integer sequence is no longer needed
    op.execute('DROP SEQUENCE IF EXISTS employees_id_seq;')


def downgrade() -> None:
    # Recreate integer sequence for ids
    op.execute('CREATE SEQUENCE IF NOT EXISTS employees_id_seq;')

    # Add temporary integer column
    op.add_column(
        'employees',
        sa.Column(
            'id_int',
            sa.Integer(),
            server_default=sa.text("nextval('employees_id_seq')"),
            nullable=False
        )
    )

    # Populate integers for existing rows
    op.execute("UPDATE employees SET id_int = nextval('employees_id_seq');")

    # Drop primary key and index on UUID column
    op.drop_constraint('employees_pkey', 'employees', type_='primary')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')

    # Drop UUID column and rename integer column back to id
    op.drop_column('employees', 'id')
    op.alter_column('employees', 'id_int', new_column_name='id')

    # Recreate primary key and index on integer column
    op.create_primary_key('employees_pkey', 'employees', ['id'])
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'])

    # Ensure the sequence owns the column for future inserts
    op.execute("ALTER SEQUENCE employees_id_seq OWNED BY employees.id;")
