from sqlalchemy import Column, String, DateTime, Integer, Boolean, JSON, Text
from sqlalchemy.sql import func
import uuid
import secrets

from usery.db.session import Base
from usery.models.user import UUIDType


class Client(Base):
    """Client model for OAuth2 and OIDC clients."""
    
    __tablename__ = "clients"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    client_secret = Column(String, nullable=False, default=lambda: secrets.token_hex(32))
    access_token_timeout = Column(Integer, nullable=False, default=3600)  # Default 1 hour in seconds
    refresh_token_timeout = Column(Integer, nullable=False, default=86400)  # Default 24 hours in seconds
    
    # OIDC specific fields
    client_type = Column(String, nullable=False, default="confidential")  # confidential, public
    redirect_uris = Column(JSON, nullable=False, default=list)  # List of allowed redirect URIs
    allowed_scopes = Column(JSON, nullable=False, default=lambda: ["openid"])  # List of allowed scopes
    response_types = Column(JSON, nullable=False, default=lambda: ["code"])  # code, token, id_token
    grant_types = Column(JSON, nullable=False, default=lambda: ["authorization_code"])  # authorization_code, implicit, refresh_token, client_credentials
    token_endpoint_auth_method = Column(String, nullable=False, default="client_secret_basic")  # client_secret_basic, client_secret_post, none
    id_token_signed_response_alg = Column(String, nullable=False, default="RS256")  # Algorithm for signing ID tokens
    require_pkce = Column(Boolean, nullable=False, default=False)  # Require PKCE for authorization code flow
    allow_offline_access = Column(Boolean, nullable=False, default=False)  # Allow refresh tokens
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())