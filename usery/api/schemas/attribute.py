from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class AttributeBase(BaseModel):
    """Base attribute schema."""
    
    json_schema: Dict[str, Any] = Field(..., description="JSON schema for the attribute")
    requires_superuser: bool = False


class AttributeCreate(AttributeBase):
    """Schema for creating an attribute."""
    pass


class AttributeUpdate(BaseModel):
    """Schema for updating an attribute."""
    
    json_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for the attribute")
    requires_superuser: Optional[bool] = None


class AttributeInDBBase(AttributeBase):
    """Base schema for attributes in DB."""
    
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        # Map schema field from DB to json_schema in API
        populate_by_name = True
        alias_generator = lambda field: "schema" if field == "json_schema" else field


class Attribute(AttributeInDBBase):
    """Schema for attribute response."""
    pass


class AttributeWithUserCount(Attribute):
    """Schema for attribute with user count."""
    
    user_count: int