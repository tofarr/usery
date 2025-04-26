from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from usery.db.session import Base
from usery.models.user import UUIDType


class Attribute(Base):
    """Attribute model for database."""
    
    __tablename__ = "attributes"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    schema = Column(JSON, nullable=False)  # Keep as 'schema' in the database but map to 'json_schema' in the API
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_attributes = relationship("UserAttribute", back_populates="attribute", cascade="all, delete-orphan")