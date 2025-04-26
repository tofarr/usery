"""Update user id to UUID

Revision ID: 99d055ab6fed
Revises: 684550666953
Create Date: 2025-04-26 19:34:39.994524

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '99d055ab6fed'
down_revision = '684550666953'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For SQLite, we need to recreate the table with the new UUID column
    # Drop existing tables if they exist
    op.execute("DROP TABLE IF EXISTS users_new")
    
    # Create a new temporary table with UUID as primary key
    op.create_table('users_new',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Copy data from the old table to the new table, generating UUIDs for each row
    op.execute(
        """
        INSERT INTO users_new (id, email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
        SELECT hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || substr(hex(randomblob(2)), 2) || '-' ||
               substr('89ab', 1 + (abs(random()) % 4), 1) || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)),
               email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at
        FROM users
        """
    )
    
    # Create indexes on the new table
    op.execute("CREATE UNIQUE INDEX ix_users_new_email ON users_new (email)")
    op.execute("CREATE INDEX ix_users_new_id ON users_new (id)")
    op.execute("CREATE UNIQUE INDEX ix_users_new_username ON users_new (username)")
    
    # Drop the old table
    op.drop_table('users')
    
    # Rename the new table to the original name
    op.rename_table('users_new', 'users')


def downgrade() -> None:
    # For SQLite, we need to recreate the table with the integer column
    # Drop existing tables if they exist
    op.execute("DROP TABLE IF EXISTS users_new")
    
    # Create a new temporary table with integer as primary key
    op.create_table('users_new',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Copy data from the old table to the new table, generating sequential IDs
    op.execute(
        """
        INSERT INTO users_new (email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
        SELECT email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at
        FROM users
        """
    )
    
    # Create indexes on the new table
    op.execute("CREATE UNIQUE INDEX ix_users_new_email ON users_new (email)")
    op.execute("CREATE INDEX ix_users_new_id ON users_new (id)")
    op.execute("CREATE UNIQUE INDEX ix_users_new_username ON users_new (username)")
    
    # Drop the old table
    op.drop_table('users')
    
    # Rename the new table to the original name
    op.rename_table('users_new', 'users')