from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from usery.api.schemas.tag import Tag
from usery.api.schemas.user import User


class UserTagBase(BaseModel):
    """Base user tag schema."""
    
    user_id: UUID
    tag_code: str


class UserTagCreate(UserTagBase):
    """Schema for creating a user tag."""
    pass


class UserTagInDBBase(UserTagBase):
    """Base schema for user tags in DB."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserTag(UserTagInDBBase):
    """Schema for user tag response."""
    pass


class UserTagWithDetails(UserTagInDBBase):
    """Schema for user tag with user and tag details."""
    
    user: User
    tag: Tag