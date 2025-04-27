"""OIDC implementation

Revision ID: oidc_implementation
Revises: 
Create Date: 2025-04-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'oidc_implementation'
down_revision = None  # Set this to the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Update clients table with OIDC fields
    op.add_column('clients', sa.Column('client_type', sa.String(), nullable=False, server_default='confidential'))
    op.add_column('clients', sa.Column('redirect_uris', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('clients', sa.Column('allowed_scopes', sa.JSON(), nullable=False, server_default='["openid"]'))
    op.add_column('clients', sa.Column('response_types', sa.JSON(), nullable=False, server_default='["code"]'))
    op.add_column('clients', sa.Column('grant_types', sa.JSON(), nullable=False, server_default='["authorization_code"]'))
    op.add_column('clients', sa.Column('token_endpoint_auth_method', sa.String(), nullable=False, server_default='client_secret_basic'))
    op.add_column('clients', sa.Column('id_token_signed_response_alg', sa.String(), nullable=False, server_default='RS256'))
    op.add_column('clients', sa.Column('require_pkce', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('clients', sa.Column('allow_offline_access', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create authorization_codes table
    op.create_table(
        'authorization_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('nonce', sa.String(), nullable=True),
        sa.Column('auth_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('code_challenge', sa.String(), nullable=True),
        sa.Column('code_challenge_method', sa.String(), nullable=True),
        sa.Column('used', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('claims', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authorization_codes_code'), 'authorization_codes', ['code'], unique=True)
    op.create_index(op.f('ix_authorization_codes_id'), 'authorization_codes', ['id'], unique=False)
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)
    
    # Create consents table
    op.create_table(
        'consents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_id'), 'consents', ['id'], unique=False)


def downgrade():
    # Drop consents table
    op.drop_index(op.f('ix_consents_id'), table_name='consents')
    op.drop_table('consents')
    
    # Drop refresh_tokens table
    op.drop_index(op.f('ix_refresh_tokens_token'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    
    # Drop authorization_codes table
    op.drop_index(op.f('ix_authorization_codes_code'), table_name='authorization_codes')
    op.drop_index(op.f('ix_authorization_codes_id'), table_name='authorization_codes')
    op.drop_table('authorization_codes')
    
    # Remove OIDC fields from clients table
    op.drop_column('clients', 'allow_offline_access')
    op.drop_column('clients', 'require_pkce')
    op.drop_column('clients', 'id_token_signed_response_alg')
    op.drop_column('clients', 'token_endpoint_auth_method')
    op.drop_column('clients', 'grant_types')
    op.drop_column('clients', 'response_types')
    op.drop_column('clients', 'allowed_scopes')
    op.drop_column('clients', 'redirect_uris')
    op.drop_column('clients', 'client_type')