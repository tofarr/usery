from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
import uuid
import secrets

from usery.db.session import Base
from usery.models.user import UUIDType


class RefreshToken(Base):
    """Refresh token model for OIDC refresh token flow."""
    
    __tablename__ = "refresh_tokens"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    token = Column(String, nullable=False, index=True, unique=True, default=lambda: secrets.token_urlsafe(64))
    client_id = Column(UUIDType, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())