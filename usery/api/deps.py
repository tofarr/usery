from typing import AsyncGenerator, Optional, Union, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
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
from usery.services.security import ALGORITHM, is_token_blacklisted, _JWT_SECRET_KEY
from usery.services.user import get_user

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
        # Decode the token using HS256 and the JWT secret key
        payload = jwt.decode(
            token, _JWT_SECRET_KEY, algorithms=[ALGORITHM]
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


def get_user_visibility_dependency() -> Callable:
    """
    Returns the appropriate dependency based on the USER_VISIBILITY setting.
    
    - 'private': Only superusers can list users
    - 'protected': Only active users can list users
    - 'public': No login required to list users
    """
    if settings.USER_VISIBILITY == "private":
        return get_current_superuser
    elif settings.USER_VISIBILITY == "protected":
        return get_current_active_user
    elif settings.USER_VISIBILITY == "public":
        # No dependency needed for public visibility
        return lambda: None
    else:
        # Default to protected if an invalid value is provided
        return get_current_active_user