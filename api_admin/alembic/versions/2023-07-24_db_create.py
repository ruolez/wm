"""DB create

Revision ID: a2e018dade94
Revises: 
Create Date: 2023-07-24 00:28:30.060061

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlalchemy_file

revision = "a2e018dade94"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "AdminDBs_admin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("TypeDB", sa.Enum("mssql", name="admindbstype"), nullable=False),
        sa.Column("Username", sa.String(), nullable=False),
        sa.Column("Password", sa.String(), nullable=False),
        sa.Column(
            "ipAddress",
            sqlalchemy_utils.types.ip_address.IPAddressType(length=50),
            nullable=True,
        ),
        sa.Column("ShareName", sa.String(), nullable=True),
        sa.Column("Port", sa.Integer(), nullable=False),
        sa.Column("NameDB", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "AdminUserProject_admin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("password", sa.String(length=100), nullable=True),
        sa.Column(
            "statususer",
            sa.Enum("admin", "regular_user", name="statususers"),
            nullable=True,
        ),
        sa.Column("activated", sa.Boolean(), nullable=True),
        sa.Column(
            "email", sqlalchemy_utils.types.email.EmailType(length=255), nullable=True
        ),
        sa.Column("avatar", sqlalchemy_file.types.ImageField(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "Article",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("Draft", "Published", "Withdrawn", name="status"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("Article")
    op.drop_table("AdminUserProject_admin")
    op.drop_table("AdminDBs_admin")
