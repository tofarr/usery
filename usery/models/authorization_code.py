from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
import uuid
import secrets

from usery.db.session import Base
from usery.models.user import UUIDType


class AuthorizationCode(Base):
    """Authorization code model for OIDC authorization code flow."""
    
    __tablename__ = "authorization_codes"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    code = Column(String, nullable=False, index=True, unique=True, default=lambda: secrets.token_urlsafe(48))
    client_id = Column(UUIDType, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    redirect_uri = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    nonce = Column(String, nullable=True)
    auth_time = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    code_challenge = Column(String, nullable=True)
    code_challenge_method = Column(String, nullable=True)
    used = Column(Boolean, default=False)
    
    # Additional claims to include in the ID token
    claims = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())