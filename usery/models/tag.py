import re
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates

from usery.db.session import Base

CODE_PATTERN = r"^[a-z0-9_]+$"


class Tag(Base):
    """Tag model for database."""
    
    __tablename__ = "tags"

    code = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    edit_requires_superuser = Column(Boolean, default=False, nullable=False)
    view_requires_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("UserTag", back_populates="tag", cascade="all, delete-orphan")

    @validates('code')
    def validate_name(self, key, value):
        assert re.match(CODE_PATTERN, value)
        return value
