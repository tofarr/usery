from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class KeyPairBase(BaseModel):
    """Base key pair schema."""
    
    active: bool = True


class KeyPairCreate(KeyPairBase):
    """Schema for creating a key pair."""
    pass


class KeyPairUpdate(BaseModel):
    """Schema for updating a key pair."""
    
    active: Optional[bool] = None


class KeyPairInDBBase(KeyPairBase):
    """Base schema for key pairs in DB."""
    
    id: UUID
    public_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KeyPair(KeyPairInDBBase):
    """Schema for key pair response (public key only)."""
    pass


class KeyPairFull(KeyPairInDBBase):
    """Schema for full key pair (including private key) - for internal use only."""
    
    private_key: str