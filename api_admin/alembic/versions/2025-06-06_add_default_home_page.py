"""add default_home_page to AdminUserProject_admin

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-06-06 17:51:05.245032

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'AdminUserProject_admin',
        sa.Column(
            'default_home_page',
            sa.String(length=255),
            nullable=True,
            comment='Default Home Page for user, UTF8 string, nullable'
        )
    )


def downgrade() -> None:
    op.drop_column('AdminUserProject_admin', 'default_home_page')