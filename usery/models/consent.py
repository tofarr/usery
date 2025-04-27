from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, UUID
from sqlalchemy.sql import func
import uuid

from usery.db.session import Base


class Consent(Base):
    """User consent model for OIDC clients."""
    
    __tablename__ = "consents"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    scopes = Column(JSON, nullable=False)  # List of scopes the user has consented to
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        # Unique constraint to ensure one active consent per user-client pair
        # This allows for updating consent by creating a new one and deactivating the old one
        # It also allows for historical tracking of consent changes
    )