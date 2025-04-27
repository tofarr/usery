from typing import Optional
from pydantic import BaseModel, HttpUrl


class AvatarUpdate(BaseModel):
    """Schema for updating a user's avatar."""
    
    avatar_url: Optional[str] = None