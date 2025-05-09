from sqlalchemy import Column, DateTime, JSON, Boolean, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from usery.db.session import Base


class Attribute(Base):
    """Attribute model for database."""
    
    __tablename__ = "attributes"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    schema = Column(JSON, nullable=False)  # Keep as 'schema' in the database but map to 'json_schema' in the API
    edit_requires_superuser = Column(Boolean, default=False, nullable=False)
    view_requires_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_attributes = relationship("UserAttribute", back_populates="attribute", cascade="all, delete-orphan")