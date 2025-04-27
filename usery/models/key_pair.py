from sqlalchemy import Boolean, Column, String, DateTime, UUID
from sqlalchemy.sql import func

from usery.db.session import Base
import uuid


class KeyPair(Base):
    """KeyPair model for database."""
    
    __tablename__ = "key_pairs"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    algorithm = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    private_key = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())