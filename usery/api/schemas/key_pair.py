from datetime import datetime
from typing import Optional

from pydantic import BaseModel, UUID4


class KeyPairBase(BaseModel):
    """Base key pair schema."""
    
    algorithm: str
    is_active: bool = True


class KeyPairCreate(KeyPairBase):
    """Schema for creating a key pair."""
    
    public_key: str
    private_key: str


class KeyPairUpdate(BaseModel):
    """Schema for updating a key pair."""
    
    algorithm: Optional[str] = None
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    is_active: Optional[bool] = None


class KeyPairInDBBase(KeyPairBase):
    """Base schema for key pairs in DB."""
    
    id: UUID4
    public_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KeyPair(KeyPairInDBBase):
    """Schema for key pair response."""
    pass


class KeyPairInDB(KeyPairInDBBase):
    """Schema for key pair in DB with private key."""
    
    private_key: str