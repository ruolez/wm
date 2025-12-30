"""create account_sync_settings table

Revision ID: c3d4e5f6g7h8
Revises: a2e018dade94
Create Date: 2025-05-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6g7h8'
down_revision = 'a2e018dade94'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'account_sync_settings',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False, comment='PK'),
        sa.Column(
            'db_name', sa.String(length=50), nullable=False,
            comment='Which database this sync applies to'
        ),
        sa.Column(
            'source_user_id', sa.Integer(), nullable=False,
            comment='ID of the source user'
        ),
        sa.Column(
            'target_user_id', sa.Integer(), nullable=False,
            comment='Target user identifier (Employees_tbl.EmployeeID)'
        ),
        sa.Column(
            'target_username', sa.String(length=255), nullable=False,
            comment='FirstName from Employees_tbl'
        ),
        sa.Column(
            'sync_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0'),
            comment='Whether this account is enabled for sync'
        ),
        sa.Column(
            'created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(),
            comment='When this record was created'
        ),
        sa.Column(
            'updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now(),
            comment='When this record was last updated'
        ),
    )
    op.create_index(
        'ix_account_sync_source_target_db',
        'account_sync_settings',
        ['db_name', 'source_user_id', 'target_user_id'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_account_sync_source_target_db', table_name='account_sync_settings')
    op.drop_table('account_sync_settings')
