from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4, Field


class ClientBase(BaseModel):
    """Base client schema."""
    
    title: str
    description: Optional[str] = None
    access_token_timeout: int = Field(3600, description="Access token timeout in seconds")
    refresh_token_timeout: int = Field(86400, description="Refresh token timeout in seconds")


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    access_token_timeout: Optional[int] = None
    refresh_token_timeout: Optional[int] = None


class ClientInDBBase(ClientBase):
    """Base schema for clients in DB."""
    
    id: UUID4
    client_secret: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Client(ClientInDBBase):
    """Schema for client response."""
    pass