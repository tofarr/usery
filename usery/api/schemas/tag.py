from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    requires_superuser: bool = False


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    requires_superuser: Optional[bool] = None


class TagInDBBase(TagBase):
    """Base schema for tags in DB."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Tag(TagInDBBase):
    """Schema for tag response."""
    pass


class TagWithUsers(Tag):
    """Schema for tag with users."""
    
    user_count: int