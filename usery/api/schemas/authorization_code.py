from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4, Field


class AuthorizationCodeBase(BaseModel):
    """Base schema for authorization codes."""
    
    client_id: UUID4
    user_id: UUID4
    redirect_uri: str
    scope: str
    nonce: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    claims: Optional[Dict[str, Any]] = None


class AuthorizationCodeCreate(AuthorizationCodeBase):
    """Schema for creating an authorization code."""
    
    expires_at: datetime


class AuthorizationCodeUpdate(BaseModel):
    """Schema for updating an authorization code."""
    
    used: bool = True


class AuthorizationCodeInDBBase(AuthorizationCodeBase):
    """Base schema for authorization codes in DB."""
    
    id: UUID4
    code: str
    auth_time: datetime
    expires_at: datetime
    used: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorizationCode(AuthorizationCodeInDBBase):
    """Schema for authorization code response."""
    pass