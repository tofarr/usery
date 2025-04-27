from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.schemas.auth import Token, Login
from usery.config.settings import settings
from usery.db.redis import get_redis
from usery.db.session import get_db
from usery.services.security import create_access_token, store_token_in_blacklist
from usery.services.user import authenticate_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": await create_access_token(
            user.id, db, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    *,
    db: AsyncSession = Depends(get_db),
    login_in: Login,
) -> Any:
    """
    JSON compatible login, get an access token for future requests.
    """
    user = await authenticate_user(db, login_in.username, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": await create_access_token(
            user.id, db, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    *,
    redis_client: Redis = Depends(get_redis),
    token: str,
) -> Any:
    """
    Logout by blacklisting the token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    await store_token_in_blacklist(
        redis_client, token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"message": "Successfully logged out"}