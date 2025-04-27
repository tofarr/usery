from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from usery.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use RS256 if private key is available in environment, otherwise fallback to HS256
ALGORITHM = "RS256" if settings.JWT_PRIVATE_KEY else "HS256"


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Use RS256 with environment key if available, otherwise fallback to HS256
    if settings.JWT_PRIVATE_KEY:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_PRIVATE_KEY, algorithm=ALGORITHM)
    else:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


async def store_token_in_blacklist(redis_client: Redis, token: str, expires_delta: int) -> None:
    """Store a token in the blacklist (Redis)."""
    await redis_client.setex(f"blacklist:{token}", expires_delta, "true")


async def is_token_blacklisted(redis_client: Redis, token: str) -> bool:
    """Check if a token is blacklisted."""
    result = await redis_client.exists(f"blacklist:{token}")
    return result > 0