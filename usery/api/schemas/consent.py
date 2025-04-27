from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, UUID4, Field


class ConsentBase(BaseModel):
    """Base schema for user consent."""
    
    user_id: UUID4
    client_id: UUID4
    scopes: List[str]


class ConsentCreate(ConsentBase):
    """Schema for creating a consent record."""
    
    is_active: bool = True


class ConsentUpdate(BaseModel):
    """Schema for updating a consent record."""
    
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ConsentInDBBase(ConsentBase):
    """Base schema for consent records in DB."""
    
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Consent(ConsentInDBBase):
    """Schema for consent response."""
    pass