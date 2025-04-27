from sqlalchemy import Boolean, Column, String, DateTime, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from usery.db.session import Base


class User(Base):
    """User model for database."""
    
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tags = relationship("UserTag", back_populates="user", cascade="all, delete-orphan")
    attributes = relationship("UserAttribute", back_populates="user", cascade="all, delete-orphan")