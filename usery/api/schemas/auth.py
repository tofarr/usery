from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token schema."""
    
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token payload schema."""
    
    sub: Optional[str] = None
    kid: Optional[str] = None  # Key ID for RS256 tokens


class Login(BaseModel):
    """Login schema."""
    
    username: str
    password: str