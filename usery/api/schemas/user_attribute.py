from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class UserAttributeBase(BaseModel):
    """Base user attribute schema."""
    
    user_id: UUID
    attribute_id: UUID
    value: Dict[str, Any] = Field(..., description="JSON value for the attribute")


class UserAttributeCreate(UserAttributeBase):
    """Schema for creating a user attribute."""
    pass


class UserAttributeUpdate(BaseModel):
    """Schema for updating a user attribute."""
    
    value: Optional[Dict[str, Any]] = Field(None, description="JSON value for the attribute")


class UserAttributeInDBBase(UserAttributeBase):
    """Base schema for user attributes in DB."""
    
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAttribute(UserAttributeInDBBase):
    """Schema for user attribute response."""
    pass