from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid

from usery.db.session import Base
from usery.models.user import UUIDType


class KeyPair(Base):
    """KeyPair model for database - stores public/private key pairs for JWT signing."""
    
    __tablename__ = "key_pairs"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    public_key = Column(String, nullable=False)
    private_key = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())