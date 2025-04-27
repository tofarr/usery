from datetime import datetime, timedelta
import os
import secrets
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from usery.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Always use HS256 for JWT tokens
ALGORITHM = "HS256"

# JWT secret key file path
JWT_SECRET_FILE = ".jwt_secret"

# Get or generate JWT secret key
def get_jwt_secret_key() -> str:
    """
    Get the JWT secret key from environment, file, or generate a new one.
    
    Priority:
    1. Environment variable JWT_SECRET_KEY
    2. Existing .jwt_secret file
    3. Generate new key and save to .jwt_secret file
    """
    # Check environment variable first
    if settings.JWT_SECRET_KEY:
        return settings.JWT_SECRET_KEY
    
    # Check for existing secret file
    if os.path.exists(JWT_SECRET_FILE):
        try:
            with open(JWT_SECRET_FILE, "r") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            # If there's any issue reading the file, we'll generate a new key
            pass
    
    # Generate a new key
    new_key = secrets.token_hex(32)
    
    # Save the key to file
    try:
        with open(JWT_SECRET_FILE, "w") as f:
            f.write(new_key)
        # Set appropriate permissions (readable only by owner)
        os.chmod(JWT_SECRET_FILE, 0o600)
    except Exception:
        # If we can't save the key, just use it for this session
        pass
        
    return new_key

# Initialize the JWT secret key
_JWT_SECRET_KEY = get_jwt_secret_key()


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