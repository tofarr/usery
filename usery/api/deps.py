from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.schemas.auth import TokenPayload
from usery.config.settings import settings
from usery.db.redis import get_redis
from usery.db.session import get_db
from usery.models.user import User
from usery.services.security import ALGORITHM, is_token_blacklisted
from usery.services.user import get_user
from usery.services import key_pair as key_pair_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    redis_client: Redis = Depends(get_redis),
) -> User:
    """
    Get the current user from the token.
    """
    if await is_token_blacklisted(redis_client, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # First try to decode the token using RS256
        # Get the unverified headers to extract the key ID
        unverified_headers = jwt.get_unverified_headers(token)
        kid = unverified_headers.get("kid")
        
        if kid:
            # If we have a key ID, get the corresponding key pair
            key_pair = await key_pair_service.get_key_pair(db, UUID(kid))
            if key_pair:
                # Verify using the public key
                payload = jwt.decode(
                    token, key_pair.public_key, algorithms=[ALGORITHM]
                )
            else:
                # Key pair not found, try with SECRET_KEY as fallback
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )
        else:
            # No key ID, try with SECRET_KEY as fallback
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user(db, user_id=UUID(token_data.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    
    return current_user