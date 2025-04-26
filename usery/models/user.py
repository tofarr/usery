from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.types import TypeDecorator
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from uuid import UUID

from usery.db.session import Base, DATABASE_URL


# Custom UUID type for SQLAlchemy that works with SQLite
class UUIDType(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36) which is suitable for SQLite.
    """
    
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, UUID):
            return UUID(value)
        return value


class User(Base):
    """User model for database."""
    
    __tablename__ = "users"

    id = Column(UUIDType, primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tags = relationship("UserTag", back_populates="user", cascade="all, delete-orphan")