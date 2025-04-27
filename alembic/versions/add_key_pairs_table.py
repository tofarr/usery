"""Add key_pairs table

Revision ID: add_key_pairs_table
Revises: d6bac3d18831
Create Date: 2025-04-27 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_key_pairs_table'
down_revision = 'd6bac3d18831'
branch_labels = None
depends_on = None


def upgrade():
    # Create key_pairs table
    op.create_table(
        'key_pairs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('algorithm', sa.String(), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('private_key', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_key_pairs_id'), 'key_pairs', ['id'], unique=False)


def downgrade():
    # Drop key_pairs table
    op.drop_index(op.f('ix_key_pairs_id'), table_name='key_pairs')
    op.drop_table('key_pairs')