from datetime import datetime, timedelta
import secrets
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from usery.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Always use HS256 for JWT tokens
ALGORITHM = "HS256"

# Generate a random JWT secret key if not provided in environment
_JWT_SECRET_KEY = settings.JWT_SECRET_KEY
if not _JWT_SECRET_KEY:
    _JWT_SECRET_KEY = secrets.token_hex(32)  # Generate a secure random key


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
    
    # Use the JWT secret key with HS256 algorithm
    encoded_jwt = jwt.encode(to_encode, _JWT_SECRET_KEY, algorithm=ALGORITHM)
        
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