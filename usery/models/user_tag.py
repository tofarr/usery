from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from usery.db.session import Base


class UserTag(Base):
    """UserTag model for database - many-to-many relationship between users and tags."""
    
    __tablename__ = "user_tags"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_code = Column(String, ForeignKey("tags.code", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tags")
    tag = relationship("Tag", back_populates="users")