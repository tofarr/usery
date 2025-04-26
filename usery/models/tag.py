from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from usery.db.session import Base


class Tag(Base):
    """Tag model for database."""
    
    __tablename__ = "tags"

    code = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("UserTag", back_populates="tag", cascade="all, delete-orphan")