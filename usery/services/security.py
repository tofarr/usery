from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from usery.config.settings import settings
from usery.services import key_pair as key_pair_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "RS256"  # Changed from HS256 to RS256


async def create_access_token(
    subject: Union[str, Any], 
    db: AsyncSession,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token using RS256 algorithm with stored key pair."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Get the active key pair
    key_pair = await key_pair_service.get_active_key_pair(db)
    if not key_pair:
        # Fallback to HS256 if no key pair is available
        to_encode = {"exp": expire, "sub": str(subject)}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    # Use RS256 with the private key
    to_encode = {"exp": expire, "sub": str(subject), "kid": str(key_pair.id)}
    encoded_jwt = jwt.encode(to_encode, key_pair.private_key, algorithm=ALGORITHM)
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