from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    """Base schema for users in DB."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema for user response."""
    pass


class UserInDB(UserInDBBase):
    """Schema for user in DB with hashed password."""
    
    hashed_password: str