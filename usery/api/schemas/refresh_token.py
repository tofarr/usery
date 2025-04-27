from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, Field


class RefreshTokenBase(BaseModel):
    """Base schema for refresh tokens."""
    
    client_id: UUID4
    user_id: UUID4
    scope: str


class RefreshTokenCreate(RefreshTokenBase):
    """Schema for creating a refresh token."""
    
    expires_at: datetime


class RefreshTokenUpdate(BaseModel):
    """Schema for updating a refresh token."""
    
    revoked: bool = True


class RefreshTokenInDBBase(RefreshTokenBase):
    """Base schema for refresh tokens in DB."""
    
    id: UUID4
    token: str
    expires_at: datetime
    revoked: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RefreshToken(RefreshTokenInDBBase):
    """Schema for refresh token response."""
    pass