from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
import uuid
import secrets

from usery.db.session import Base
from usery.models.user import UUIDType


class Client(Base):
    """Client model for OAuth2 clients."""
    
    __tablename__ = "clients"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    client_secret = Column(String, nullable=False, default=lambda: secrets.token_hex(32))
    access_token_timeout = Column(Integer, nullable=False, default=3600)  # Default 1 hour in seconds
    refresh_token_timeout = Column(Integer, nullable=False, default=86400)  # Default 24 hours in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())