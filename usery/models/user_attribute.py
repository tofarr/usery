from sqlalchemy import Column, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from usery.db.session import Base
from usery.models.user import UUIDType


class UserAttribute(Base):
    """UserAttribute model for database - relationship between users and attributes."""
    
    __tablename__ = "user_attributes"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attribute_id = Column(UUIDType, ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="attributes")
    attribute = relationship("Attribute", back_populates="user_attributes")